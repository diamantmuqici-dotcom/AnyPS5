import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SECRET = os.environ.get("UPSTREAM_WEBHOOK_SECRET", "").encode()
TOKEN = os.environ.get("FORK_DISPATCH_TOKEN", "")
REPO = os.environ.get("FORK_REPO", "diamantmuqici-dotcom/AnyPS5")
EVENT_TYPE = "upstream-push"
PORT = int(os.environ.get("SYNC_WEBHOOK_PORT", "8765"))


def verified(body, header):
    if not SECRET or not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(SECRET, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header[7:])


def dispatch(payload):
    if not TOKEN:
        return 503, "dispatch token missing"
    url = "https://api.github.com/repos/%s/dispatches" % REPO
    data = json.dumps({
        "event_type": EVENT_TYPE,
        "client_payload": {
            "upstream_ref": payload.get("ref", ""),
            "upstream_sha": payload.get("after", ""),
        },
    }).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Authorization": "Bearer " + TOKEN,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "anyps5-fork-sync",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status, "dispatched"
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")[:500]
    except Exception as exc:
        return 502, str(exc)


class Handler(BaseHTTPRequestHandler):
    def reply(self, code, message):
        body = json.dumps({"status": code, "message": message}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path.split("?")[0].rstrip("/") != "/sync":
            self.reply(404, "not found")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.reply(400, "bad length")
            return
        if length < 2 or length > 2_000_000:
            self.reply(400, "bad length")
            return
        body = self.rfile.read(length)
        if not verified(body, self.headers.get("X-Hub-Signature-256", "")):
            self.reply(401, "bad signature")
            return
        if self.headers.get("X-GitHub-Event", "") != "push":
            self.reply(200, "ignored event")
            return
        payload = json.loads(body)
        if payload.get("ref") != "refs/heads/main":
            self.reply(200, "ignored ref")
            return
        code, message = dispatch(payload)
        self.reply(code if code < 400 else 502, message)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    if not SECRET or not TOKEN:
        sys.exit("set UPSTREAM_WEBHOOK_SECRET and FORK_DISPATCH_TOKEN")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
