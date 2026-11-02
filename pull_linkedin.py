#!/usr/bin/env python3
"""Pull your own LinkedIn data via the Member Data Portability API (snapshot domains).

Usage:
  python3 pull_linkedin.py [outdir] [--domains CONNECTIONS,INBOX,...]

Output folder: the outdir argument, else LINKEDIN_OUTPUT_DIR from .env (see .env.example).
Pulls every domain LinkedIn documents unless LINKEDIN_DOMAINS or --domains narrows it. Writes one JSON file per
domain plus _pull_report.json (counts and status only). The export holds other people's names and messages:
keep it somewhere private and never commit it. A run never replaces a non-empty file with an empty result.
Token lookup: see linkedin_token.py. Prints counts only, never the token or profile data.
"""
import datetime as dt, json, os, sys, time, urllib.error, urllib.request

import config
from linkedin_token import find_token

# The 66 domains on LinkedIn's snapshot-domain reference (checked 2026-11-02), plus GROUP_POSTS from its API example.
# Domains fill in on LinkedIn's side at different times: one that is empty or unknown today may have data on a later run.
ALL_DOMAINS = [
    "ACCOUNT_HISTORY", "ACTOR_SAVE_ITEM", "AD_TARGETING", "ADS_CLICKED", "ADS_LAN", "ALL_COMMENTS", "ALL_LIKES",
    "ALL_VOTES", "ARTICLES", "CAUSES_YOU_CARE_ABOUT", "CERTIFICATIONS", "COMPANY_FOLLOWS", "CONNECTIONS", "CONTACTS",
    "COURSES", "EASYAPPLY_BLOCKING", "EDUCATION", "EMAIL_ADDRESSES", "ENDORSEMENTS", "EVENTS", "GROUP_POSTS", "GROUPS",
    "HONORS", "IDENTITY_CREDENTIALS_AND_ASSETS", "INBOX", "INFERENCE_TAKEOUT", "INSTANT_REPOSTS", "INVITATIONS",
    "JOB_APPLICANT_SAVED_ANSWERS", "JOB_APPLICATIONS", "JOB_POSTINGS", "JOB_SEEKER_PREFERENCES", "LANGUAGES",
    "LEARNING", "LEARNING_COACH_AI_TAKEOUT", "LEARNING_COACH_INBOX", "LEARNING_ROLEPLAY_INBOX", "LOGIN",
    "MARKETPLACE_ENGAGEMENTS", "MARKETPLACE_OPPORTUNITIES", "MARKETPLACE_PROVIDERS", "MEMBER_FOLLOWING",
    "MEMBER_SHARE_INFO", "ORGANIZATIONS", "PATENTS", "PHONE_NUMBERS", "POSITIONS", "PREMIUM_NOTES", "PROFILE",
    "PROFILE_SUMMARY", "PROJECTS", "PUBLICATIONS", "RECEIPTS", "RECEIPTS_LBP", "RECOMMENDATIONS", "REGISTRATION",
    "REVIEWS", "RICH_MEDIA", "SAVED_JOB_ALERTS", "SAVED_JOBS", "SEARCHES", "SECURITY_CHALLENGE_PIPE", "SKILLS",
    "TALENT_QUESTION_SAVED_RESPONSE", "TEST_SCORES", "TRUSTED_GRAPH", "VOLUNTEERING_EXPERIENCES",
]
BASE = "https://api.linkedin.com/rest/memberSnapshotData?q=criteria&domain="


def get(url, token):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Linkedin-Version": "202312",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def pull(domain, token):
    """Return (rows, note). note is "" normally, or why there is nothing (e.g. HTTP 400/404)."""
    rows, start, note = [], 0, ""
    while True:
        try:
            data = get(f"{BASE}{domain}&start={start}", token)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                sys.exit("token expired: create a new one in the LinkedIn developer portal (OAuth Token Tools)")
            body = e.read().decode(errors="ignore")
            # docs: keep paging until "No data found for this memberId"
            if e.code in (404, 400) or "No data found" in body:
                if not rows:
                    note = f"HTTP {e.code}: no data or domain not available"
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
    return rows, note


def write_json(path, obj):
    """Write JSON atomically, and not at all if the file already holds exactly this content
    (a sync client then sees no change, and Drive's version history is not filled with identical copies)."""
    text = json.dumps(obj, indent=1, ensure_ascii=False)
    try:
        with open(path, encoding="utf-8") as f:
            if f.read() == text:
                return False
    except OSError:
        pass
    tmp = os.path.join(os.path.dirname(path), "." + os.path.basename(path) + ".tmp")  # replace atomically so a sync client never sees half a file
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)
    return True


def main():
    args = sys.argv[1:]
    domains = [d.strip().upper() for d in config.get("LINKEDIN_DOMAINS").split(",") if d.strip()] or ALL_DOMAINS
    if "--domains" in args:
        i = args.index("--domains")
        domains = [d.strip().upper() for d in args[i + 1].split(",") if d.strip()]
        del args[i:i + 2]
    token = find_token()
    if not token:
        sys.exit("No LinkedIn token found (env LINKEDIN_TOKEN, .env, Keychain or a token file; see README).")
    out = os.path.expanduser(args[0]) if args else config.output_dir()
    os.makedirs(out, exist_ok=True)
    report = {"at": dt.datetime.now().isoformat(timespec="seconds"), "domains": {}}
    for d in domains:
        path = os.path.join(out, f"{d}.json")
        try:
            rows, note = pull(d, token)
        except Exception as e:
            report["domains"][d] = {"rows": None, "status": f"FAILED {type(e).__name__}"}
            print(f"{d}: FAILED ({type(e).__name__})")
            continue
        status = note or "ok"
        if not rows and os.path.exists(path) and os.path.getsize(path) > 2:
            status = "kept previous file (this run returned nothing)"
        else:
            write_json(path, rows)
        report["domains"][d] = {"rows": len(rows), "status": status}
        print(f"{d}: {len(rows)} rows" + ("" if status == "ok" else f" ({status})"))
    write_json(os.path.join(out, "_pull_report.json"), report)
    empty = sorted(d for d, v in report["domains"].items() if not v["rows"])
    print(f"Done. {len(domains) - len(empty)} domains with data, {len(empty)} empty or unavailable. Report: _pull_report.json")


if __name__ == "__main__":
    main()
