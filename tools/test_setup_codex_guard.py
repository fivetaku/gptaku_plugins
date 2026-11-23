#!/usr/bin/env python3
"""Codex guard in setup.sh: no-op under Codex layout, unchanged under Claude layout.
All runs use a fake HOME and stubbed gh/claude; nothing real is touched."""
import hashlib, os, shutil, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ["dd", "ddiring", "tikeytaka"]
MODES = ["", "ask", "ask autoupdate", "star yes", "star no", "autoupdate yes", "autoupdate no"]


def snapshot(d):
    out = {}
    for p in sorted(Path(d).rglob("*")):
        if p.is_file():
            out[str(p.relative_to(d))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


class Base(unittest.TestCase):
    def setUp(self):
        self.T = Path(tempfile.mkdtemp(prefix="codexguard-"))
        self.addCleanup(shutil.rmtree, self.T, True)
        self.stubs = self.T / "stubs"
        self.stubs.mkdir()
        self.log = self.T / "stub.log"
        self.log.write_text("")
        for n in ("gh", "claude", "open", "osascript"):
            s = self.stubs / n
            s.write_text('#!/bin/sh\necho "%s $@" >> "%s"\nexit 0\n' % (n, self.log))
            s.chmod(0o755)

    def seed_home(self, home):
        c = home / ".claude"
        (c / "plugins").mkdir(parents=True)
        (c / "settings.json").write_text("{}\n")
        (c / "plugins" / "known_marketplaces.json").write_text(
            '{"gptaku-plugins": {"autoUpdate": false}}\n')
        (c / "plugins" / "installed_plugins.json").write_text('{"version":2,"plugins":{}}\n')

    def env(self, home):
        e = {"HOME": str(home), "PATH": "%s:/usr/bin:/bin:/usr/sbin:/sbin" % self.stubs,
             "CLAUDE_PLUGIN_ROOT": "x"}
        return e

    def run_setup(self, script, mode, home):
        r = subprocess.run(["bash", str(script)] + mode.split(), env=self.env(home),
                           capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
        return r


class CodexLayout(Base):
    def test_noop(self):
        for p in PLUGINS:
            for mode in MODES:
                with self.subTest(plugin=p, mode=mode):
                    base = self.T / ("c_%s_%s" % (p, mode.replace(" ", "_")))
                    home = base / "home"
                    self.seed_home(home)
                    ch = base / "codexhome"
                    ch.mkdir(parents=True)
                    (ch / "config.toml").write_text("")
                    dst = ch / "plugins/cache/gptaku-plugins" / p / "9.9.9"
                    dst.mkdir(parents=True)
                    shutil.copytree(ROOT / "plugins" / p / "setup", dst / "setup")
                    before = snapshot(home)
                    self.log.write_text("")
                    r = self.run_setup(dst / "setup/setup.sh", mode, home)
                    self.assertEqual(r.returncode, 0)
                    self.assertEqual(r.stdout + r.stderr, "")
                    self.assertEqual(snapshot(home), before)
                    self.assertEqual(self.log.read_text(), "")


class ClaudeLayout(Base):
    def layout(self, tag, p, script_text=None):
        home = self.T / tag / "home"
        self.seed_home(home)
        dst = home / ".claude/plugins/cache/gptaku-plugins" / p / "9.9.9"
        dst.mkdir(parents=True)
        shutil.copytree(ROOT / "plugins" / p / "setup", dst / "setup")
        if script_text is not None:
            (dst / "setup/setup.sh").write_text(script_text)
        return home, dst / "setup/setup.sh"

    def test_same_as_original(self):
        for p in PLUGINS:
            with self.subTest(plugin=p):
                # plugins are submodules: origin/main stores only a gitlink sha, so read the
                # pre-guard script from that commit inside the submodule.
                ls = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "origin/main", "plugins/%s" % p],
                                    capture_output=True, text=True, check=True).stdout.split()
                orig = subprocess.run(
                    ["git", "-C", str(ROOT / "plugins" / p), "show", "%s:setup/setup.sh" % ls[2]],
                    capture_output=True, text=True, check=True).stdout
                h1, s1 = self.layout("old_" + p, p, orig)
                h2, s2 = self.layout("new_" + p, p)
                a = self.run_setup(s1, "ask autoupdate", h1)
                b = self.run_setup(s2, "ask autoupdate", h2)
                self.assertEqual((a.returncode, a.stdout, a.stderr), (b.returncode, b.stdout, b.stderr))
                if p == "dd":
                    lines = b.stdout.splitlines()
                    self.assertTrue(any(l.startswith("STAR_ASK") for l in lines), b.stdout)
                    self.assertTrue(any(l.startswith("AUTOUPDATE_ASK") for l in lines), b.stdout)


if __name__ == "__main__":
    unittest.main()
