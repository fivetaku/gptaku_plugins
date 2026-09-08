"""Dependency integration tests: isolated registry, real imports and CLI processes."""
import json
import os
import shutil
import site
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
# Keep installed Python dependencies available after HOME is isolated.
USER_SITE = site.getusersitepackages()


class CliPayload(TypedDict):
    job: dict[str, str | int]
    content: str
    state: str
    candidates: list[str]
    json_endpoints: int
    report_path: str


Installation = tuple[Path, Path, Path]


def install_search(root: Path, marker: str) -> Path:
    skill = root / "skills" / "insane-search"
    engine = skill / "engine"
    engine.mkdir(parents=True)
    _ = (engine / "__init__.py").write_text("from .transport import fetch\n", encoding="utf-8")
    _ = (engine / "transport.py").write_text(
        "from types import SimpleNamespace\n"
        + "def fetch(url, *, timeout, max_attempts, enable_playwright, enable_phase0, "
        + "enable_extraction, enable_retry, enable_markdown, enable_maincontent):\n"
        + "    assert timeout == 7 and max_attempts == 2\n"
        + "    assert not enable_playwright and enable_phase0 and enable_extraction\n"
        + "    assert enable_retry and not enable_markdown and not enable_maincontent\n"
        + f"    return SimpleNamespace(ok=True, content={marker!r}, final_url=url, "
        + "verdict='strong_ok', summary='', stop_reason='success')\n",
        encoding="utf-8",
    )
    return skill


@pytest.fixture
def installed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Installation:
    home = tmp_path / "home"
    cache = home / ".claude" / "plugins" / "cache" / "fixture"
    crawl_skill = cache / "insane-crawl" / "0.1.0" / "skills" / "insane-crawl"
    _ = shutil.copytree(SKILL_ROOT / "engine", crawl_skill / "engine", ignore=shutil.ignore_patterns("__pycache__"))
    search_install = cache / "insane-search" / "0.16.1"
    search_skill = install_search(search_install, "registered-body")
    # An unregistered higher version must never outrank installPath.
    _ = install_search(cache / "insane-search" / "99.0.0", "unregistered-body")
    registry = home / ".claude" / "plugins" / "installed_plugins.json"
    _ = registry.write_text(json.dumps({
        "version": 2,
        "plugins": {"insane-search@fixture": [{"scope": "user", "installPath": str(search_install)}]},
    }), encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join((str(crawl_skill), USER_SITE)))
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    monkeypatch.delenv("INSANE_SEARCH_SKILL_ROOT", raising=False)
    monkeypatch.delenv("INSANE_SEARCH_ENDPOINT_MINER", raising=False)
    return crawl_skill, search_skill, registry


