"""Adapter for the local insane-search endpoint discovery implementation."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast
from urllib.parse import urlsplit

from .models import DiscoveryResult
from .search_dependency import search_skill_roots


class ProbeResult(TypedDict, total=False):
    url: str
    kind: str
    bytes: int


class MinerReport(TypedDict, total=False):
    candidates: list[str]
    probed: list[ProbeResult]


def discover(
    url: str,
    *,
    state_root: Path,
    max_bundles: int = 8,
    max_probes: int = 20,
    timeout: int = 15,
) -> DiscoveryResult:
    """Run insane-search's local endpoint miner and normalize its report."""
    script = find_endpoint_miner()
    if script is None:
        return DiscoveryResult(
            state="unavailable",
            candidates=(),
            reason=(
                "local insane-search endpoint_miner.py was not found; current insane-search "
                "releases do not include this optional script. Set INSANE_SEARCH_ENDPOINT_MINER "
                "to a compatible local endpoint_miner.py if available, or use crawl/fetch without discovery."
            ),
        )
    env = os.environ.copy()
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            url,
            "--max-bundles",
            str(max(0, max_bundles)),
            "--max-probes",
            str(max(0, max_probes)),
            "--timeout",
            str(max(1, timeout)),
        ],
        cwd=script.parents[1],
        env=env,
        capture_output=True,
        text=True,
        timeout=max(5, timeout * (max_probes + max_bundles + 2)),
        check=False,
    )
    source_report = _report_path(completed.stdout)
    if source_report is None or not source_report.exists():
        reason = (completed.stderr or completed.stdout or f"miner exit {completed.returncode}").strip()
        return DiscoveryResult(state="unavailable", candidates=(), reason=reason[-1000:])
    report = _load_report(source_report)
    report_path = _persist_report(report, state_root, url)
    candidates = tuple(str(item) for item in report.get("candidates", []))
    json_hits = [
        item for item in report.get("probed", []) if item.get("kind") == "json"
    ]
    state = "probable" if json_hits else "candidate"
    reason = (
        "GET JSON candidates were replayed by the local insane-search miner; "
        "page-render attribution is still required before proven fast-path use."
        if json_hits
        else "Candidates were mined from fetched page and bundle text; no replayed JSON endpoint was found."
    )
    return DiscoveryResult(
        state=state,
        candidates=candidates,
        reason=reason,
        report_path=str(report_path),
        json_endpoints=len(json_hits),
    )


def find_endpoint_miner() -> Path | None:
    """Prefer explicit and installed local insane-search copies."""
    override = os.environ.get("INSANE_SEARCH_ENDPOINT_MINER", "").strip()
    if override:
        script = Path(override).expanduser().resolve()
        if script.is_file():
            return script
    for root in search_skill_roots():
        script = root / "scripts" / "endpoint_miner.py"
        if script.is_file():
            return script
    home = Path.home()
    candidates = sorted(
        home.glob(
            ".claude/plugins/marketplaces/*/plugins/insane-search/skills/insane-search/scripts/endpoint_miner.py"
        ),
        reverse=True,
    )
    candidates.append(
        home
        / "insane_plugins"
        / "plugins"
        / "insane-search"
        / "skills"
        / "insane-search"
        / "scripts"
        / "endpoint_miner.py"
    )
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def _report_path(stdout: str) -> Path | None:
    for line in reversed(stdout.splitlines()):
        if line.startswith("report:"):
            return Path(line.split(":", 1)[1].strip())
    return None


def _load_report(path: Path) -> MinerReport:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("endpoint miner report must be an object")
    return cast(MinerReport, cast(object, payload))


def _persist_report(report: MinerReport, state_root: Path, url: str) -> Path:
    host = (urlsplit(url).hostname or "unknown").lower()
    destination = state_root / "discovery" / host / "miner-report.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return destination
