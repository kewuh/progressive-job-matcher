# Contacts: flag jobs where you know someone

A warm introduction is often the best way into a job. This feature reads the user's LinkedIn connections, groups them by current employer, and flags every tracked job at an organisation where they know someone: on the dashboard ("You know 3 people here", with names and LinkedIn links), with a "Where I know someone" filter, and in a "Contacts" column in the sheet.

## 1. Getting the LinkedIn export

Tell the user:

1. On LinkedIn, go to **Me → Settings & Privacy → Data privacy → Download your data** (older versions call it "Get a copy of your data").
2. Choose the option to pick particular files ("Want something in particular?"), tick **Connections** only, and click **Request archive**. LinkedIn may ask for their password. (Connections alone usually arrives within 10–20 minutes; a full archive can take a day.)
3. When LinkedIn's email arrives, go back to the same page and click **Download archive**. It's a `.zip` containing `Connections.csv`.
4. Upload the zip, or just `Connections.csv`, here.

Connections only show a company if the contact lists one on their profile, and LinkedIn lets members hide their email from the export. Both are normal.

## 2. Building the network

With a shell: `python3 scripts/contacts.py build --linkedin <file> --out network.json`. Without one, read the CSV yourself (skip the "Notes" lines above the `First Name,Last Name,...` header) and build the same structure.

It keeps each contact's name, position, connected-on date and profile link, grouped by company. **It never keeps their email addresses.**

Store it in the user's private database as `data/users/me/network` (set; `if_version` if it exists): `{builtAt, source, connections, orgs: {key: {org, people: [...]}}}`. If the file is over ~900 KB, split `orgs` across `network-1`, `network-2`, … and put `{parts: n}` in `network`.

Tell the user how many connections and organisations were found, and the top 10 organisations by number of contacts.

## 3. Matching

Run `python3 scripts/contacts.py match --network network.json --jobs-dir <jobs folder> --out matches.json`, or match by hand using the same rules:

- Compare organisation names after lowercasing and removing punctuation, a leading "The", legal suffixes (Inc, LLC, Ltd…) and bracketed parts.
- Also match a bracketed acronym ("Natural Resources Defense Council (NRDC)" matches "NRDC").
- A shorter name matches a longer one only on whole words at the start and only if it's distinctive (2+ words or 6+ letters): "Planned Parenthood" matches "Planned Parenthood Federation of America", but "Planned Parenthood of Greater New York" stays separate, and "Action" matches nothing.
- Ignore generic employers: self-employed, freelance, confidential, stealth.

For each matched job, update its document with `contactsCount`, `contacts` (up to 5: `{name, position, url}`) and `contactsOrg` (the employer as written on LinkedIn). Clear those fields from jobs that no longer match. Batch writes (≤ 50 per batch, `if_version`).

Then fill the sheet's **Contacts** column (P; add the header if it's missing) for matched rows, e.g. `Alex Example (Digital Strategist); Sam Sample (Designer); +1 more`.

Finally, report the matched jobs with the most contacts and the highest fit first, and suggest the user ask one of those contacts about the role or the team. Don't draft or send messages to contacts unless the user asks, and never send anything yourself.

## 4. Every day after that

The daily run (step 5b in `references/daily-run.md`) matches new jobs against the stored network. When the user uploads a new export (suggest every 2–3 months), rebuild the network and rematch all jobs.

## Privacy

Connections are other people's information. Keep it to what's useful:

- Store the network only in the user's own private Job Scout database, never in a repository, a shared file or a public artifact.
- Keep names, positions and profile links; never email addresses.
- If the user shares their tracker sheet with anyone, point out that the Contacts column shows contacts' names, and offer to leave that column empty.
- If the user asks to delete their network, delete `network` (and any parts) and clear `contacts`, `contactsCount` and `contactsOrg` from every job.
