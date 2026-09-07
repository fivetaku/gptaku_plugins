#!/usr/bin/env python3
"""Exercise marketplace source boundaries through the real CLI in temporary Git repos.

Run: python3 tools/test_validate_marketplace.py -v
Only the standard library and Git are required; no installed state is accessed.
"""

import importlib.util
import json
import ntpath
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Final, final, override
from unittest.mock import patch

VALIDATOR: Final = Path(__file__).resolve().with_name("validate_marketplace.py")


@final
class MarketplaceSourceTests(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.temporary = tempfile.TemporaryDirectory(prefix="marketplace-source-")
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.root = self.home / "marketplace"
        self.plugin = self.root / "plugins/demo"
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith("GIT_")}
        self.env.update({
            "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.home / "config"),
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        })

    @override
    def setUp(self) -> None:
        self.root.mkdir()
        _ = self.git("init", "-b", "main")
        (self.root / "tools").mkdir()
        _ = shutil.copy2(VALIDATOR, self.root / "tools/validate_marketplace.py")
        (self.root / ".claude-plugin").mkdir()
        self.manifest(self.plugin)
        self.source("./plugins/demo")

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.root), *args], env=self.env,
            capture_output=True, text=True, timeout=20, check=True,
        )
        return result.stdout.strip()

    def manifest(self, directory: Path) -> None:
        metadata = directory / ".claude-plugin"
        metadata.mkdir(parents=True)
        _ = (metadata / "plugin.json").write_text(json.dumps({
            "name": "demo", "version": "1.0.0", "description": "Fixture",
            "author": {"name": "Fixture"}, "license": "MIT",
        }), encoding="utf-8")

    def source(self, value: str) -> None:
        _ = (self.root / ".claude-plugin/marketplace.json").write_text(json.dumps({
            "name": "fixture", "owner": {"name": "Fixture"},
            "plugins": [{"name": "demo", "source": value}],
        }), encoding="utf-8")

    def assert_cli_status(self, expected: int) -> None:
        result = subprocess.run(
            [sys.executable, str(self.root / "tools/validate_marketplace.py")],
            cwd=self.home, env=self.env, capture_output=True, text=True,
            timeout=20, check=False,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def test_listed_ignored_source_is_rejected(self) -> None:
        _ = (self.root / ".gitignore").write_text("/plugins/demo/\n", encoding="utf-8")
        self.assert_cli_status(1)

    def test_legitimate_local_sources_are_accepted(self) -> None:
        for source in ("./plugins/demo", "plugins/demo", "./plugins/demo/"):
            with self.subTest(source=source):
                self.source(source)
                self.assert_cli_status(0)

    def test_windows_manifest_paths_reach_native_filesystem_lookup(self) -> None:
        spec = importlib.util.spec_from_file_location("marketplace_windows_probe", VALIDATOR)
        assert spec is not None and spec.loader is not None
        validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator)
        for source in ("./plugins/demo", "plugins/demo", "./plugins/demo/"):
            with self.subTest(source=source), \
                    patch.object(validator, "ROOT", r"C:\repo"), \
                    patch.object(validator, "os", SimpleNamespace(path=ntpath)), \
                    patch.object(validator.subprocess, "run",
                                 return_value=subprocess.CompletedProcess([], 1, "", "")) as git_check, \
                    patch.object(ntpath, "isdir", return_value=False) as directory:
                # Only unavailable Windows filesystem/Git I/O is substituted.
                # The actual validator and stdlib Windows path semantics run.
                validator.validate_plugin_manifest("demo", source)
                directory.assert_called_once_with(r"C:\repo\plugins\demo")
                self.assertEqual(git_check.call_args.args[0][-1], "plugins/demo")

    def test_tracked_local_source_is_accepted(self) -> None:
        _ = self.git("add", "plugins/demo")
        self.assert_cli_status(0)

    def test_force_added_ignored_source_is_rejected(self) -> None:
        _ = (self.root / ".gitignore").write_text("/plugins/demo/\n", encoding="utf-8")
        _ = self.git("add", "-f", "plugins/demo")
        self.assertNotEqual(self.git("ls-files", "plugins/demo"), "")
        self.assert_cli_status(1)

    def test_ignore_negation_keeps_public_source_usable(self) -> None:
        _ = (self.root / ".gitignore").write_text(
            "/plugins/*\n!/plugins/demo/\n", encoding="utf-8")
        self.assert_cli_status(0)

    def test_nested_ignore_rule_is_enforced(self) -> None:
        _ = (self.root / "plugins/.gitignore").write_text("demo/\n", encoding="utf-8")
        self.assert_cli_status(1)

    def test_research_source_is_rejected_even_without_ignore_rule(self) -> None:
        self.manifest(self.root / "RESEARCH/demo")
        self.source("./RESEARCH/demo")
        self.assert_cli_status(1)

    def test_outside_relative_source_is_rejected(self) -> None:
        self.manifest(self.home / "outside")
        self.source("../outside")
        self.assert_cli_status(1)

    def test_absolute_sources_are_rejected_inside_and_outside_repository(self) -> None:
        outside = self.home / "outside"
        self.manifest(outside)
        for source in (self.plugin, outside):
            with self.subTest(source=source):
                self.source(str(source))
                self.assert_cli_status(1)

    def test_other_plugin_location_is_rejected(self) -> None:
        self.manifest(self.root / "plugins/other")
        self.source("./plugins/other")
        self.assert_cli_status(1)

    def test_parent_traversal_is_rejected(self) -> None:
        for source in ("./plugins/demo/../demo", "./plugins/../plugins/demo"):
            with self.subTest(source=source):
                self.source(source)
                self.assert_cli_status(1)

    def test_plugin_symlink_escape_is_rejected(self) -> None:
        for target in (self.root / "RESEARCH/demo", self.home / "outside",
                       self.root / "plugins/demo-copy"):
            with self.subTest(target=target):
                self.manifest(target)
                if self.plugin.is_symlink():
                    self.plugin.unlink()
                else:
                    shutil.rmtree(self.plugin)
                self.plugin.symlink_to(target, target_is_directory=True)
                self.assert_cli_status(1)

    def test_plugins_parent_symlink_escape_is_rejected(self) -> None:
        plugins = self.root / "plugins"
        outside = self.home / "outside-plugins"
        _ = plugins.rename(outside)
        plugins.symlink_to(outside, target_is_directory=True)
        self.assert_cli_status(1)

    def test_git_ignore_failure_is_rejected(self) -> None:
        shutil.rmtree(self.root / ".git")
        self.assert_cli_status(1)

    def test_existing_manifest_validation_remains_enforced(self) -> None:
        manifest = self.plugin / ".claude-plugin/plugin.json"
        _ = manifest.write_text(json.dumps({"name": "demo"}), encoding="utf-8")
        self.assert_cli_status(1)


if __name__ == "__main__":
    _ = unittest.main()
