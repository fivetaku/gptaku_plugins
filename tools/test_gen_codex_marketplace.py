#!/usr/bin/env python3
"""Offline tests for gen_codex_marketplace.py."""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location("gen", Path(__file__).resolve().parent / "gen_codex_marketplace.py")
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


def make_repo(ready):
    d = Path(tempfile.mkdtemp())
    (d / ".claude-plugin").mkdir()
    (d / "tools").mkdir()
    plugins = [
        {"name": "core", "source": "./plugins/core", "category": "development"},
        {"name": "alpha", "source": "./plugins/alpha", "category": "productivity"},
        {"name": "beta", "source": "./plugins/beta", "category": "research"},
    ]
    (d / ".claude-plugin/marketplace.json").write_text(json.dumps({"plugins": plugins}))
    (d / ".gitmodules").write_text(
        '[submodule "plugins/alpha"]\n\tpath = plugins/alpha\n\turl = https://github.com/x/alpha.git\n'
        '[submodule "plugins/beta"]\n\tpath = plugins/beta\n\turl = https://github.com/x/beta.git\n')
    for n, v in (("core", "0.2.5"), ("alpha", "1.0.0"), ("beta", "2.1.0")):
        p = d / "plugins" / n / ".claude-plugin"
        p.mkdir(parents=True)
        (p / "plugin.json").write_text(json.dumps({"name": n, "version": v}))
    (d / "tools/codex_ready.json").write_text(json.dumps({"plugins": ready}))
    return d


def run(d, argv, ls=lambda u, r: True):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = gen.main(argv, ls, d)
    return code, buf.getvalue()


class T(unittest.TestCase):
    def test_build_shape(self):
        d = make_repo(["alpha", "core"])
        data = gen.build(d)
        self.assertEqual(data["name"], "gptaku-plugins")
        self.assertEqual([p["name"] for p in data["plugins"]], ["alpha", "core"])
        a, c = data["plugins"]
        self.assertEqual(a["source"], {"source": "url", "url": "https://github.com/x/alpha.git", "ref": "v1.0.0"})
        self.assertEqual(c["source"], {"source": "git-subdir", "url": gen.PARENT_URL,
                                       "path": "plugins/core", "ref": "core--v0.2.5"})
        self.assertEqual(a["category"], "Productivity")
        self.assertEqual(c["category"], "Development")
        self.assertEqual(a["policy"], {"installation": "AVAILABLE", "authentication": "ON_INSTALL"})

    def test_check_passes(self):
        d = make_repo(["alpha", "core"])
        self.assertEqual(run(d, [])[0], 0)
        code, out = run(d, ["--check"])
        self.assertEqual(code, 0)
        self.assertIn("OK: 2 entries, all tags present", out)

    def test_check_missing_tag(self):
        d = make_repo(["alpha", "core"])
        run(d, [])
        code, out = run(d, ["--check"], lambda u, r: r != "v1.0.0")
        self.assertEqual(code, 1)
        self.assertIn("MISSING TAG alpha v1.0.0", out)

    def test_check_stale_or_missing_file(self):
        d = make_repo(["alpha"])
        code, out = run(d, ["--check"])
        self.assertEqual(code, 1)
        self.assertIn("missing", out)
        run(d, [])
        (d / "tools/codex_ready.json").write_text(json.dumps({"plugins": ["alpha", "beta"]}))
        code, out = run(d, ["--check"])
        self.assertEqual(code, 1)
        self.assertIn("beta", out)

    def test_unknown_name(self):
        d = make_repo(["nope"])
        code, out = run(d, [])
        self.assertEqual(code, 1)
        self.assertIn("nope", out)


if __name__ == "__main__":
    unittest.main()
