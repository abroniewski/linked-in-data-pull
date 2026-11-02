#!/usr/bin/env python3
"""Pull your own LinkedIn data via the Member Data Portability API (snapshot domains).

Usage:
  python3 pull_linkedin.py [outdir] [--domains CONNECTIONS,INBOX,...]

Writes one JSON file per domain into outdir (default: ./linkedin-export). The export holds other people's
names and messages: keep outdir outside this repo (or inside it, where .gitignore blocks it) and never upload it.
Token lookup: see linkedin_token.py. Prints row counts only, never the token or profile data.
"""
import json, os, sys, time, urllib.error, urllib.request

from linkedin_token import find_token

DOMAINS = [
    "CONNECTIONS", "INBOX", "INVITATIONS", "JOB_APPLICATIONS", "SAVED_JOBS",
    "SAVED_JOB_ALERTS", "JOB_SEEKER_PREFERENCES", "COMPANY_FOLLOWS", "SEARCHES",
    "POSITIONS", "SKILLS", "EDUCATION", "CERTIFICATIONS", "RECOMMENDATIONS",
    "ENDORSEMENTS", "PROFILE", "JOB_APPLICANT_SAVED_ANSWERS", "PREMIUM_NOTES",
]
BASE = "https://api.linkedin.com/rest/memberSnapshotData?q=criteria&domain="


def get(url, token):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Linkedin-Version": "202312",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def pull(domain, token):
    rows, start = [], 0
    while True:
        try:
            data = get(f"{BASE}{domain}&start={start}", token)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                sys.exit("token expired: create a new one in the LinkedIn developer portal (OAuth Token Tools)")
            body = e.read().decode(errors="ignore")
            # docs: keep paging until "No data found for this memberId"
            if e.code in (404, 400) or "No data found" in body:
                break
            raise
        els = data.get("elements", [])
        if not els:
            break
        for el in els:
            rows.extend(el.get("snapshotData", []))
        if not any(l.get("rel") == "next" for l in data.get("paging", {}).get("links", [])):
            break
        start += 1
        time.sleep(0.3)
    return rows


def main():
    args = sys.argv[1:]
    domains = DOMAINS
    if "--domains" in args:
        i = args.index("--domains")
        domains = [d.strip().upper() for d in args[i + 1].split(",") if d.strip()]
        del args[i:i + 2]
    token = find_token()
    if not token:
        sys.exit("No LinkedIn token found (env LINKEDIN_TOKEN, Keychain or a token file; see linkedin_token.py).")
    out = os.path.expanduser(args[0]) if args else "linkedin-export"
    os.makedirs(out, exist_ok=True)
    os.chmod(out, 0o700)
    for d in domains:
        try:
            rows = pull(d, token)
        except Exception as e:
            print(f"{d}: FAILED ({type(e).__name__})")
            continue
        path = os.path.join(out, f"{d}.json")
        with open(path, "w") as f:
            json.dump(rows, f, indent=1, ensure_ascii=False)
        os.chmod(path, 0o600)
        print(f"{d}: {len(rows)} rows")


if __name__ == "__main__":
    main()
