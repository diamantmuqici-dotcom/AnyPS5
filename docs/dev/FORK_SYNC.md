# Fork sync

This fork mirrors `boykopovar/AnyPS5`. Upstream is the source of truth for every tracked source file. Files that exist only in this fork (`build-relinker/`, `fork/`, `docs/dev/FORK_SYNC.md`, `tools/fork_sync_fixups.py`, `tools/sync_upstream.ps1`, `tools/webhook_upstream_sync.py`, `.github/workflows/sync-upstream.yml`) survive every sync.

## Automatic sync (GitHub Actions)

`.github/workflows/sync-upstream.yml` runs every 15 minutes and on manual dispatch. It fetches upstream `main`, merges with `-X theirs` so upstream wins content conflicts, restores fork notes through `tools/fork_sync_fixups.py`, records the mirrored SHA in `fork/LAST_SYNC_UPSTREAM`, and pushes to this fork's `main`.

Required secrets in this fork (Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `SYNC_TOKEN` | Personal access token with `repo` write scope on this fork. Required because `GITHUB_TOKEN` cannot push to a repository's default branch under some branch-protection rules. |

Trigger manually with `workflow_dispatch` from the Actions tab.

## Immediate webhook sync

For near-instant mirroring when upstream pushes, `tools/webhook_upstream_sync.py` verifies GitHub `push` webhooks from upstream and fires a `repository_dispatch` event that starts the same workflow in seconds.

Host the receiver on a machine reachable from the internet, behind TLS, on port 8765 by default. Environment:

| Variable | Value |
|---|---|
| `UPSTREAM_WEBHOOK_SECRET` | Secret used when creating the upstream webhook. |
| `FORK_DISPATCH_TOKEN` | Personal access token with `repo` scope on this fork. |
| `FORK_REPO` | `diamantmuqici-dotcom/AnyPS5` |
| `SYNC_WEBHOOK_PORT` | Listener port, default `8765`. |

Run:

```sh
python3 tools/webhook_upstream_sync.py
```

In `boykopovar/AnyPS5` repository settings, add a webhook pointing to `https://<host>/sync`, content type `application/json`, secret matching `UPSTREAM_WEBHOOK_SECRET`, and select the `push` event. The receiver ignores events that are not `push` on `refs/heads/main` and rejects requests with an invalid `X-Hub-Signature-256`.

The 15-minute schedule remains active as a fallback if the webhook path is down.

## Self-contained poller

`tools/poll_and_sync.py` needs no access to upstream repository settings. It polls the GitHub commits API for upstream `main`, and when the SHA differs from `fork/LAST_SYNC_UPSTREAM`, runs `tools/sync_upstream.ps1 -Push`. Run it on any machine with git, Python 3 and a configured GitHub credential:

```sh
set SYNC_WORKDIR=C:\temp\AnyPS5-push
set SYNC_POLL_SECONDS=60
python tools/poll_and_sync.py
```

| Variable | Default | Meaning |
|---|---|---|
| `UPSTREAM_REPO` | `boykopovar/AnyPS5` | Repository to watch. |
| `UPSTREAM_BRANCH` | `main` | Branch to watch. |
| `SYNC_POLL_SECONDS` | `60` | Poll interval in seconds. |
| `SYNC_WORKDIR` | current directory | Fork checkout. |
| `SYNC_SCRIPT` | `tools/sync_upstream.ps1` | Sync script path. |
| `SYNC_STATE_FILE` | `<workdir>/fork/LAST_SYNC_UPSTREAM` | Last mirrored SHA file. |

## Manual sync

From a checkout of this fork on Windows:

```powershell
python tools/fork_sync_fixups.py -h 2>$null
powershell -File tools/sync_upstream.ps1 -WorkDir C:\temp\AnyPS5-push
```

Add `-Push` to push the resulting commit to this fork's `main`. Without `-Push` the merge stays local.

## Conflict policy

Upstream content always wins on overlapping files. This preserves the exact upstream tree. Fork-only paths (`build-relinker/`, `fork/`, the sync tooling, this document) do not exist upstream, so a merge never deletes or overwrites them. The fork note in `README.md` and the mtime troubleshooting block in `docs/dev/BUILD.md` are re-applied idempotently after every merge.
