#!/usr/bin/env python3
"""Pull your recent LinkedIn activity via the Member Data Portability change-log feed.

Usage: python3 pull_changelog.py [--data-dir DIR]

DIR (default: LINKEDIN_OUTPUT_DIR from .env, see .env.example) holds all output, outside this repo:
  changelog/state.json        last processedAt
  changelog/events.jsonl      raw events, de-duplicated by id
  changelog/digest-YYYY-MM-DD.md   digest of NEW events only
  companies.txt               optional: company names to flag, one per line
Token lookup: see linkedin_token.py. Never prints the token.
"""
import datetime as dt, json, os, sys, time, urllib.error, urllib.request

import config
from linkedin_token import find_token

API = "https://api.linkedin.com/rest/"


def data_dir():
    args = sys.argv[1:]
    if "--data-dir" in args:
        return os.path.expanduser(args[args.index("--data-dir") + 1])
    return config.output_dir()


def _private(path, mode):
    """Tighten permissions where the filesystem allows it (cloud-synced folders such as Google Drive refuse chmod)."""
    try:
        os.chmod(path, mode)
    except OSError:
        pass


def call(url, token, method="GET", body=None):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None, headers={
        "Authorization": f"Bearer {token}", "Linkedin-Version": "202312",
        "X-Restli-Protocol-Version": "2.0.0", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        if e.code == 401:
            sys.exit("token expired: regenerate in the developer portal")
        e.detail = e.read().decode(errors="ignore")[:300]
        raise


def ensure_authorization(token):
    url = API + "memberAuthorizations?q=memberAndApplication"
    try:
        if call(url, token).get("elements"):
            return
    except urllib.error.HTTPError as e:
        if e.code not in (400, 403, 404):
            raise
    try:
        call(API + "memberAuthorizations", token, "POST", {})
    except urllib.error.HTTPError as e:
        sys.exit(f"memberAuthorizations failed: HTTP {e.code} {getattr(e, 'detail', '')}")


def fetch_events(token, start):
    events, seen = [], set()
    while True:
        q = f"{API}memberChangeLogs?q=memberAndApplication&count=50"
        if start:
            q += f"&startTime={start}"
        try:
            data = call(q, token)
        except urllib.error.HTTPError as e:
            sys.exit(f"memberChangeLogs failed: HTTP {e.code} {getattr(e, 'detail', '')}")
        els = [e for e in data.get("elements", []) if e.get("id") not in seen]
        if not els:
            break
        for e in els:
            seen.add(e.get("id"))
        events.extend(els)
        last = max(e.get("processedAt", 0) for e in els)
        if len(data.get("elements", [])) < 50 or last <= (start or 0):
            break
        start = last + 1
        time.sleep(0.3)
    return events


def flat(o):
    if isinstance(o, dict):
        return " ".join(flat(v) for v in o.values())
    if isinstance(o, list):
        return " ".join(flat(v) for v in o)
    return str(o)


def companies(base):
    """Company names to flag in events: companies.txt in the data dir, one per line (optional)."""
    path = os.path.join(base, "companies.txt")
    if not os.path.exists(path):
        return set()
    return {l.strip() for l in open(path, encoding="utf-8") if l.strip() and not l.startswith("#")}


def when(ms):
    return dt.datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M") if ms else "?"


def main():
    token = find_token()
    if not token:
        sys.exit("No LinkedIn token found (env LINKEDIN_TOKEN, Keychain or a token file; see linkedin_token.py).")
    base = data_dir()
    out = os.path.join(base, "changelog")
    os.makedirs(out, exist_ok=True)
    _private(out, 0o700)
    sp, ep = os.path.join(out, "state.json"), os.path.join(out, "events.jsonl")
    state = json.load(open(sp)) if os.path.exists(sp) else {}
    known = set()
    if os.path.exists(ep):
        known = {json.loads(l).get("id") for l in open(ep, encoding="utf-8") if l.strip()}
    ensure_authorization(token)
    events = fetch_events(token, state.get("lastProcessedAt"))
    new = [e for e in events if e.get("id") not in known]
    with open(ep, "a", encoding="utf-8") as f:
        for e in new:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    if events:
        state["lastProcessedAt"] = max(max(e.get("processedAt", 0) for e in events), state.get("lastProcessedAt", 0))
        json.dump(state, open(sp, "w"))
    cos = companies(base)
    msgs, invs, hits, other = [], [], [], 0
    for e in new:
        res = (e.get("resourceName") or "").lower()
        txt = flat(e.get("activity", {}))
        line = f"{when(e.get('capturedAt'))} | {e.get('method','')} | {res}"
        if "message" in res and e.get("method") in ("CREATE", None):
            a = e.get("activity", {})
            sender = a.get("actor") or e.get("actor") or "?"
            msgs.append(f"- {line} | from {sender} | thread {a.get('conversationId') or a.get('threadId') or e.get('resourceId','?')} | {txt[:200]!r}")
        elif "invitation" in res:
            invs.append(f"- {line} | {txt[:160]!r}")
        else:
            other += 1
        m = [c for c in cos if c.lower() in txt.lower()]
        if m:
            hits.append(f"- {line} | mentions {', '.join(sorted(m))} | {txt[:160]!r}")
    day = dt.date.today().isoformat()
    body = [f"# LinkedIn change-log digest {day} (private)", "",
            f"New events: {len(new)} (fetched {len(events)}, already stored {len(events)-len(new)}). Other event types: {other}.", "",
            "## Messages", *(msgs or ["- none"]), "", "## Invitations", *(invs or ["- none"]), "",
            "## Mentions of watched companies", *(hits or ["- none"])]
    path = os.path.join(out, f"digest-{day}.md")
    if os.path.exists(path):
        if not new:
            print(f"events fetched={len(events)} new=0 (digest for {day} left as is)")
            return
        body[0] = f"# Additional events at {dt.datetime.now():%H:%M}"
        open(path, "a", encoding="utf-8").write("\n" + "\n".join(body) + "\n")
    else:
        open(path, "w", encoding="utf-8").write("\n".join(body) + "\n")
    _private(path, 0o600)
    print(f"events fetched={len(events)} new={len(new)} messages={len(msgs)} invitations={len(invs)} company_mentions={len(hits)} -> {os.path.basename(path)}")


if __name__ == "__main__":
    main()
