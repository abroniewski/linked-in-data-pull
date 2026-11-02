# Dependencies on this repo

Other projects read the files this repo writes. Changing them without coordination breaks those projects.

## mdi-market-trends (MDI daily market brief)

Repo: Moving-Data-Insights/mdi-market-trends (local `~/CODE_Repositories/mdi-market-brief`). It does no LinkedIn pulling of its own any more. It only reads two files from the output folder (`LINKEDIN_OUTPUT_DIR`, the Google Drive folder `AGENTS/data/linkedin-export/`):

| File | Written by | Shape the brief relies on |
|---|---|---|
| `CONNECTIONS.json` | `pull_linkedin.py` | JSON array of row objects exactly as LinkedIn's API returns them (`snapshotData` rows), UTF-8, indent 1. Rows repeat about 3 times, the brief de-duplicates by profile URL |
| `COMPANY_FOLLOWS.json` | `pull_linkedin.py` | Same: JSON array of row objects as returned by LinkedIn |

The brief re-scores the network whenever the hash of these files changes, so the snapshot job refreshes them every Sunday before the brief runs (see below). `pull_linkedin.py` writes a file only when its content changed, replaces it atomically, and never replaces a non-empty file with an empty result.

### Rules
- Do not rename these files, move the output folder, or change the JSON shape (field names, wrapping, row repetition handling) without telling the market-brief project first.
- Extra fields or datasets the brief needs: request them in this repo (they are probably already in the snapshot, which pulls every documented domain; see `_pull_report.json`), do not add a second LinkedIn pull in the brief repo.
- The brief's side of this note lives in its README.

## Schedule that keeps the files fresh
Weekly snapshot job `local.linkedin-snapshot`: Sundays 05:30 local time, through the launcher app. Install commands are in the README ("Weekly full snapshot"). The brief runs daily at 11:00.
