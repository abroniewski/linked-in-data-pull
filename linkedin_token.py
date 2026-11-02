"""Find the LinkedIn Member Data Portability token without ever printing it.

Order: LINKEDIN_TOKEN (environment or .env), macOS Keychain (service from LINKEDIN_KEYCHAIN_SERVICE, default
linkedin-dma-token), then token files
(.env / .env.txt next to these scripts, then ~/linkedin-feed/.env.txt). Token files hold one line:
LINKEDIN_TOKEN=... and must never be committed (.gitignore covers them).
"""
import os, subprocess

import config

HERE = os.path.dirname(os.path.abspath(__file__))
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
    keychain_service = config.get("LINKEDIN_KEYCHAIN_SERVICE", "linkedin-dma-token")
    token = config.get("LINKEDIN_TOKEN")
    if token:
        return token
    try:
        out = subprocess.run(["security", "find-generic-password", "-s", keychain_service, "-w"],
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
