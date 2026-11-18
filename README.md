# Progressive Job Matcher

A daily job-search assistant that runs on Claude (the skill is called **Job Scout**). Each morning it:

- reads your job-alert emails and job listservs (read-only)
- checks live job boards, the organisations you care about and job-sharing Bluesky accounts
- confirms each posting is still open and finds the employer's own link
- scores every job against your experience (from your CVs and cover letters), with a one-line "why it fits" and "watch out"
- closes jobs whose deadlines have passed
- optionally flags jobs at organisations where you **know someone**, from your LinkedIn connections export
- keeps a **dashboard** and a **Google Sheet** tracker in sync, so you can move jobs from Suggested → Applied → Interviewing in either place

You set it up once by chatting with Claude. Your profile, jobs and settings stay private in your own Claude artifact and your own sheet.

## What you need

- A Claude account with artifacts and connectors
- **Gmail** and **Google Sheets** connectors (Settings → Connectors)
- A **web search** connector (for checking job pages and the dashboard's "Find new jobs" button)
- Somewhere to run it daily: Claude Code on the web, or the Claude desktop app's scheduled tasks
- Optional: Claude in Chrome, if you want a daily LinkedIn scan on your own computer

## Install

**Claude.ai or the desktop app (skill):** download [`dist/job-scout-skill.zip`](dist/job-scout-skill.zip) from this repo, then go to Settings → Capabilities → Skills → Upload skill.

**Claude Code (plugin):**

```bash
claude plugin marketplace add kewuh/progressive-job-matcher
```

```bash
claude plugin install job-scout@job-scout
```

Or copy `skills/job-scout` into `~/.claude/skills/`.

## Set up

Start a chat and say **"Set up Job Scout"**. Claude will:

1. Build your profile from your CV and what you're looking for: roles, levels, places, dealbreakers, and where your odds are best.
2. Publish your private dashboard.
3. Ask you to make a blank Google Sheet (it only ever writes to that one sheet) and set up the tracker tab.
4. Help you choose sources: email alerts and lists, organisations' job boards, sites to watch, Bluesky accounts.
5. Schedule the daily run.
6. Optionally, flag jobs where you know someone: upload your LinkedIn data export (Settings & Privacy → Data privacy → Get a copy of your data → Connections).
7. Optionally, set up the LinkedIn scan on your computer.

After that, ask **"run my job scan"** any time, or let the schedule do it.

## Safety

Job Scout is built to be safe to leave running:

- Gmail and Drive are **read-only**: it never sends, replies, drafts, labels or deletes.
- It writes only to your Job Scout dashboard and your one tracker sheet.
- It never logs in, creates accounts, applies, messages or posts for you, and never tries to get around a site's bot checks.
- It treats email and web content as data, not instructions.
- It skips personal emails that aren't about jobs, and doesn't store phone numbers or addresses.
- Your LinkedIn connections, if you upload them, stay in your private database. Their email addresses are never kept, and nothing is ever sent to them.

## What's in the repo

| Path | What it is |
|---|---|
| `skills/job-scout/SKILL.md` | The skill: what Job Scout is, ground rules, data model |
| `skills/job-scout/references/` | Setup guide, the daily-run prompt, scoring rules, how to find sources, the LinkedIn scan |
| `skills/job-scout/assets/dashboard.html` | The dashboard artifact |
| `skills/job-scout/scripts/live_boards.py` | Reads Greenhouse, Lever, Ashby, Rippling and UltiPro boards and Bluesky feeds |
| `skills/job-scout/scripts/contacts.py` | Groups your LinkedIn connections by employer and matches them to your jobs |
| `skills/job-scout/scripts/job_id.py` | The job-id hash shared with the dashboard |
| `skills/job-scout/templates/` | Example profile and config |
| `.claude-plugin/` | Claude Code plugin and marketplace manifests |
| `dist/job-scout-skill.zip` | The skill, zipped for upload to Claude |

Run the board scanner yourself with:

```bash
python3 skills/job-scout/scripts/live_boards.py --config my-config.json --out live.json
```

## License

MIT
