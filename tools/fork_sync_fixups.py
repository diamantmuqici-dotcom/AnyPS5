from pathlib import Path

FORK_NOTE = (
    "> **Fork note:** This repository mirrors AnyPS5 for the "
    "`diamantmuqici-dotcom` account. It tracks upstream `boykopovar/AnyPS5` "
    "and includes a WinLibs GCC 15.2.0 relinker-only build under "
    "`build-relinker/` (Windows x86-64, `relinker.exe`). Title compatibility "
    "depends on the system PRX libraries implemented upstream; this fork does "
    "not add proprietary firmware, keys, or copyrighted binaries."
)

MTIME_MARKER = "manifest 'build.ninja' still dirty after 100 tries"
MTIME_BLOCK = """If Ninja fails with `manifest 'build.ninja' still dirty after 100 tries, perhaps system time is not set`, source files have modification times ahead of the system clock, typically from extracting an archive whose timestamps were preserved in a different time zone. Reset the timestamps of the checkout to the current time and configure in a new build directory:

```powershell
$now = Get-Date
Get-ChildItem -LiteralPath <checkout> -Recurse -Force -File | ForEach-Object { $_.LastWriteTime = $now; $_.CreationTime = $now }
```
"""


def apply_readme():
    path = Path("README.md")
    if not path.exists():
        return
    lines = [
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.startswith("> **Fork note:**")
    ]
    index = next((i for i, line in enumerate(lines) if line.startswith("**English**")), 0)
    lines.insert(index, FORK_NOTE)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def apply_build_doc():
    path = Path("docs/dev/BUILD.md")
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    if MTIME_MARKER in text:
        return
    marker = "If the build stops with `fatal error: opening dependency file"
    index = text.find(marker)
    if index == -1:
        return
    path.write_text(text[:index] + MTIME_BLOCK + "\n" + text[index:], encoding="utf-8")


apply_readme()
apply_build_doc()
print("fork customizations applied")
