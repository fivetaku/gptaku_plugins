#!/usr/bin/env python3
"""Generate .agents/plugins/marketplace.json (Codex) from the Claude marketplace.

Codex never fetches git submodules, so every entry points straight at the
plugin's own repo and release tag.

Usage:
  python3 tools/gen_codex_marketplace.py            # write
  python3 tools/gen_codex_marketplace.py --check    # exit 1 if stale or a tag is missing
"""
from __future__ import annotations

import difflib
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARENT_URL = "https://github.com/fivetaku/gptaku_plugins.git"
OUT_REL = Path(".agents/plugins/marketplace.json")


class GenError(Exception):
    pass


def _submodule_urls(root: Path) -> dict[str, str]:
    path = root / ".gitmodules"
    urls: dict[str, str] = {}
    if not path.exists():
        return urls
    cur = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        m = re.match(r'\[submodule "(.+)"\]', line)
        if m:
            cur = {"name": m.group(1)}
            continue
        if cur is not None and "=" in line:
            k, v = [s.strip() for s in line.split("=", 1)]
            cur[k] = v
            if k == "url":
                urls[cur.get("path", cur["name"])] = v
    return urls


def build(root: Path) -> dict:
    claude = json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    by_name = {p["name"]: p for p in claude.get("plugins", [])}
    ready = json.loads((root / "tools" / "codex_ready.json").read_text(encoding="utf-8"))["plugins"]
    subs = _submodule_urls(root)
    entries = []
    for name in ready:
        if name not in by_name:
            raise GenError(f"{name}: in codex_ready.json but not in Claude marketplace")
        src = by_name[name].get("source", f"./plugins/{name}")
        rel = src[2:] if src.startswith("./") else src
        pj = root / rel / ".claude-plugin" / "plugin.json"
        if not pj.exists():
            raise GenError(f"{name}: missing {pj}")
        ver = json.loads(pj.read_text(encoding="utf-8")).get("version")
        if not ver:
            raise GenError(f"{name}: no version in {pj}")
        if rel in subs:
            source = {"source": "url", "url": subs[rel], "ref": f"v{ver}"}
        else:
            source = {"source": "git-subdir", "url": PARENT_URL, "path": rel, "ref": f"{name}--v{ver}"}
        entries.append({
            "name": name,
            "source": source,
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": str(by_name[name].get("category", "productivity")).capitalize(),
        })
    return {"name": "gptaku-plugins", "interface": {"displayName": "GPTaku plugins"}, "plugins": entries}


def render(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def default_ls_remote(url: str, ref: str) -> bool:
    try:
        r = subprocess.run(["git", "ls-remote", "--tags", url, f"refs/tags/{ref}"],
                           capture_output=True, text=True, timeout=30)
    except (subprocess.TimeoutExpired, OSError):
        return False
    return r.returncode == 0 and bool(r.stdout.strip())


def check(root: Path, ls_remote=default_ls_remote) -> tuple[int, list[str]]:
    data = build(root)
    want = render(data)
    out = root / OUT_REL
    lines: list[str] = []
    code = 0
    have = out.read_text(encoding="utf-8") if out.exists() else None
    if have != want:
        code = 1
        lines.append(f"STALE: {OUT_REL} " + ("missing" if have is None else "differs from generated"))
        lines.extend(l.rstrip("\n") for l in difflib.unified_diff(
            (have or "").splitlines(True), want.splitlines(True),
            fromfile=str(OUT_REL), tofile="generated"))
    entries = data["plugins"]
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(lambda e: ls_remote(e["source"]["url"], e["source"]["ref"]), entries))
    missing = 0
    for e, ok in zip(entries, results):
        if not ok:
            missing += 1
            lines.append(f"MISSING TAG {e['name']} {e['source']['ref']}")
    if missing:
        code = 1
    if code == 0:
        lines.append(f"OK: {len(entries)} entries, all tags present")
    return code, lines


def main(argv: list[str], ls_remote=default_ls_remote, root: Path = ROOT) -> int:
    try:
        if "--check" in argv:
            code, lines = check(root, ls_remote)
            print("\n".join(lines))
            return code
        data = build(root)
        out = root / OUT_REL
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(data), encoding="utf-8")
        print(f"wrote {OUT_REL} ({len(data['plugins'])} entries)")
        return 0
    except (GenError, FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
