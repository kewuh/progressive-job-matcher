# Setting up Job Scout

Work through these steps with the user. Ask questions in small batches, propose sensible defaults, and keep moving. Setup usually takes 15–30 minutes.

## 1. Build the profile (the most important step)

Ask the user for:

1. **Their CV or LinkedIn summary.** Ask them to paste it or attach the file. If they keep CVs in Google Drive, you may read them (read-only) with their permission.
2. **What they want:** job types and titles, levels (be generous: include one level below and above), sectors and causes, salary floor if any.
3. **Where:** home city, whether remote is fine, any second cities. Ask if some places should score a bit lower.
4. **Dealbreakers:** e.g. no corporate marketing, no relocation, no fixed-term.
5. **Where their odds are best:** past interviews and rejections tell you a lot. If they've applied to jobs before, ask which ones got interviews. Small and mid-sized organisations often respond better than famous institutions.
6. **Pronouns**, and any personal topics the scan should never read about (e.g. medical, legal, immigration, family).

Write the profile doc (see `templates/profile.example.json`):

- `summary`: 150–300 words, specific, with numbers. This is what every job is scored against.
- `prefs`: locations, levels, must-haves, dealbreakers, best-odds organisation types, and "BE EXPANSIVE" unless they want a tight list.
- `locations` (plain text) and `locationFilters` (2–4 dashboard filter options, each a label plus a lowercase regex such as `new york|nyc|brooklyn|remote`).
- `queries`: 8–15 short search phrases covering their titles, skills and causes.

Show them the summary and prefs and ask them to correct anything.

## 2. Publish the dashboard

Publish `assets/dashboard.html` as a new artifact with the Artifact tool, with capabilities:

```json
{"db": {}, "user": {}, "sample": {}, "mcp": {"servers": [{"server": "<their web-search connector name>", "tools": ["web_search", "web_fetch"]}]}}
```

The dashboard calls a web-search connector named in the constant `SEARCH_SERVER` near the top of its script (default `"Parallel Search"`). If the user's search connector has a different name or different tool names, change that constant and the tool names in `fetchPages` and the search handler before publishing. If they have no search connector, publish without `mcp`; the daily run still works, only the "Find new jobs" button won't.

Then write the profile doc and an initial config doc to `data/users/me` with ArtifactData. Give the user the artifact link. All their data stays private to them.

## 3. Create the tracker sheet

Ask the user to create a blank Google Sheet (sheets.new), rename the first tab to `Jobs`, and paste you the link. Don't create it yourself: Job Scout only writes to a sheet the user made. Take the ID from the URL (between `/d/` and `/edit`).

Write the header row:

`Status, Fit, Title, Organisation, Location, Salary, Posted, Closes (deadline), Still open?, Source, Found, Why it fits, Notes, Link, ID, Contacts`

(write it to `Jobs!A1:P1`). Save `sheetId`, `sheetTab` ("Jobs"), `sheetUrl` and `sheetColumns` in config. Tell them they can edit Status, Fit and Notes in the sheet, add their own rows (Title + Link, ID blank), and delete rows they don't care about; the daily run picks those changes up.

## 4. Choose sources

Go through `references/sources.md` with them:

- **Email:** which job newsletters, alerts and listservs they already get (or should sign up for). Record sender addresses and Google Groups addresses in `config.email`. Suggest a Gmail label (e.g. "Jobs") for anything else they want read.
- **Live boards:** organisations they'd love to work for. For each, find the careers page; if it's on Greenhouse, Lever, Ashby, Rippling or UltiPro, add it to `liveBoards` (these are read completely every day). Otherwise add it to `orgWatch` with its careers URL.
- **Watchlist pages:** job boards and searches for their field (`watch[]`).
- **Bluesky:** job-board and organisation accounts in their field (`bluesky.handles`); accounts that only post jobs go in `announceAllHandles` too.
- **Filters:** set `filters.titleInclude`, `titleExclude` and `locationInclude` (regex fragments) to match their field and places. These only pre-filter live boards; scoring still decides.

Aim for 10–30 live boards and orgs to start; they can add more any time.

## 5. Schedule the daily run

Create a daily scheduled task at a time that suits them (outside 6–9am US Pacific is less busy). Its prompt should be the full contents of `references/daily-run.md` with these filled in at the top:

- the dashboard artifact URL
- the sheet ID
- the person's name and pronouns
- their email query (built from `config.email`, see daily-run step 3)

Which tool to use depends on where they run Claude:

- **Claude Code on the web / cloud session:** `create_trigger` (fresh session each day is fine; all state is in the database).
- **Claude desktop app:** a scheduled task in the app.
- **Anywhere else:** tell them to run "run my job scan" each morning.

If the scheduled task needs connectors (Gmail, Sheets, search), make sure they're attached to it, and tell the user if any couldn't be.

## 6. First run

Offer to run the daily scan now so they see results. Afterwards, walk them through the dashboard and the sheet, and ask what looks wrong: bad matches mean the profile or prefs need tightening; missing jobs mean a source is missing.

## 7. Optional: contacts

Offer to flag jobs where they know someone: they upload their LinkedIn data export and you follow `references/linkedin-contacts.md`. It takes about 10 minutes, mostly waiting for LinkedIn's email.

## 8. Optional: LinkedIn on their computer

If they use the Claude desktop app with Claude in Chrome and are signed in to LinkedIn, offer the browser scan in `references/linkedin-browser-scan.md`. It runs as a scheduled task on their own computer and adds rows to the sheet.
