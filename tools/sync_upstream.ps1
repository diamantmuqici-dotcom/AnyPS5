param(
  [string]$WorkDir = (Get-Location).Path,
  [string]$Upstream = "https://github.com/boykopovar/AnyPS5.git",
  [string]$Branch = "main",
  [switch]$Push
)
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $WorkDir
if (-not (Test-Path -LiteralPath .git)) { throw "Not a git repository: $WorkDir" }
git remote add upstream $Upstream 2>$null
if ($LASTEXITCODE -ne 0) { git remote set-url upstream $Upstream }
git fetch upstream $Branch --no-tags
if (git merge-base --is-ancestor "upstream/$Branch" HEAD) { Write-Output "Already up to date"; exit 0 }
$sha = git rev-parse "upstream/$Branch"
git merge --no-commit --no-ff -X theirs "upstream/$Branch"
if ($LASTEXITCODE -ne 0) {
  $conflicts = git diff --name-only --diff-filter=U
  foreach ($path in $conflicts) {
    git checkout --theirs -- $path 2>$null
    if ($LASTEXITCODE -ne 0) { git rm -f -- $path 2>$null }
    git add -- $path 2>$null
  }
}
python tools/fork_sync_fixups.py
New-Item -ItemType Directory -Force -Path fork | Out-Null
Set-Content -LiteralPath fork/LAST_SYNC_UPSTREAM -Value $sha
git add -A
git -c core.safecrlf=false commit -m "sync: mirror upstream AnyPS5 at $sha"
if ($Push) { git push origin "HEAD:$Branch" }
Write-Output "Synced to $sha"
