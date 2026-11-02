# linked-in-data-pull

Pull **your own** LinkedIn data through LinkedIn's Member Data Portability API, into a folder you choose. Standard-library Python 3, no installs.

| Script | What it does |
|---|---|
| `pull_linkedin.py` | Full snapshot: one JSON file per domain, for every domain LinkedIn documents (about 67: connections, inbox, invitations, jobs, profile, comments, likes, login history, ...), plus `_pull_report.json` with row counts per domain |
| `pull_changelog.py` | New messages and invitations from the change-log feed, as a dated Markdown digest. Meant to run daily |
| `DEPENDENCIES.md` | Who reads the output files, and what must not change without coordination |
| `config.py`, `linkedin_token.py` | Settings (`.env`) and token lookup shared by both |

## Before you start

- **Availability.** The Member Data Portability API exists because of the EU Digital Markets Act. As far as we know it is offered to members in the EU/EEA and Switzerland; check LinkedIn's developer docs for your region and read LinkedIn's API terms.
- **You need your own app and token.** LinkedIn developer portal: create an app, add the "Member Data Portability API (Member)" product, then Docs and tools > OAuth Token Tools > Create token with scope `r_dma_portability_self_serve`. Tokens expire after about 60 days.
- **Privacy.** The output contains other people's names and messages. Keep it somewhere private, never commit it, never upload it to a public place. `.gitignore` blocks `.env`, `*.json`, `*.jsonl`, `*.csv`, `*.log`, `output/`, `changelog/` and `companies.txt`, but `.gitignore` can't protect a file you force-add, so keep the output folder outside this repo. The scripts print counts only, never the token or profile data.

## Setup

    cp .env.example .env      # then edit .env

`.env` is gitignored and holds your settings. `.env.example` lists every setting:

| Setting | What it does |
|---|---|
| `LINKEDIN_OUTPUT_DIR` | The folder every run writes to: snapshot files directly in it, plus `changelog/` and an optional `companies.txt`. Point it at a synced folder (Google Drive, Dropbox) to have the data available everywhere. Default `./output` |
| `LINKEDIN_TOKEN` | Your token (optional here, see below) |
| `LINKEDIN_KEYCHAIN_SERVICE` | macOS Keychain service holding the token (default `linkedin-dma-token`) |
| `LINKEDIN_DOMAINS` | Comma-separated domains to pull. Blank = all |

Real environment variables override `.env`. Use another file with `LINKEDIN_ENV_FILE=/path/to/file`.

### Token

Checked in this order: `LINKEDIN_TOKEN` (environment or `.env`), then macOS Keychain
(`security add-generic-password -U -s linkedin-dma-token -a "$USER" -w`), then a file containing one line `LINKEDIN_TOKEN=...` (`.env.txt` here, or `~/linkedin-feed/.env.txt`). A 401 prints "token expired"; update the token and re-run.

## Full snapshot

    python3 pull_linkedin.py                       # all domains into LINKEDIN_OUTPUT_DIR
    python3 pull_linkedin.py --domains CONNECTIONS,PROFILE
    python3 pull_linkedin.py /some/other/folder    # overrides LINKEDIN_OUTPUT_DIR

Files are overwritten in place on each run (keep history with your sync tool or git, not by dated copies). A run never replaces a non-empty file with an empty result. LinkedIn compiles domains at different speeds and some are only available to some members, so check `_pull_report.json` for which domains returned rows and re-run later for the empty ones. `CONNECTIONS.json` can repeat rows, so de-duplicate by profile URL.

## Daily change-log digest (macOS launchd)

Scheduled jobs on macOS can't answer permission prompts, so they can't read a Google Drive folder on their own. Instead of giving Python Full Disk Access, the job goes through one small launcher app that holds the permission:

    ./launchd/build-runner-app.sh           # compiles and builds ~/Applications/Agent Job Runner.app (ad-hoc signed; needs the Xcode command line tools)
    open -W -a "$HOME/Applications/Agent Job Runner.app" --args "$PWD/launchd/run-changelog.sh"
                                            # permission test, run once in Terminal; click Allow if macOS asks
                                            # about files managed by Google Drive (if it asks for something else, see below)
    ./launchd/install.sh                    # daily 08:30
    LABEL=my.linkedin-changelog HOUR=7 MINUTE=0 ./launchd/install.sh

The launcher (`launchd/agent-job-runner.c`) only runs an executable script that sits inside `~/CODE_Repositories`, so it can't be used to run arbitrary commands. It starts `/bin/zsh SCRIPT ARGS` as a child and stays the parent until the job ends. Its contract for any job: `open -W -a "<app>" --args SCRIPT [ARGS]`. The script gets only the minimal environment macOS gives apps, no working directory, and no log redirection from launchd, so it must `cd`, set `PATH`/`USER` if it needs them, and redirect its own output (see `launchd/run-changelog.sh`).

Needs `.env` first (the job reads `LINKEDIN_OUTPUT_DIR` from it). State, digests (`changelog/`) and the optional `companies.txt` live in the output folder. The log is `~/Library/Logs/<LABEL>.log`. If macOS never shows a Google Drive prompt and the test fails with "Operation not permitted", grant the app (not Python) Full Disk Access in System Settings > Privacy & Security.

Remove it: `launchctl bootout gui/$(id -u)/local.linkedin-changelog && rm ~/Library/LaunchAgents/local.linkedin-changelog.plist`

## Weekly full snapshot (macOS launchd)

Keeps the full snapshot (all domains, including `CONNECTIONS.json` and `COMPANY_FOLLOWS.json`) fresh. Same launcher app and setup as above, a different job:

    JOB=snapshot ./launchd/install.sh       # Sundays 05:30, label local.linkedin-snapshot, log ~/Library/Logs/local.linkedin-snapshot.log
    launchctl kickstart -k gui/$(id -u)/local.linkedin-snapshot     # run it once now

Override with `LABEL`, `HOUR`, `MINUTE`, `WEEKDAY` (0 = Sunday ... 6; `WEEKDAY=any` for every day). A run only rewrites files whose content changed. Other projects depend on these files: see DEPENDENCIES.md.

## License

MIT, see LICENSE.
