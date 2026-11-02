"""Settings for the LinkedIn pull scripts, read from a .env file.

Copy .env.example to .env (gitignored) in this folder and fill it in. Real environment variables win over
.env. Set LINKEDIN_ENV_FILE to read a different file. Nothing here ever prints a value.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_loaded = False


def _parse(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                k, _, v = line.partition("=")
                k = k.replace("export ", "").strip()
                v = v.strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
                    v = v[1:-1]
                if k and v:
                    os.environ.setdefault(k, v)
    except OSError:
        pass


def load():
    global _loaded
    if _loaded:
        return
    _loaded = True
    _parse(os.path.expanduser(os.environ.get("LINKEDIN_ENV_FILE", os.path.join(HERE, ".env"))))


def get(name, default=""):
    load()
    return os.environ.get(name, default).strip()


def output_dir():
    """Root folder for everything the scripts write (snapshot files, changelog/, companies.txt)."""
    return os.path.expanduser(get("LINKEDIN_OUTPUT_DIR", os.path.join(HERE, "output")))
