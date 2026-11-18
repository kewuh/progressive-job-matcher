# Job sources

Movement Match is only as good as its sources. Mix the four kinds below. Store them in the `config` doc.

## 1. Email (`config.email`)

The cheapest, richest source. Ask the user what they already receive, and suggest:

- **Job alerts** from LinkedIn, Indeed, Idealist and the like. Set up 5–15 saved searches with daily emails. Narrow titles + a location work better than broad ones; add a couple of searches for less obvious titles that fewer people apply to.
- **Sector job newsletters and digests** (most fields have them). Add each sender to `jobListSenders`.
- **Google Groups / listservs** in their field. Add the group's address to `jobListGroups` (jobs-only lists) or `discussionGroups` (mixed lists, where only clear job posts are taken). Note that a group may post from a `@googlegroups.com` address that differs from its public address; include both.
- **A Gmail label** (e.g. "Jobs") that the user applies to anything else they want read.
- **The hiring search** (`hiringSearch: true`): searches the inbox for "hiring" to catch newsletters and announcements that mention jobs.

## 2. Live boards (`config.liveBoards`)

Many organizations post jobs through an applicant-tracking system with a public JSON feed. These are read completely every day by `scripts/live_boards.py`, so new jobs are caught the day they appear and closed ones are spotted.

| type | How to find the slug | Feed |
|---|---|---|
| `greenhouse` | `boards.greenhouse.io/<slug>` or `job-boards.greenhouse.io/<slug>` | `boards-api.greenhouse.io/v1/boards/<slug>/jobs` |
| `lever` | `jobs.lever.co/<slug>` | `api.lever.co/v0/postings/<slug>?mode=json` |
| `ashby` | `jobs.ashbyhq.com/<slug>` | `api.ashbyhq.com/posting-api/job-board/<slug>` |
| `rippling` | `ats.rippling.com/<slug>/jobs` | the board page itself |
| `ultipro` | `recruiting.ultipro.com/<TENANT>/JobBoard/<BOARD-ID>` | set `base` to that URL instead of `slug` |

To find an organization's board, open its careers page and look at where "Apply" links go, or web search "<org> greenhouse" / "<org> lever". Check a guessed slug by fetching the feed and confirming the organization's name.

Never rely on a cached web-fetch copy of these boards; read the live feed.

## 3. Organizations and pages (`orgWatch`, `watch`)

- `orgWatch`: organizations without a JSON feed. Store `name`, `category`, `careersUrl`, `status` (`resolved`, `resolved-unverified` if guessed, or `no-jobs-page`) and `lastCheckedAt`. The daily run fetches about 20 per day, oldest first.
- `watch`: job boards and saved searches (`kind: "board"`), organizations the person would love to work for (`kind: "org"`, which boosts fit), and keyword searches (`kind: "search"`, run as web searches). Add a `note` on how to read each one.

Good starting points: the person's favorite 20–50 organizations, peers of the places that have interviewed them, and sector job boards. Agencies and consultancies in their field often hire more, and less competitively, than big-name organizations.

## 4. Bluesky (`config.bluesky`)

Public feeds, read without logging in.

- `handles`: job-board accounts, organizations and people who regularly share jobs in the field.
- `announceAllHandles`: accounts where every post is a job (e.g. a job board's bot). Their posts become candidates directly; other accounts' posts are filtered for hiring words and the links followed.

Find accounts with `https://public.api.bsky.app/xrpc/app.bsky.actor.searchActors?q=<name>`. Remove people who haven't shared a job in 60 days.

## Sites that need care

- Sites that render jobs with JavaScript or block automated reading: use web search for "<site> <job title>" instead of fetching.
- Sites that refuse automated access: skip them; never try to get around the block.
- LinkedIn: use the email alerts, or the optional browser scan on the user's own computer. Never fetch LinkedIn pages from the cloud.
