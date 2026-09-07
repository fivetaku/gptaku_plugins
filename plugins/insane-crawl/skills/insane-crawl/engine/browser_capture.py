"""Stealth browser capture, evidence receipt, and cookie-to-HTTP handoff."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TypedDict, cast
from urllib.parse import urlsplit


@dataclass(frozen=True, slots=True)
class CookieRecord:
    name: str
    value: str
    domain: str
    path: str
    secure: bool
    http_only: bool


@dataclass(frozen=True, slots=True)
class NetworkRecord:
    status: int
    resource_type: str
    url: str
    content_type: str


@dataclass(frozen=True, slots=True)
class BrowserCaptureResult:
    ok: bool
    final_url: str
    title: str
    html: str
    cookies: tuple[CookieRecord, ...]
    network: tuple[NetworkRecord, ...]
    replay_ok: bool
    replay_status: int
    replay_bytes: int
    error: str


class CaptureCookie(TypedDict):
    name: str
    value: str
    domain: str
    path: str
    secure: bool
    http_only: bool


class CaptureNetwork(TypedDict):
    status: int
    resource_type: str
    url: str
    content_type: str


class CapturePayload(TypedDict):
    ok: bool
    final_url: str
    title: str
    html: str
    cookies: list[CaptureCookie]
    network: list[CaptureNetwork]
    replay_ok: bool
    replay_status: int
    replay_bytes: int
    error: str


def capture_page(url: str, *, timeout: int, receipt_dir: Path | None) -> BrowserCaptureResult:
    """Capture one rendered page with the pinned local CloakBrowser runtime."""
    runtime = find_runtime()
    if runtime is None:
        return BrowserCaptureResult(False, url, "", "", (), (), False, 0, 0, "cloak runtime not found")
    work_dir = receipt_dir or Path(os.environ.get("TMPDIR", "/tmp")) / "insane-crawl-browser"
    work_dir.mkdir(parents=True, exist_ok=True)
    output = work_dir / "browser-capture.json"
    completed = subprocess.run(
        [str(runtime), "-m", "engine.browser_worker", url, str(output), str(max(5, timeout))],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=max(30, timeout * 4),
        check=False,
    )
    if completed.returncode != 0 or not output.exists():
        error = (completed.stderr or completed.stdout or f"browser exit {completed.returncode}").strip()
        return BrowserCaptureResult(False, url, "", "", (), (), False, 0, 0, error[-2000:])
    payload = json.loads(output.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("browser capture payload must be an object")
    result = _parse_capture(cast(CapturePayload, cast(object, payload)))
    if receipt_dir is not None:
        write_receipt(result, receipt_dir / "browser-receipt.json")
    return result


def find_runtime() -> Path | None:
    override = os.environ.get("INSANE_CRAWL_CLOAK_PYTHON", "").strip()
    candidates = [Path(override).expanduser()] if override else []
    candidates.append(Path.home() / ".local" / "share" / "insane-crawl" / "cloak-venv" / "bin" / "python")
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def write_receipt(result: BrowserCaptureResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    endpoint_candidates = [asdict(item) for item in rank_endpoint_candidates(result.network)]
    payload = {
        "capture": {
            "ok": result.ok,
            "final_url": result.final_url,
            "title": result.title,
            "html_bytes": len(result.html.encode("utf-8", "surrogatepass")),
            "cookie_count": len(result.cookies),
            "network_count": len(result.network),
            "replay_ok": result.replay_ok,
            "replay_status": result.replay_status,
            "replay_bytes": result.replay_bytes,
            "error": result.error,
        },
        "cookies": [
            {
                "name": item.name,
                "domain": item.domain,
                "path": item.path,
                "secure": item.secure,
                "http_only": item.http_only,
            }
            for item in result.cookies
        ],
        "network": [asdict(item) for item in result.network],
        "endpoint_candidates": endpoint_candidates,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def rank_endpoint_candidates(network: tuple[NetworkRecord, ...]) -> tuple[NetworkRecord, ...]:
    """Rank content-shaped requests while demoting telemetry and challenge traffic."""
    scored: list[tuple[int, NetworkRecord]] = []
    for item in network:
        lowered = item.url.lower()
        if item.resource_type not in {"xhr", "fetch"} and "json" not in item.content_type.lower():
            continue
        penalties = sum(
            token in lowered
            for token in ("pixel", "submit", "analytics", "beacon", "tracking", "challenge", "captcha")
        )
        hints = sum(
            token in lowered
            for token in ("/api/", "graphql", "search", "product", "detail", "article", "item", "list")
        )
        score = hints * 3 - penalties * 4 + ("json" in item.content_type.lower()) * 2
        score += item.status == 200
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1].url))
    return tuple(item for _, item in scored[:100])


def authority(url: str) -> str:
    parsed = urlsplit(url)
    return (parsed.hostname or "unknown").lower()


def _parse_capture(payload: CapturePayload) -> BrowserCaptureResult:
    raw_cookies = payload["cookies"]
    raw_network = payload["network"]
    cookies = tuple(
        CookieRecord(
            name=str(item.get("name", "")),
            value=str(item.get("value", "")),
            domain=str(item.get("domain", "")),
            path=str(item.get("path", "/")),
            secure=bool(item.get("secure", False)),
            http_only=bool(item.get("http_only", False)),
        )
        for item in raw_cookies
    )
    network = tuple(
        NetworkRecord(
            status=int(item.get("status", 0)),
            resource_type=str(item.get("resource_type", "")),
            url=str(item.get("url", "")),
            content_type=str(item.get("content_type", "")),
        )
        for item in raw_network
    )
    return BrowserCaptureResult(
        ok=payload["ok"],
        final_url=payload["final_url"],
        title=payload["title"],
        html=payload["html"],
        cookies=cookies,
        network=network,
        replay_ok=payload["replay_ok"],
        replay_status=payload["replay_status"],
        replay_bytes=payload["replay_bytes"],
        error=payload["error"],
    )