def cli(crawl_skill: Path, state: Path, *args: str) -> CliPayload:
    completed = subprocess.run(
        [sys.executable, "-m", "engine", "--state-dir", str(state), *args],
        cwd=crawl_skill, env=os.environ.copy(), capture_output=True, text=True,
        timeout=60, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload: CliPayload = json.loads(completed.stdout)
    return payload


def fetched_body(crawl_skill: Path, state: Path) -> str:
    result = cli(crawl_skill, state, "crawl", "https://example.com/", "--ignore-robots",
                 "--max-pages", "1", "--timeout", "7", "--max-attempts-per-page", "2")
    assert result["job"]["state"] == "completed"
    assert result["job"]["processed_pages"] == 1
    page = cli(crawl_skill, state, "page", str(result["job"]["job_id"]), "1")
    return page["content"]


def test_registered_install_is_imported_and_called_by_crawl_cli(installed: Installation, tmp_path: Path) -> None:
    crawl_skill, _, _ = installed
    assert fetched_body(crawl_skill, tmp_path / "state") == "registered-body"


def test_skill_override_precedes_registry(installed: Installation, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    crawl_skill, _, _ = installed
    home = Path.home()
    override = install_search(home / "override", "override-body")
    monkeypatch.setenv("INSANE_SEARCH_SKILL_ROOT", "~/" + str(override.relative_to(home)))
    assert fetched_body(crawl_skill, tmp_path / "state") == "override-body"


def test_development_sibling_without_registry(installed: Installation, tmp_path: Path) -> None:
    crawl_skill, _, registry = installed
    registry.unlink()
    _ = install_search(crawl_skill.parents[2] / "insane-search", "sibling-body")
    assert fetched_body(crawl_skill, tmp_path / "state") == "sibling-body"


def install_miner(skill: Path) -> Path:
    script = skill / "scripts" / "endpoint_miner.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    _ = script.write_text(
        "import json, os, sys\nfrom pathlib import Path\n"
        + "assert sys.argv[2:] == ['--max-bundles', '0', '--max-probes', '0', '--timeout', '1']\n"
        + "report = Path(os.environ['HOME']) / 'miner-output.json'\n"
        + "report.write_text(json.dumps({'candidates': [sys.argv[1] + 'api'], "
        + "'probed': [{'url': sys.argv[1] + 'api', 'kind': 'json'}]}))\n"
        + "print('report:', report)\n",
        encoding="utf-8",
    )
    return script


def test_registered_optional_miner_runs_through_discover_cli(installed: Installation, tmp_path: Path) -> None:
    crawl_skill, search_skill, _ = installed
    _ = install_miner(search_skill)
    result = cli(crawl_skill, tmp_path / "state", "discover", "https://example.com/",
                 "--max-bundles", "0", "--max-probes", "0", "--timeout", "1")
    assert result["state"] == "probable"
    assert result["candidates"] == ["https://example.com/api"]
    assert result["json_endpoints"] == 1
    assert json.loads(Path(result["report_path"]).read_text(encoding="utf-8")) == {
        "candidates": ["https://example.com/api"],
        "probed": [{"url": "https://example.com/api", "kind": "json"}],
    }


@pytest.mark.parametrize("override", ["INSANE_SEARCH_ENDPOINT_MINER", "INSANE_SEARCH_SKILL_ROOT"])
def test_explicit_miner_override_precedes_registry(installed: Installation, tmp_path: Path,
                                                   monkeypatch: pytest.MonkeyPatch, override: str) -> None:
    crawl_skill, search_skill, _ = installed
    registered = install_miner(search_skill)
    _ = registered.write_text("raise AssertionError('registered miner must not run')\n", encoding="utf-8")
    skill = tmp_path / "override-skill"
    script = install_miner(skill)
    monkeypatch.setenv(override, str(script if override.endswith("ENDPOINT_MINER") else skill))
    result = cli(crawl_skill, tmp_path / "state", "discover", "https://example.com/",
                 "--max-bundles", "0", "--max-probes", "0", "--timeout", "1")
    assert result["state"] == "probable"


def test_registered_search_without_optional_miner_is_unavailable(installed: Installation, tmp_path: Path) -> None:
    crawl_skill, search_skill, _ = installed
    _ = install_miner(search_skill.parents[2] / "99.0.0" / "skills" / "insane-search")
    result = cli(crawl_skill, tmp_path / "state", "discover", "https://example.com/")
    assert result["state"] == "unavailable"
    assert result["candidates"] == []
    assert result["json_endpoints"] == 0
    assert not result["report_path"]


def test_registry_precedes_development_sibling(installed: Installation, tmp_path: Path) -> None:
    crawl_skill, _, _ = installed
    _ = install_search(crawl_skill.parents[2] / "insane-search", "sibling-body")
    assert fetched_body(crawl_skill, tmp_path / "state") == "registered-body"


@pytest.mark.parametrize("payload", ["{", "[]", '{"plugins": []}',
                                     '{"plugins": {"insane-search@fixture": [{}]}}'])
def test_invalid_registry_is_reported(installed: Installation, tmp_path: Path, payload: str) -> None:
    crawl_skill, _, registry = installed
    _ = registry.write_text(payload, encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "engine", "--state-dir", str(tmp_path / "state"),
         "discover", "https://example.com/"], cwd=crawl_skill, env=os.environ.copy(),
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert completed.returncode == 2
    assert str(registry) in completed.stderr
