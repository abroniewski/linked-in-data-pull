"""Find the LinkedIn Member Data Portability token without ever printing it.

Order: env LINKEDIN_TOKEN, macOS Keychain (service from env LINKEDIN_KEYCHAIN_SERVICE, default
linkedin-dma-token), then token files
(.env / .env.txt next to these scripts, then ~/linkedin-feed/.env.txt). Token files hold one line:
LINKEDIN_TOKEN=... and must never be committed (.gitignore covers them).
"""
import os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
KEYCHAIN_SERVICE = os.environ.get("LINKEDIN_KEYCHAIN_SERVICE", "linkedin-dma-token")
TOKEN_FILES = [os.path.join(HERE, ".env"), os.path.join(HERE, ".env.txt"), "~/linkedin-feed/.env.txt"]


def _from_file(path):
    try:
        with open(os.path.expanduser(path), encoding="utf-8-sig") as f:
            for line in f:
                k, _, v = line.strip().partition("=")
                if k.replace("export ", "").strip() == "LINKEDIN_TOKEN" and v.strip():
                    return v.strip().strip("'\"")
    except OSError:
        pass
    return ""


def find_token():
    token = os.environ.get("LINKEDIN_TOKEN", "").strip()
    if token:
        return token
    try:
        out = subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
                             capture_output=True, text=True)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except FileNotFoundError:  # not on macOS
        pass
    for path in TOKEN_FILES:
        token = _from_file(path)
        if token:
            return token
    return ""
