import json
import os
import subprocess
import sys
import time
import urllib.request

REPO = os.environ.get("UPSTREAM_REPO", "boykopovar/AnyPS5")
BRANCH = os.environ.get("UPSTREAM_BRANCH", "main")
INTERVAL = int(os.environ.get("SYNC_POLL_SECONDS", "60"))
WORKDIR = os.environ.get("SYNC_WORKDIR", os.getcwd())
SCRIPT = os.environ.get("SYNC_SCRIPT", "tools/sync_upstream.ps1")
STATE = os.environ.get("SYNC_STATE_FILE", os.path.join(WORKDIR, "fork", "LAST_SYNC_UPSTREAM"))


def head_sha():
    url = "https://api.github.com/repos/%s/commits/%s" % (REPO, BRANCH)
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "anyps5-fork-sync",
    })
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)["sha"]


def last_synced():
    try:
        with open(STATE, encoding="utf-8") as handle:
            return handle.read().strip()
    except OSError:
        return ""


def run_sync():
    command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
               "-File", SCRIPT, "-WorkDir", WORKDIR, "-Push"]
    result = subprocess.run(command, cwd=WORKDIR)
    if result.returncode != 0:
        raise RuntimeError("sync script exited %d" % result.returncode)


def main():
    while True:
        try:
            current = head_sha()
            recorded = last_synced()
            if current and current != recorded:
                print("%s -> %s, syncing" % (recorded or "none", current), flush=True)
                run_sync()
                print("synced to %s" % current, flush=True)
            else:
                print("up to date at %s" % current, flush=True)
        except Exception as exc:
            print("poll error: %s" % exc, flush=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
