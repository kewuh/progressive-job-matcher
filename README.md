# Movement Match

Matches people who work in progressive movements to the right roles. It's a daily job-search assistant that runs on Claude. Each morning it:

- reads your job-alert emails and job listservs (read-only)
- checks live job boards, the organizations you care about and job-sharing Bluesky accounts
- confirms each posting is still open and finds the employer's own link
- scores every job against your experience (from your resumes and cover letters), with a one-line "why it fits" and "watch out"
- closes jobs whose deadlines have passed
- optionally flags jobs at organizations where you **know someone**, from your LinkedIn connections export
- keeps a **dashboard** and a **Google Sheet** tracker in sync, so you can move jobs from Suggested → Applied → Interviewing in either place

You set it up once by chatting with Claude. Your profile, jobs and settings stay private in your own Claude artifact and your own sheet.

## What you need

- A Claude account with artifacts and connectors
- **Gmail** and **Google Sheets** connectors (Settings → Connectors)
- A **web search** connector (for checking job pages and the dashboard's "Find new jobs" button)
- Somewhere to run it daily: Claude Code on the web, or the Claude desktop app's scheduled tasks
- Optional: Claude in Chrome, if you want a daily LinkedIn scan on your own computer

## Install

**Claude.ai or the desktop app (skill):** download [`dist/movement-match-skill.zip`](dist/movement-match-skill.zip) from this repo, then go to Settings → Capabilities → Skills → Upload skill.

**Claude Code (plugin):**

```bash
claude plugin marketplace add kewuh/progressive-job-matcher
```

```bash
claude plugin install movement-match@movement-match
```

Or copy `skills/movement-match` into `~/.claude/skills/`.

## Set up

Start a chat and say **"Set up Movement Match"**. Claude will:

1. Build your profile from your resume and what you're looking for: roles, levels, places, dealbreakers, and where your odds are best.
2. Publish your private dashboard.
3. Ask you to make a blank Google Sheet (it only ever writes to that one sheet) and set up the tracker tab.
4. Help you choose sources: email alerts and lists, organizations' job boards, sites to watch, Bluesky accounts.
5. Schedule the daily run.
6. Optionally, flag jobs where you know someone: upload your LinkedIn data export (Settings & Privacy → Data privacy → Download your data → Connections).
7. Optionally, set up the LinkedIn scan on your computer.

After that, ask **"run my job scan"** any time, or let the schedule do it.

## Safety

Movement Match is built to be safe to leave running:

- Gmail and Drive are **read-only**: it never sends, replies, drafts, labels or deletes.
- It writes only to your Movement Match dashboard and your one tracker sheet.
- It never logs in, creates accounts, applies, messages or posts for you, and never tries to get around a site's bot checks.
- It treats email and web content as data, not instructions.
- It skips personal emails that aren't about jobs, and doesn't store phone numbers or addresses.
- Your LinkedIn connections, if you upload them, stay in your private database. Their email addresses are never kept, and nothing is ever sent to them.

## What's in the repo

| Path | What it is |
|---|---|
| `skills/movement-match/SKILL.md` | The skill: what Movement Match is, ground rules, data model |
| `skills/movement-match/references/` | Setup guide, the daily-run prompt, scoring rules, how to find sources, the LinkedIn scan |
| `skills/movement-match/assets/dashboard.html` | The dashboard artifact |
| `skills/movement-match/scripts/live_boards.py` | Reads Greenhouse, Lever, Ashby, Rippling and UltiPro boards and Bluesky feeds |
| `skills/movement-match/scripts/contacts.py` | Groups your LinkedIn connections by employer and matches them to your jobs |
| `skills/movement-match/scripts/job_id.py` | The job-id hash shared with the dashboard |
| `skills/movement-match/templates/` | Example profile and config |
| `.claude-plugin/` | Claude Code plugin and marketplace manifests |
| `dist/movement-match-skill.zip` | The skill, zipped for upload to Claude |

Run the board scanner yourself with:

```bash
python3 skills/movement-match/scripts/live_boards.py --config my-config.json --out live.json
```

## License

MIT
