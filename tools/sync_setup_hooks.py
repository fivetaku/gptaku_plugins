#!/usr/bin/env python3
"""Render shared/update-hook/setup.sh.template into every plugin's setup/setup.sh
and copy the canonical gptaku-update-check.cjs next to it.

Per-plugin values (PLUGIN, OWN_REPO) are read from the plugin's existing
setup/setup.sh, so the existing file is the only per-plugin input.

Safety: before overwriting, every non-comment line of the existing setup.sh must
also appear in the rendered output. If the existing file carries logic the
template does not have, that plugin is NOT written and is reported as
"custom-logic" (exit 1) -- logic is never dropped silently. Plugins whose custom
logic is known and tracked can be listed in HOLD with a reason; they are left
untouched and reported, but do not fail --check.

Usage:
  python3 tools/sync_setup_hooks.py            # write
  python3 tools/sync_setup_hooks.py --check    # exit 1 if anything is out of sync
  python3 tools/sync_setup_hooks.py --plugins dd gaseo
"""
from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "shared" / "update-hook"
TEMPLATE = SHARED / "setup.sh.template"
CJS = SHARED / "gptaku-update-check.cjs"
PLUGINS = ROOT / "plugins"

# Plugins whose setup.sh has extra, plugin-specific logic beyond the template.
# They are skipped (both files) until the template grows an extension point.
HOLD = {
    "ddiring": "first-run doctor.sh self-check (FIRST_RUN + DDIRING_DOCTOR) not in template",
    "tikeytaka": "write_project_memory() per-project memory note not in template",
}

VARS = ("PLUGIN", "OWN_REPO")


def read_vars(text: str) -> dict[str, str]:
    out = {}
    for name in VARS:
        m = re.search(r'^%s="([^"\n]*)"' % name, text, re.M)
        if not m:
            raise ValueError("%s=\"...\" not found" % name)
        out[name] = m.group(1)
    return out


def render(template: str, values: dict[str, str]) -> str:
    out = template
    for name, val in values.items():
        out = out.replace("__%s__" % name, val)
    left = sorted(set(re.findall(r"__[A-Z_]+__", out)))
    if left:
        raise ValueError("unrendered placeholders: %s" % ", ".join(left))
    return out


def is_code(line: str) -> bool:
    s = line.strip()
    return bool(s) and not s.startswith("#") and not s.startswith("//")


def custom_lines(existing: str, rendered: str) -> list[str]:
    have = {l.strip() for l in rendered.splitlines()}
    return [l for l in existing.splitlines() if is_code(l) and l.strip() not in have]


def write_atomic(path: Path, data: bytes, mode: int) -> None:
    fd, tmp = tempfile.mkstemp(prefix=".%s." % path.name, suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def stat_diff(old: str, new: str) -> str:
    add = rem = 0
    for l in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0):
        if l.startswith("+") and not l.startswith("+++"):
            add += 1
        elif l.startswith("-") and not l.startswith("---"):
            rem += 1
    return "+%d -%d" % (add, rem)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="do not write; exit 1 if out of sync")
    ap.add_argument("--plugins", nargs="*", help="limit to these plugin names")
    args = ap.parse_args()

    template = TEMPLATE.read_text(encoding="utf-8")
    cjs = CJS.read_bytes()
    targets = sorted(p.parent.parent for p in PLUGINS.glob("*/setup/setup.sh"))
    if args.plugins:
        want = set(args.plugins)
        missing = want - {t.name for t in targets}
        if missing:
            print("unknown plugin(s): %s" % ", ".join(sorted(missing)), file=sys.stderr)
            return 2
        targets = [t for t in targets if t.name in want]

    failed = False
    counts: dict[str, int] = {}
    for plug in targets:
        name = plug.name
        sh = plug / "setup" / "setup.sh"
        cj = plug / "setup" / "gptaku-update-check.cjs"
        if name in HOLD:
            status, detail = "held", HOLD[name]
        else:
            existing = sh.read_text(encoding="utf-8")
            try:
                rendered = render(template, read_vars(existing))
            except ValueError as e:
                status, detail = "error", str(e)
                failed = True
            else:
                extra = custom_lines(existing, rendered)
                if extra:
                    status = "custom-logic"
                    detail = "existing setup.sh has %d line(s) not in template, not written:\n%s" % (
                        len(extra), "\n".join("      | " + l for l in extra[:20]))
                    failed = True
                else:
                    sh_ok = existing == rendered
                    cj_ok = cj.exists() and cj.read_bytes() == cjs
                    if sh_ok and cj_ok:
                        status, detail = "in-sync", ""
                    else:
                        parts = []
                        if not sh_ok:
                            parts.append("setup.sh %s" % stat_diff(existing, rendered))
                        if not cj_ok:
                            parts.append("gptaku-update-check.cjs differs")
                        detail = ", ".join(parts)
                        if args.check:
                            status = "out-of-sync"
                            failed = True
                        else:
                            mode = sh.stat().st_mode & 0o777
                            if not sh_ok:
                                write_atomic(sh, rendered.encode("utf-8"), mode)
                            if not cj_ok:
                                cmode = cj.stat().st_mode & 0o777 if cj.exists() else 0o644
                                write_atomic(cj, cjs, cmode)
                            status = "updated"
        counts[status] = counts.get(status, 0) + 1
        print("%-16s %-13s %s" % (name, status, detail))

    print("\nsummary: " + ", ".join("%s=%d" % kv for kv in sorted(counts.items())))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
