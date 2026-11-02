# linked-in-data-pull

Pull **your own** LinkedIn data through LinkedIn's Member Data Portability API. Standard-library Python 3, no installs.

| Script | What it does | Where its output goes |
|---|---|---|
| `pull_linkedin.py` | Full snapshot: one JSON file per domain (connections, inbox, invitations, job applications, saved jobs, profile, ...) | Folder you pass, default `./linkedin-export` |
| `pull_changelog.py` | New messages and invitations from the change-log feed, as a dated Markdown digest. Meant to run daily | `~/linkedin-feed/changelog/` (or `--data-dir`) |
| `linkedin_token.py` | Shared token lookup used by both | |

## Before you start

- **Availability.** The Member Data Portability API exists because of the EU Digital Markets Act. As far as we know it is offered to members in the EU/EEA and Switzerland; check LinkedIn's developer docs for your region and read LinkedIn's API terms.
- **You need your own app and token.** LinkedIn developer portal: create an app, add the "Member Data Portability API (Member)" product, then Docs and tools > OAuth Token Tools > Create token with scope `r_dma_portability_self_serve`. Tokens expire after about 60 days.
- **Privacy.** The output contains other people's names and messages. Keep it on your own machine, never commit it, never upload it. `.gitignore` blocks `.env*`, `*.json`, `*.jsonl`, `*.csv`, `*.log`, `linkedin-export/`, `changelog/`, `data/` and `companies.txt`, but `.gitignore` can't protect a file you force-add, so keep exports outside the repo. The scripts print counts only, never the token or profile data.

## Token

Checked in this order:

1. `export LINKEDIN_TOKEN='...'` in the shell (one-off runs).
2. macOS Keychain (recommended; launchd can read it):
   `security add-generic-password -U -s linkedin-dma-token -a "$USER" -w`
   Use another service name by setting `LINKEDIN_KEYCHAIN_SERVICE`.
3. A token file containing one line `LINKEDIN_TOKEN=...`: `.env` or `.env.txt` in this folder (gitignored), or `~/linkedin-feed/.env.txt`.

A 401 prints "token expired". Update the token and re-run.

## Full snapshot

    python3 pull_linkedin.py ~/linkedin-export
    python3 pull_linkedin.py ~/linkedin-export --domains CONNECTIONS,COMPANY_FOLLOWS,POSITIONS

Some domains fill in later on LinkedIn's side; re-run if a domain shows 0 rows. `CONNECTIONS.json` can repeat rows, so de-duplicate by profile URL.

## Daily change-log digest (macOS launchd)

    ./launchd/install.sh                    # daily 08:30, data in ~/linkedin-feed
    LABEL=my.linkedin-changelog HOUR=7 MINUTE=0 DATA_DIR=~/somewhere ./launchd/install.sh

State, digests and the optional `companies.txt` (company names to flag, one per line) live in the data folder, outside the repo. Keep that folder out of `~/Documents`, `~/Desktop` and `~/Downloads`: macOS blocks launchd jobs from reading them.

Remove it: `launchctl bootout gui/$(id -u)/local.linkedin-changelog && rm ~/Library/LaunchAgents/local.linkedin-changelog.plist`

## License

MIT, see LICENSE.
