"""Bounded single-page fetch contract used by the crawl coordinator."""
from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol, runtime_checkable
from urllib.parse import urlsplit

from .browser_capture import capture_page, write_receipt
from .search_dependency import search_skill_roots
from .urls import extract_links


class SearchAttempt(Protocol):
    status: int


class SearchFetchResult(Protocol):
    ok: bool
    content: str
    final_url: str
    verdict: str
    summary: str
    stop_reason: str



@runtime_checkable
class SearchFetch(Protocol):
    def __call__(
        self,
        url: str,
        *,
        timeout: int,
        max_attempts: int,
        enable_playwright: bool,
        enable_phase0: bool,
        enable_extraction: bool,
        enable_retry: bool,
        enable_markdown: bool,
        enable_maincontent: bool,
    ) -> SearchFetchResult: ...


BACKPRESSURE_STATUSES: Final = frozenset({429, 503})


@dataclass(frozen=True, slots=True)
class FetchPageResult:
    ok: bool
    requested_url: str
    final_url: str
    verdict: str
    content: str
    links: tuple[str, ...]
    error: str
    receipt_path: str = ""
    backpressure_status: int = 0


def _backpressure_status(result: object) -> int:
    """Return reported backpressure on an unsuccessful fetch, or 0.

    A crawler that paces itself but ignores 429/503 is not being polite; the
    server has explicitly asked for more room and that request outranks our
    own schedule.
    Search's FetchResult/Attempt expose no headers or Retry-After value.
    """
    if getattr(result, "ok", False):
        return 0
    trace = getattr(result, "trace", ())
    for attempt in reversed(tuple(trace)):
        status = int(getattr(attempt, "status", 0) or 0)
        if status in BACKPRESSURE_STATUSES:
            return status
    return 0


def _load_search_fetch() -> SearchFetch:
    for root in search_skill_roots():
        if (root / "engine" / "__init__.py").is_file():
            root_text = str(root)
            if root_text not in sys.path:
                sys.path.insert(0, root_text)
            spec = importlib.util.spec_from_file_location(
                "insane_search_engine",
                root / "engine" / "__init__.py",
                submodule_search_locations=[str(root / "engine")],
            )
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            fetch = module.__dict__.get("fetch")
            if isinstance(fetch, SearchFetch):
                return fetch
    msg = "insane-search engine not found; install insane-search or set INSANE_SEARCH_SKILL_ROOT"
    raise RuntimeError(msg)


def fetch_page(
    url: str,
    *,
    seed_url: str,
    timeout: int,
    max_attempts: int,
    allow_private: bool,
    browser_fallback: bool = True,
    receipt_dir: Path | None = None,
) -> FetchPageResult:
    """Fetch one page with a per-page attempt budget and extract same-site links."""
    if allow_private:
        os.environ["INSANE_ALLOW_PRIVATE"] = "1"
    fetch = _load_search_fetch()
    result = fetch(
        url,
        timeout=timeout,
        max_attempts=max_attempts,
        enable_playwright=False,
        enable_phase0=True,
        enable_extraction=True,
        enable_retry=True,
        enable_markdown=False,
        enable_maincontent=False,
    )
    backpressure = _backpressure_status(result)
    if result.ok or backpressure or not browser_fallback:
        final_url = result.final_url or url
        links = extract_links(result.content, final_url, seed_url) if result.ok else ()
        error = "" if result.ok else (result.summary or result.stop_reason or result.verdict)
        return FetchPageResult(
            ok=result.ok,
            requested_url=url,
            final_url=final_url,
            verdict=result.verdict,
            content=result.content,
            links=links,
            error=error,
            backpressure_status=backpressure,
        )
    browser = capture_page(url, timeout=timeout, receipt_dir=receipt_dir)
    final_url = browser.final_url or result.final_url or url
    links = extract_links(browser.html, final_url, seed_url) if browser.ok else ()
    receipt_path = str(receipt_dir / "browser-receipt.json") if receipt_dir is not None else ""
    if receipt_dir is not None and not Path(receipt_path).exists():
        write_receipt(browser, Path(receipt_path))
    error = "" if browser.ok else (browser.error or result.summary or result.stop_reason or result.verdict)
    return FetchPageResult(
        ok=browser.ok,
        requested_url=url,
        final_url=final_url,
        verdict="browser_ok" if browser.ok else result.verdict,
        content=browser.html if browser.html else result.content,
        links=links,
        error=error,
        receipt_path=receipt_path,
        backpressure_status=backpressure,
    )


def authority(url: str) -> str:
    """Return the robots and host-governor authority key."""
    parsed = urlsplit(url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return f"{parsed.scheme.lower()}://{(parsed.hostname or '').lower()}:{port}"
