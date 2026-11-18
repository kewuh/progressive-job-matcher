#!/usr/bin/env python3
"""Job Scout: find jobs at organisations where you know someone.

Reads the Connections.csv file from a LinkedIn data export (or the whole
export .zip), groups your connections by their current employer, and matches
those employers against your tracked jobs.

Privacy: connections' email addresses are always dropped. The output stays on
your machine or in your own private Job Scout database; never commit it,
share it or put it in a public place.

Usage:
  python3 contacts.py build   --linkedin Connections.csv|export.zip --out network.json
  python3 contacts.py match   --network network.json --jobs-dir DIR [--out matches.json]
  python3 contacts.py lookup  --network network.json "Organisation name"

network.json  {"builtAt", "source", "connections", "orgs": {key: {"org", "people": [{"name","position","connectedOn","url"}]}}}
matches.json  {job_id: {"contactsCount": n, "contacts": [{"name","position","url"}] (up to 5), "contactsOrg": "employer as written on LinkedIn"}}
"""
import argparse
import csv
import datetime
import glob
import io
import json
import os
import re
import sys
import zipfile

LEGAL = r"\b(inc|incorporated|llc|l\.l\.c|ltd|limited|plc|corp|corporation|co|company|pbc|cic|gmbh|lp|llp)\b\.?"
# Words too generic to match an organisation on their own.
GENERIC = {"action", "fund", "foundation", "network", "project", "alliance", "campaign", "union", "council",
           "center", "centre", "institute", "group", "coalition", "partners", "media", "digital", "strategies",
           "global", "national", "international", "america", "american", "united", "states", "new", "york",
           "self employed", "self-employed", "freelance", "freelancer", "independent", "consultant", "retired",
           "stealth", "confidential", "various", "none", "na", "n a", "new york", "london", "washington",
           "washington dc", "chicago", "california", "usa", "uk", "us"}


def norm(name):
    s = (name or "").lower().replace("&", " and ").replace("’", "'")
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(LEGAL, " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"^\s*the\s+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def keys_for(name):
    """All lookup keys for an organisation name: the main name, any acronym in
    brackets, and the part before a colon/dash ("Org: Programme")."""
    out = set()
    k = norm(name)
    if k:
        out.add(k)
    for m in re.findall(r"\(([^)]+)\)", name or ""):
        # Only real acronyms like "(NRDC)", not places like "(New York)".
        if re.fullmatch(r"[A-Z0-9&.\-]{2,10}", m.strip()):
            out.add(norm(m))
    head = re.split(r"\s[-–:|]\s|:", name or "")[0]
    if head and head != name:
        h = norm(head)
        if h:
            out.add(h)
    return {x for x in out if x and x not in GENERIC}


def read_connections(path):
    """Return rows from Connections.csv. LinkedIn puts a few 'Notes' lines above
    the header, so find the header line first."""
    if zipfile.is_zipfile(path):
        z = zipfile.ZipFile(path)
        names = [n for n in z.namelist() if n.lower().endswith("connections.csv")]
        if not names:
            sys.exit("No Connections.csv inside that zip. In the LinkedIn export, make sure Connections was included.")
        text = z.read(names[0]).decode("utf-8-sig", errors="replace")
    else:
        text = open(path, encoding="utf-8-sig", errors="replace").read()
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if l.lower().startswith("first name")), None)
    if start is None:
        sys.exit("Couldn't find the header row ('First Name,Last Name,...') in that file.")
    return list(csv.DictReader(io.StringIO("\n".join(lines[start:]))))


def build(a):
    rows = read_connections(a.linkedin)
    orgs = {}
    n = 0
    for r in rows:
        company = (r.get("Company") or "").strip()
        name = " ".join(x for x in [(r.get("First Name") or "").strip(), (r.get("Last Name") or "").strip()] if x)
        if not company or not name:
            continue
        k = norm(company)
        if not k or k in GENERIC:
            continue
        n += 1
        person = {"name": name, "position": (r.get("Position") or "").strip()[:120],
                  "connectedOn": (r.get("Connected On") or "").strip(), "url": (r.get("URL") or "").strip()}
        o = orgs.setdefault(k, {"org": company, "people": []})
        o["people"].append(person)  # email deliberately not kept
    out = {"builtAt": datetime.date.today().isoformat(), "source": "LinkedIn Connections.csv",
           "connections": n, "orgs": orgs}
    json.dump(out, open(a.out, "w"), ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(a.out)
    print("%d connections at %d organisations -> %s (%d KB)" % (n, len(orgs), a.out, size // 1024))
    if size > 900_000:
        print("Note: over 900 KB; store it in the database as several parts (see references/linkedin-contacts.md).")


def index(network):
    idx = {}
    for k, o in network["orgs"].items():
        for key in keys_for(o["org"]) | {k}:
            idx.setdefault(key, []).append(k)
    return idx


def find(network, idx, org_name):
    """Network org keys that match a job's organisation name."""
    hits = set()
    for key in keys_for(org_name):
        hits.update(idx.get(key, []))
        # Prefix match on whole words, e.g. "planned parenthood" vs
        # "planned parenthood federation of america". The shorter side must be
        # distinctive (2+ words or 6+ letters) so "Action" doesn't match everything.
        for other in idx:
            short, long_ = (key, other) if len(key) <= len(other) else (other, key)
            if short == long_ or short in GENERIC:
                continue
            if (len(short.split()) >= 2 or len(short) >= 6) and long_.startswith(short + " "):
                hits.update(idx[other])
    return sorted(hits)


def match(a):
    network = json.load(open(a.network))
    idx = index(network)
    out = {}
    for f in glob.glob(os.path.join(a.jobs_dir, "**", "*.json"), recursive=True):
        try:
            j = json.load(open(f))
        except Exception:
            continue
        if not j.get("org"):
            continue
        ks = find(network, idx, j["org"])
        if not ks:
            continue
        people = [p for k in ks for p in network["orgs"][k]["people"]]
        out[os.path.basename(f)[:-5]] = {"contactsCount": len(people),
                                         "contacts": [{"name": p["name"], "position": p["position"], "url": p["url"]} for p in people[:5]],
                                         "contactsOrg": network["orgs"][ks[0]]["org"]}
    if a.out:
        json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=1)
    print("%d tracked jobs are at organisations where you know someone" % len(out))
    for k, v in sorted(out.items(), key=lambda x: -x[1]["contactsCount"])[:40]:
        print(" ", k, v["contactsOrg"], "-", v["contactsCount"], "contact(s):", "; ".join(p["name"] for p in v["contacts"][:3]))


def lookup(a):
    network = json.load(open(a.network))
    idx = index(network)
    for k in find(network, idx, a.org):
        o = network["orgs"][k]
        print(o["org"])
        for p in o["people"]:
            print("  ", p["name"], "-", p["position"], p["url"])


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--linkedin", required=True); b.add_argument("--out", default="network.json")
    m = sub.add_parser("match"); m.add_argument("--network", required=True); m.add_argument("--jobs-dir", required=True); m.add_argument("--out", default="")
    l = sub.add_parser("lookup"); l.add_argument("--network", required=True); l.add_argument("org")
    a = ap.parse_args()
    {"build": build, "match": match, "lookup": lookup}[a.cmd](a)


if __name__ == "__main__":
    main()
