#!/usr/bin/env python3
"""Exercise the release helper with real Git repositories, never real installs.

Run: python3 tools/test_plugin_release.py -v
Only the standard library and the helper's Git/Bash/Python prerequisites are used.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Final, final, override

SCRIPT: Final = Path(__file__).resolve().parents[1] / "scripts/plugin-release.sh"


@final
class PluginReleaseTests(unittest.TestCase):
    """Each test owns disposable parent, plugin, HOME, and remote repositories."""

    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.temporary = tempfile.TemporaryDirectory(prefix="plugin-release-")
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.root = self.home / "gptaku_plugins"
        self.plugin = self.root / "plugins/demo"
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith("GIT_")}
        self.env.update({
            "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.home / "config"),
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0", "GIT_EDITOR": "true",
            "GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.test",
            "GIT_COMMITTER_NAME": "Fixture",
            "GIT_COMMITTER_EMAIL": "fixture@example.test",
        })

    @override
    def setUp(self) -> None:
        _ = self.git(self.home, "init", "-b", "main", str(self.root))
        _ = self.git(self.home, "init", "-b", "main", str(self.plugin))
        (self.plugin / ".claude-plugin").mkdir()
        self.manifest("1.0.0")
        _ = (self.plugin / "CHANGELOG.md").write_text("## 1.0.0\n", encoding="utf-8")
        _ = self.git(self.plugin, "add", ".")
        _ = self.git(self.plugin, "commit", "-m", "base plugin")
        _ = self.git(self.root, "-c", "protocol.file.allow=always", "submodule", "add",
                     str(self.plugin), "plugins/demo")
        _ = self.git(self.root, "submodule", "absorbgitdirs")
        _ = (self.root / "unrelated.txt").write_text("original\n", encoding="utf-8")
        (self.root / "scripts").mkdir()
        _ = shutil.copy2(SCRIPT, self.root / "scripts/plugin-release.sh")
        _ = self.git(self.root, "add", ".")
        _ = self.git(self.root, "commit", "-m", "base parent")
        _ = self.git(self.plugin, "checkout", "-b", "feature")
        self.manifest("2.0.0")
        _ = self.git(self.plugin, "add", ".")
        _ = self.git(self.plugin, "commit", "-m", "new version")
        _ = self.git(self.plugin, "checkout", "main")

    @property
    def feature(self) -> str:
        return self.git(self.plugin, "rev-parse", "refs/heads/feature")

    def git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(["git", "-C", str(repo), *args], env=self.env,
                                capture_output=True, text=True, timeout=20, check=True)
        return result.stdout.strip()

    def manifest(self, version: str) -> None:
        _ = (self.plugin / ".claude-plugin/plugin.json").write_text(
            json.dumps({"name": "demo", "version": version}), encoding="utf-8")

    def release(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(self.root / "scripts/plugin-release.sh"), *args],
            cwd=self.home, env=self.env, capture_output=True, text=True, timeout=30,
            check=False,
        )

    def state(self) -> tuple[str, ...]:
        """Capture refs, branch, index, and working changes on both sides."""
        return tuple(self.git(repo, *args) for repo in (self.root, self.plugin)
                     for args in (("show-ref",), ("rev-parse", "HEAD"),
                                  ("rev-parse", "--abbrev-ref", "HEAD"),
                                  ("status", "--porcelain", "--untracked-files=all"),
                                  ("diff", "--cached", "--binary"),
                                  ("diff", "--binary")))

    def assert_refused_unchanged(self, *args: str) -> None:
        before = self.state()
        result = self.release(*args)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.state(), before, result.stdout + result.stderr)

    def test_refuses_unrelated_staged_parent_change_before_plugin_mutation(self) -> None:
        # Given: unrelated user work is already staged in the parent.
        _ = (self.root / "unrelated.txt").write_text("private staged work\n", encoding="utf-8")
        _ = self.git(self.root, "add", "unrelated.txt")
        before = self.state()
        # When: the real helper is invoked without pushing.
        result = self.release("demo", "feature")
        # Then: no commit, branch switch, merge, or index change is permitted.
        committed = self.git(self.root, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD")
        self.assertNotEqual(result.returncode, 0,
                            f"unsafe helper succeeded; parent commit paths: {committed}\n"
                            + result.stdout + result.stderr)
        self.assertEqual(self.state(), before)

    def test_refuses_staged_plugin_pointer(self) -> None:
        _ = self.git(self.plugin, "checkout", "feature")
        _ = self.git(self.root, "add", "plugins/demo")
        self.assert_refused_unchanged("demo", "feature")

    def test_refuses_wrong_parent_branch(self) -> None:
        _ = self.git(self.root, "checkout", "-b", "unrelated")
        self.assert_refused_unchanged("demo", "feature")

    def test_refuses_detached_parent(self) -> None:
        _ = self.git(self.root, "checkout", "--detach")
        self.assert_refused_unchanged("demo", "feature", "--push")

    def test_refuses_pending_parent_merge_with_clean_index(self) -> None:
        _ = self.git(self.root, "checkout", "-b", "pending")
        _ = self.git(self.root, "commit", "--allow-empty", "-m", "pending parent")
        _ = self.git(self.root, "checkout", "main")
        _ = self.git(self.root, "merge", "--no-ff", "--no-commit", "pending")
        self.assertEqual(self.git(self.root, "diff", "--cached"), "")
        self.assert_refused_unchanged("demo", "feature")

    def test_refuses_wrong_plugin_branch(self) -> None:
        _ = self.git(self.plugin, "checkout", "-b", "unrelated")
        self.assert_refused_unchanged("demo", "feature")

    def test_refuses_detached_plugin(self) -> None:
        _ = self.git(self.plugin, "checkout", "--detach")
        self.assert_refused_unchanged("demo", "feature")

    def test_refuses_missing_main(self) -> None:
        _ = self.git(self.plugin, "checkout", "feature")
        _ = self.git(self.plugin, "branch", "-D", "main")
        self.assert_refused_unchanged("demo", "feature")

    def test_refuses_missing_source_branch(self) -> None:
        self.assert_refused_unchanged("demo", "absent")

    def test_refuses_commit_instead_of_source_branch(self) -> None:
        self.assert_refused_unchanged("demo", self.feature)

    def test_refuses_dirty_plugin(self) -> None:
        _ = (self.plugin / "untracked.txt").write_text("work\n", encoding="utf-8")
        self.assert_refused_unchanged("demo", "feature")

    def test_refuses_invalid_arguments(self) -> None:
        for args in ((), ("demo",), ("demo", "feature", "--typo"),
                     ("demo", "feature", "--push", "extra"), ("../plugins/demo", "feature")):
            with self.subTest(args=args):
                self.assert_refused_unchanged(*args)

    def test_happy_path_uses_script_root_and_merged_version(self) -> None:
        # Given: HOME differs from the script location, and unrelated work is unstaged.
        other_home = self.home / "other-home"
        other_home.mkdir()
        self.env["HOME"] = str(other_home)
        _ = (self.root / "unrelated.txt").write_text("unstaged work\n", encoding="utf-8")
        # When: merge feature (2.0.0) while the checked-out manifest is 1.0.0.
        result = self.release("demo", "feature")
        # Then: only the gitlink is committed; no tags or installation state is created.
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        merged = self.git(self.plugin, "rev-parse", "HEAD")
        self.assertEqual(self.git(self.root, "rev-parse", "HEAD:plugins/demo"), merged)
        self.assertEqual(self.git(self.plugin, "rev-parse", "HEAD^2"), self.feature)
        self.assertEqual(self.git(self.plugin, "branch", "--show-current"), "main")
        self.assertEqual(self.git(self.root, "diff-tree", "--no-commit-id", "--name-only",
                                  "-r", "HEAD"), "plugins/demo")
        self.assertEqual(self.git(self.root, "show", "HEAD:unrelated.txt"), "original")
        self.assertEqual((self.root / "unrelated.txt").read_text(encoding="utf-8"), "unstaged work\n")
        self.assertEqual(json.loads(self.git(self.plugin, "show", "HEAD:.claude-plugin/plugin.json"))
                         ["version"], "2.0.0")
        self.assertEqual(self.git(self.root, "tag"), "")
        self.assertEqual(self.git(self.plugin, "tag"), "")
        self.assertEqual(list(other_home.iterdir()), [])

    def test_happy_path_from_source_branch(self) -> None:
        _ = self.git(self.plugin, "checkout", "feature")
        result = self.release("demo", "feature")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git(self.plugin, "rev-parse", "HEAD^2"), self.feature)

    def test_already_merged_pointer_is_a_no_op(self) -> None:
        _ = self.git(self.plugin, "merge", "--no-ff", "feature", "-m", "fixture merge")
        _ = self.git(self.root, "add", "plugins/demo")
        _ = self.git(self.root, "commit", "-m", "fixture pointer")
        before = self.state()
        result = self.release("demo", "feature")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.state(), before)

    def test_refuses_invalid_version_from_merge_result(self) -> None:
        # Given: checked-out main is valid; only the incoming manifest is invalid.
        _ = self.git(self.plugin, "checkout", "feature")
        self.manifest("not-a-version")
        _ = self.git(self.plugin, "add", ".")
        _ = self.git(self.plugin, "commit", "-m", "invalid version")
        _ = self.git(self.plugin, "checkout", "main")
        parent_head = self.git(self.root, "rev-parse", "HEAD")
        plugin_head = self.git(self.plugin, "rev-parse", "HEAD")
        # When: merge validation sees the actual incoming version.
        result = self.release("demo", "feature")
        # Then: neither repository gains a commit or tag.
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git(self.root, "rev-parse", "HEAD"), parent_head)
        self.assertEqual(self.git(self.plugin, "rev-parse", "HEAD"), plugin_head)
        self.assertEqual(self.git(self.root, "diff", "--cached"), "")

    def test_pushes_only_to_disposable_local_remotes(self) -> None:
        remotes = (self.home / "parent.git", self.home / "plugin.git")
        for repo, remote in zip((self.root, self.plugin), remotes):
            _ = self.git(self.home, "init", "--bare", str(remote))
            _ = self.git(repo, "remote", "add", "origin", str(remote))
        result = self.release("demo", "feature", "--push")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for repo, remote in zip((self.root, self.plugin), remotes):
            self.assertEqual(self.git(remote, "rev-parse", "refs/heads/main"),
                             self.git(repo, "rev-parse", "HEAD"))
            self.assertEqual(self.git(remote, "tag"), "")


if __name__ == "__main__":
    _ = unittest.main()
