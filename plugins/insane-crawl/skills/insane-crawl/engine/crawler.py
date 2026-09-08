"""Deterministic, bounded crawl coordinator."""
from __future__ import annotations

import os
from pathlib import Path
from time import monotonic, sleep, time
from urllib.parse import urlsplit
from uuid import uuid4

from .fetcher import fetch_page
from .models import DEFAULT_USER_AGENT, CrawlResult
from .robots import RobotsCache, check_robots
from .store import Store
from .urls import normalize_url

DEFAULT_DELAY_SECONDS = 1.0
DEFAULT_LEASE_TIMEOUT_SECONDS = 300.0


def _wall_clock() -> float:
    """Lease ages must survive process restarts, so they use wall-clock time."""
    return time()


class _HostPacer:
    """Space out requests to one authority, including consecutive successes.

    Backing off only after failures lets a healthy host absorb an unbroken
    burst at full speed, which is the behaviour a politeness delay exists to
    prevent.
    """

    def __init__(self, delay_seconds: float) -> None:
        self._delay = max(0.0, delay_seconds)
        self._next_allowed: dict[str, float] = {}

    def wait(self, url: str) -> float:
        if self._delay <= 0.0:
            return 0.0
        authority = urlsplit(url).netloc.lower()
        now = monotonic()
        earliest = self._next_allowed.get(authority)
        waited = 0.0
        if earliest is not None and earliest > now:
            waited = earliest - now
            sleep(waited)
            now = monotonic()
        self._next_allowed[authority] = now + self._delay
        return waited


def default_state_root() -> Path:
    """Resolve user-local state outside plugin and repository trees."""
    override = os.environ.get("INSANE_CRAWL_STATE_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_STATE_HOME", "").strip()
    return (Path(xdg).expanduser() if xdg else Path.home() / ".local" / "state") / "insane-crawl"


def crawl(
    seed_url: str,
    *,
    state_root: Path | None = None,
    max_pages: int = 100,
    max_depth: int = 3,
    max_pages_this_run: int = 20,
    run_for_seconds: float = 45.0,
    timeout: int = 20,
    max_attempts_per_page: int = 8,
    ignore_robots: bool = False,
    allow_private: bool = False,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
    lease_timeout_seconds: float = DEFAULT_LEASE_TIMEOUT_SECONDS,
) -> CrawlResult:
    """Create and run a crawl job until complete or the turn budget expires."""
    normalized = normalize_url(seed_url)
    if not normalized:
        raise ValueError("seed_url must be an absolute http(s) URL")
    store = Store(state_root or default_state_root())
    job_id = store.create_job(
        normalized,
        max_pages=max(1, max_pages),
        max_depth=max(0, max_depth),
        ignore_robots=ignore_robots,
    )
    return _run(
        store,
        job_id,
        max_pages_this_run=max_pages_this_run,
        run_for_seconds=run_for_seconds,
        timeout=timeout,
        max_attempts_per_page=max_attempts_per_page,
        allow_private=allow_private,
        delay_seconds=delay_seconds,
        lease_timeout_seconds=lease_timeout_seconds,
    )


def resume(
    job_id: str,
    *,
    state_root: Path | None = None,
    max_pages_this_run: int = 20,
    run_for_seconds: float = 45.0,
    timeout: int = 20,
    max_attempts_per_page: int = 8,
    allow_private: bool = False,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
    lease_timeout_seconds: float = DEFAULT_LEASE_TIMEOUT_SECONDS,
) -> CrawlResult:
    """Resume one persisted job with a fresh turn budget."""
    store = Store(state_root or default_state_root())
    status = store.status(job_id)
    if status.cancelled:
        return CrawlResult(status=status, processed_this_run=0, next_step="none")
    store.set_state(job_id, "running")
    return _run(
        store,
        job_id,
        max_pages_this_run=max_pages_this_run,
        run_for_seconds=run_for_seconds,
        timeout=timeout,
        max_attempts_per_page=max_attempts_per_page,
        allow_private=allow_private,
        delay_seconds=delay_seconds,
        lease_timeout_seconds=lease_timeout_seconds,
    )


def _run(
    store: Store,
    job_id: str,
    *,
    max_pages_this_run: int,
    run_for_seconds: float,
    timeout: int,
    max_attempts_per_page: int,
    allow_private: bool,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
    lease_timeout_seconds: float = DEFAULT_LEASE_TIMEOUT_SECONDS,
) -> CrawlResult:
    started = monotonic()
    processed_this_run = 0
    worker_id = uuid4().hex[:12]
    pacer = _HostPacer(delay_seconds)
    robots_cache = RobotsCache()
    # A worker that crashed or hung previously still owns its row; recover it
    # by age before leasing, so resume cannot silently skip those pages.
    store.reclaim_stale_leases(
        job_id,
        older_than_seconds=lease_timeout_seconds,
        now=_wall_clock(),
    )
    while processed_this_run < max(1, max_pages_this_run):
        status = store.status(job_id)
        if status.cancelled:
            return CrawlResult(status=status, processed_this_run=processed_this_run, next_step="none")
        if status.processed_pages >= status.max_pages:
            store.set_state(job_id, "completed")
            final = store.status(job_id)
            return CrawlResult(status=final, processed_this_run=processed_this_run, next_step="results")
        if monotonic() - started >= max(0.1, run_for_seconds):
            break
        row = store.lease_next(job_id, owner=worker_id, now=_wall_clock())
        if row is None:
            store.set_state(job_id, "completed")
            final = store.status(job_id)
            return CrawlResult(status=final, processed_this_run=processed_this_run, next_step="results")
        seq = int(row["seq"])
        url = str(row["url"])
        depth = int(row["depth"])
        if depth > status.max_depth:
            store.skip_page(job_id, seq=seq, reason="max_depth")
            processed_this_run += 1
            continue
        if not status.ignore_robots:
            decision = check_robots(
                url,
                user_agent=DEFAULT_USER_AGENT,
                timeout=min(timeout, 10),
                allow_private=allow_private,
                cache=robots_cache,
            )
            if not decision.allowed:
                store.skip_page(job_id, seq=seq, reason=decision.reason)
                processed_this_run += 1
                continue
        pacer.wait(url)
        page = fetch_page(
            url,
            seed_url=status.seed_url,
            timeout=timeout,
            max_attempts=max(1, max_attempts_per_page),
            allow_private=allow_private,
            receipt_dir=store.root / "receipts" / job_id / f"{seq:08d}",
        )
        links = page.links if depth < status.max_depth else ()
        store.commit_page(
            job_id,
            seq=seq,
            url=url,
            final_url=page.final_url,
            depth=depth,
            status="ok" if page.ok else "failed",
            content=page.content,
            links=links,
            error=page.error,
        )
        processed_this_run += 1
    final = store.status(job_id)
    if final.pending_pages == 0:
        store.set_state(job_id, "completed")
        final = store.status(job_id)
        return CrawlResult(status=final, processed_this_run=processed_this_run, next_step="results")
    store.set_state(job_id, "paused_budget")
    final = store.status(job_id)
    return CrawlResult(status=final, processed_this_run=processed_this_run, next_step="resume")
