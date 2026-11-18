#!/usr/bin/env python3
"""Movement Match live-board scanner.

Reads complete, machine-readable job boards (Greenhouse, Lever, Ashby, Rippling,
UltiPro) and public Bluesky feeds, filters them with the keyword rules in your
config, and prints candidate jobs that are not already tracked. It also reports
tracked jobs that have disappeared from a complete board (likely closed).

It only reads public pages and APIs. It never logs in, never sends anything,
and never tries to get around a site's bot checks.

Usage:
  python3 live_boards.py --config config.json [--jobs-dir DIR] [--out live.json] [--days 3]

  --config    the Movement Match config (see templates/config.example.json)
  --jobs-dir  a folder of tracked job JSON files (one per job, as saved from
              the Movement Match database); used to skip known jobs and spot closures
  --out       where to write the full JSON result (default: live.json)
  --days      how far back to read Bluesky posts (default: 3)
"""
import argparse
import concurrent.futures as cf
import datetime
import glob
import json
import os
import re
import subprocess

ACTIVE = ("suggested", "shortlist", "applied", "interview")


def curl(args, timeout=30):
    p = subprocess.run(["curl", "-s", "-L", "-m", str(timeout)] + args,
                       capture_output=True, text=True, timeout=timeout + 5)
    return p.stdout


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def rx(words, default):
    words = [w for w in (words or []) if w]
    if not words:
        return re.compile(default, re.I)
    return re.compile("|".join(words), re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--jobs-dir", default="")
    ap.add_argument("--out", default="live.json")
    ap.add_argument("--days", type=int, default=3)
    a = ap.parse_args()

    cfg = json.load(open(a.config))
    filt = cfg.get("filters", {})
    TK = rx(filt.get("titleInclude"), r".")
    BAD = rx(filt.get("titleExclude"), r"$^")
    LOC = rx(filt.get("locationInclude"), r".")
    HK = rx(filt.get("postInclude"), r"hiring|job|apply|seeks|join our team|open role|position")

    tracked = {}
    if a.jobs_dir:
        for f in glob.glob(os.path.join(a.jobs_dir, "**", "*.json"), recursive=True):
            try:
                d = json.load(open(f))
                if d.get("url") and d.get("title"):
                    tracked[os.path.basename(f)[:-5]] = d
            except Exception:
                pass
    urls = {d["url"] for d in tracked.values()}
    keys = {norm(d.get("org"))[:12] + norm(d.get("title"))[:30] for d in tracked.values()}

    out = {"candidates": [], "possiblyClosed": [], "sources": {}, "socialPosts": []}

    def cand(src, org, title, loc, url, posted=""):
        if url in urls or (norm(org)[:12] + norm(title)[:30]) in keys:
            return
        if TK.search(title or "") and not BAD.search(title or "") and LOC.search(loc or "remote"):
            out["candidates"].append(dict(source=src, org=org, title=title, location=loc, url=url, posted=posted))

    def closed_check(name, live_urls, match):
        for k, d in tracked.items():
            if d.get("status") in ACTIVE and match(d.get("url", "")) and d["url"] not in live_urls:
                out["possiblyClosed"].append({"id": k, "title": d.get("title"), "org": d.get("org"), "board": name})

    # ---- ATS boards (complete and live) ----
    def read_board(b):
        name, kind, slug = b["name"], b["type"], b["slug"]
        try:
            if kind == "greenhouse":
                d = json.loads(curl(["https://boards-api.greenhouse.io/v1/boards/%s/jobs" % slug], 40))
                J = [(j["title"], (j.get("location") or {}).get("name", ""), j["absolute_url"], (j.get("updated_at") or "")[:10]) for j in d.get("jobs", [])]
            elif kind == "lever":
                d = json.loads(curl(["https://api.lever.co/v0/postings/%s?mode=json" % slug], 40))
                J = [(j["text"], (j.get("categories") or {}).get("location", ""), j["hostedUrl"], "") for j in d] if isinstance(d, list) else []
            elif kind == "ashby":
                d = json.loads(curl(["https://api.ashbyhq.com/posting-api/job-board/%s" % slug], 40))
                J = [(j["title"], j.get("location", ""), j["jobUrl"], (j.get("publishedAt") or "")[:10]) for j in d.get("jobs", [])]
            elif kind == "rippling":
                h = curl(["https://ats.rippling.com/en-GB/%s/jobs" % slug], 40)
                m = re.search(r'__NEXT_DATA__" type="application/json">(.*?)</script>', h, re.S)
                found = []

                def walk(x):
                    if isinstance(x, dict):
                        if "workLocations" in x and "name" in x and "id" in x:
                            found.append(x)
                        for v in x.values():
                            walk(v)
                    elif isinstance(x, list):
                        for v in x:
                            walk(v)
                if m:
                    walk(json.loads(m.group(1)))
                J = [(j["name"], ", ".join(w if isinstance(w, str) else (w.get("name") or "") for w in j["workLocations"]),
                      "https://ats.rippling.com/en-GB/%s/jobs/%s" % (slug, j["id"]), "") for j in found]
                # The page structure changes; only treat a job as closed if its id is absent from the raw HTML.
                for k, dd in tracked.items():
                    if dd.get("status") in ACTIVE and slug in dd.get("url", ""):
                        jid = dd["url"].rstrip("/").rsplit("/", 1)[-1]
                        if jid and jid not in h:
                            out["possiblyClosed"].append({"id": k, "title": dd.get("title"), "org": dd.get("org"), "board": name})
                return name, "ok", J, None
            elif kind == "ultipro":
                base = b["base"]  # e.g. https://recruiting.ultipro.com/<TENANT>/JobBoard/<BOARD-ID>
                body = json.dumps({"opportunitySearch": {"Top": 100, "Skip": 0, "QueryString": "", "OrderBy": [{"Value": "postedDateDesc", "PropertyName": "PostedDate", "Ascending": False}], "Filters": []},
                                   "matchCriteria": {"PreferredJobs": [], "Educations": [], "LicenseAndCertifications": [], "Skills": [], "hasNoLicenses": False, "SkippedSkills": []}})
                d = json.loads(curl(["-X", "POST", "-H", "Content-Type: application/json", "-d", body, base + "/JobBoardView/LoadSearchResults"], 40))
                J = []
                for o in d.get("opportunities", []):
                    locs = ", ".join((l.get("LocalizedDescription") or "") for l in (o.get("Locations") or []))
                    if o.get("JobLocationType") == 2:
                        locs = "Remote; " + locs
                    J.append((o["Title"], locs, base + "/OpportunityDetail?opportunityId=" + o["Id"], (o.get("PostedDate") or "")[:10]))
            else:
                return name, "skipped", [], "unknown type " + kind
            return name, "ok", J, None
        except Exception as e:
            return name, "failed", [], str(e)[:120]

    boards = cfg.get("liveBoards", [])
    with cf.ThreadPoolExecutor(6) as ex:
        for name, st, J, err in ex.map(read_board, boards):
            out["sources"][name] = {"result": st, "jobs": len(J), "note": err or ""}
            if st != "ok":
                continue
            for t, l, u, pd in J:
                cand(name, name, t, l, u, pd)
            live = {x[2] for x in J}
            b = next(x for x in boards if x["name"] == name)
            if b["type"] in ("greenhouse", "lever", "ashby", "ultipro"):
                host = {"greenhouse": "greenhouse", "lever": "lever.co", "ashby": "ashbyhq", "ultipro": b.get("base", "~")}[b["type"]]
                closed_check(name, live, lambda u, s=b["slug"], h=host: h in u and s in u)

    # ---- Bluesky (public, no login) ----
    cut = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=a.days)).strftime("%Y-%m-%dT%H:%M:%S")
    handles = cfg.get("bluesky", {}).get("handles", [])
    announce = set(cfg.get("bluesky", {}).get("announceAllHandles", []))

    def feed(hd):
        try:
            d = json.loads(curl(["https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=%s&limit=50&filter=posts_no_replies" % hd], 20))
            res = []
            for it in d.get("feed", []):
                if "reason" in it:
                    continue
                p = it["post"]
                r = p["record"]
                if r.get("createdAt", "") < cut:
                    continue
                t = r.get("text", "")
                if hd in announce or HK.search(t):
                    links = [f2.get("uri") for fc in r.get("facets", []) for f2 in fc.get("features", []) if f2.get("uri")]
                    ext = ((p.get("embed") or {}).get("external") or {}).get("uri")
                    if ext:
                        links.append(ext)
                    res.append({"handle": hd, "date": r["createdAt"][:10], "text": t.replace("\n", " ")[:300], "links": links[:3]})
            return hd, "ok", res
        except Exception:
            return hd, "failed", []

    okc = 0
    with cf.ThreadPoolExecutor(8) as ex:
        for hd, st, res in ex.map(feed, handles):
            okc += st == "ok"
            for p in res:
                if p["handle"] in announce:
                    if LOC.search(p["text"]) and TK.search(p["text"]) and not any(u in urls for u in p["links"]):
                        out["candidates"].append(dict(source="Bluesky: " + hd, org="", title=p["text"], location="", url=(p["links"] or [""])[0], posted=p["date"]))
                else:
                    out["socialPosts"].append(p)
    if handles:
        out["sources"]["Bluesky"] = {"result": "ok" if okc else "failed", "jobs": len(out["socialPosts"]), "note": "%d/%d feeds read" % (okc, len(handles))}

    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out["sources"], indent=1))
    print("possibly closed:", len(out["possiblyClosed"]))
    for c in out["candidates"]:
        print(" | ".join([c["source"], c["org"], c["title"][:110], c["location"][:40], c["posted"]]))
    print("social posts to review:", len(out["socialPosts"]))


if __name__ == "__main__":
    main()
