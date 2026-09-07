import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from typing import TypedDict

import pytest

from engine import crawler, fetcher
from engine.fetcher import FetchPageResult
from engine.store import Store


class ResumePayload(TypedDict):
    job: dict[str, str | int | float | bool]
    processed_this_run: int


@pytest.mark.parametrize("status_code", [429, 503])
def test_backpressure_persists_and_retries_in_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status_code: int,
) -> None:
    root = "https://example.com/"
    limited = root + "a"
    tail = root + "b"
    calls: list[str] = []
    now = [1000.0]

    def fetch(url: str, **_kwargs: str | int | bool | Path | None) -> FetchPageResult:
        calls.append(url)
        if url == limited and calls.count(limited) == 1:
            return FetchPageResult(
                False, url, url, "blocked", "busy", (), "limited",
                backpressure_status=status_code,
            )
        return FetchPageResult(True, url, url, "ok", url, (limited, tail) if url == root else (), "")

    def unexpected_sleep(_seconds: float) -> None:
        pytest.fail("backpressure must return, not sleep")

    monkeypatch.setattr(crawler, "fetch_page", fetch)
    monkeypatch.setattr(crawler, "_wall_clock", lambda: now[0])
    monkeypatch.setattr(crawler, "monotonic", lambda: 0.0)
    monkeypatch.setattr(crawler, "sleep", unexpected_sleep)
    first = crawler.crawl(
        root, state_root=tmp_path, max_pages=3, max_pages_this_run=5,
        ignore_robots=True, delay_seconds=0,
    )
    assert calls == [root, limited]
    assert first.status.state == "paused_backpressure"
    assert first.processed_this_run == first.status.processed_pages == 1
    assert first.status.failed_pages == 0
    assert first.status.pending_pages == 2
    assert first.next_step == "resume"
    assert first.status.retry_at == 1060.0
    assert first.status.pause_reason == f"http_{status_code}_retry_after_unavailable"
    store = Store(tmp_path)
    assert store.status(first.status.job_id) == first.status
    assert store.active_leases(first.status.job_id) == ()
    assert [page.url for page in store.results(first.status.job_id, 10, 0)] == [root]

    now[0] = 1059.0
    early = crawler.resume(first.status.job_id, state_root=tmp_path, delay_seconds=0)
    assert early.status == first.status
    assert early.processed_this_run == 0
    assert calls == [root, limited]
    assert store.lease_next(first.status.job_id, owner="early", now=now[0]) is None

    now[0] = 1060.0
    final = crawler.resume(first.status.job_id, state_root=tmp_path, delay_seconds=0)
    assert calls == [root, limited, limited, tail]
    assert final.status.state == "completed"
    assert final.status.processed_pages == 3
    assert final.status.failed_pages == final.status.pending_pages == 0
    assert final.processed_this_run == 2
    assert final.status.retry_at == 0.0
    assert final.status.pause_reason == ""
    assert [page.url for page in store.results(first.status.job_id, 10, 0)] == [root, limited, tail]


@pytest.mark.parametrize("recovered", [False, True])
def test_search_backpressure_skips_browser_but_keeps_recovered_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recovered: bool,
) -> None:
    calls: list[str] = []

    def search(url: str, **_kwargs: str | int | bool | Path | None) -> SimpleNamespace:
        calls.append(url)
        return SimpleNamespace(
            ok=recovered, content="page", final_url=url, verdict="ok" if recovered else "blocked",
            summary="limited", stop_reason="success" if recovered else "budget",
            trace=[SimpleNamespace(status=429), SimpleNamespace(status=200 if recovered else 503)],
        )

    def unexpected_browser(*_args: str, **_kwargs: int | Path | None) -> None:
        pytest.fail("reported backpressure must not launch a browser")

    monkeypatch.setattr(fetcher, "_load_search_fetch", lambda: search)
    monkeypatch.setattr(fetcher, "capture_page", unexpected_browser)
    monkeypatch.setattr(crawler, "_wall_clock", lambda: 1000.0)
    monkeypatch.setattr(crawler, "monotonic", lambda: 0.0)
    result = crawler.crawl(
        "https://example.com/", state_root=tmp_path, max_pages=1, ignore_robots=True,
    )
    assert calls == ["https://example.com/"]
    assert result.status.state == ("completed" if recovered else "paused_backpressure")
    assert result.status.processed_pages == int(recovered)
    assert result.status.failed_pages == 0
    if recovered:
        again = crawler.resume(result.status.job_id, state_root=tmp_path)
        assert again.status.processed_pages == 1
        assert calls == ["https://example.com/"]
    else:
        assert result.status.pause_reason == "http_503_retry_after_unavailable"


def test_success_with_earlier_backpressure_is_not_requeued(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fetch(url: str, **_kwargs: str | int | bool | Path | None) -> FetchPageResult:
        calls.append(url)
        return FetchPageResult(True, url, url, "ok", "page", (), "", backpressure_status=429)

    monkeypatch.setattr(crawler, "fetch_page", fetch)
    result = crawler.crawl("https://example.com/", state_root=tmp_path, ignore_robots=True)
    assert result.status.state == "completed"
    assert result.status.processed_pages == 1
    assert result.status.retry_at == 0
    _ = crawler.resume(result.status.job_id, state_root=tmp_path)
    assert calls == ["https://example.com/"]


def test_repeated_limit_has_bounded_new_deadline_and_cancel_still_wins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    now = [1000.0]

    def fetch(url: str, **_kwargs: str | int | bool | Path | None) -> FetchPageResult:
        calls.append(url)
        return FetchPageResult(False, url, url, "blocked", "", (), "limited", backpressure_status=429)

    monkeypatch.setattr(crawler, "fetch_page", fetch)
    monkeypatch.setattr(crawler, "_wall_clock", lambda: now[0])
    monkeypatch.setattr(crawler, "monotonic", lambda: 0.0)
    first = crawler.crawl("https://example.com/", state_root=tmp_path, ignore_robots=True)
    now[0] = 1100.0
    second = crawler.resume(first.status.job_id, state_root=tmp_path)
    assert second.status.retry_at == 1160.0
    assert second.status.pending_pages == 1
    assert second.status.processed_pages == second.processed_this_run == 0
    assert len(calls) == 2
    Store(tmp_path).cancel(first.status.job_id)
    cancelled = crawler.resume(first.status.job_id, state_root=tmp_path)
    assert cancelled.status.cancelled
    assert cancelled.next_step == "none"
    assert len(calls) == 2


def test_ordinary_failure_is_not_backpressure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fetch(url: str, **_kwargs: str | int | bool | Path | None) -> FetchPageResult:
        return FetchPageResult(False, url, url, "not_found", "", (), "404")

    monkeypatch.setattr(crawler, "fetch_page", fetch)
    result = crawler.crawl("https://example.com/", state_root=tmp_path, ignore_robots=True)
    assert result.status.state == "completed"
    assert result.status.failed_pages == 1
    assert result.status.retry_at == 0


def test_old_database_migrates_without_losing_frontier(tmp_path: Path) -> None:
    with closing(sqlite3.connect(tmp_path / "crawl.sqlite3")) as connection:
        _ = connection.executescript("""
            CREATE TABLE jobs (
                job_id TEXT PRIMARY KEY, seed_url TEXT NOT NULL, state TEXT NOT NULL,
                max_pages INTEGER NOT NULL, max_depth INTEGER NOT NULL,
                ignore_robots INTEGER NOT NULL, cancelled INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE frontier (
                job_id TEXT NOT NULL, seq INTEGER NOT NULL, url TEXT NOT NULL,
                depth INTEGER NOT NULL, state TEXT NOT NULL, error TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (job_id, seq), UNIQUE (job_id, url)
            );
            INSERT INTO jobs VALUES ('old', 'https://example.com/', 'paused_budget', 3, 2, 1, 0, '', '');
            INSERT INTO frontier VALUES ('old', 1, 'https://example.com/', 0, 'pending', '');
        """)
    store = Store(tmp_path)
    status = store.status("old")
    assert status.state == "paused_budget"
    assert status.pending_pages == 1
    assert status.pause_reason == ""
    assert status.retry_at == 0
    assert store.lease_next("old", owner="worker", now=1000.0) is not None
    store.pause_backpressure("old", seq=1, reason="http_429_retry_after_unavailable", retry_at=1060.0)
    assert Store(tmp_path).status("old").retry_at == 1060.0
    assert store.active_leases("old") == ()
    assert store.create_job("https://example.com/new", max_pages=1, max_depth=0, ignore_robots=True)


def test_fresh_cli_process_honors_pause_and_later_recovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def limited(url: str, **_kwargs: str | int | bool | Path | None) -> FetchPageResult:
        return FetchPageResult(False, url, url, "blocked", "", (), "limited", backpressure_status=503)

    home = tmp_path / "home"
    home.mkdir()
    state = tmp_path / "state"
    monkeypatch.setattr(crawler, "fetch_page", limited)
    monkeypatch.setattr(crawler, "_wall_clock", lambda: 1000.0)
    monkeypatch.setattr(crawler, "monotonic", lambda: 0.0)
    result = crawler.crawl("https://example.com/", state_root=state, ignore_robots=True)
    # Run the real CLI entry point in fresh interpreters. Only the clock and
    # network boundary are substituted; SQLite, resume and JSON are real.
    script = """
import runpy, sys
from engine import crawler
from engine.fetcher import FetchPageResult
now = float(sys.argv.pop(1))
crawler._wall_clock = lambda: now
crawler.monotonic = lambda: 0.0
def fetch(url, **kwargs):
    assert now >= 1060.0, 'CLI fetched before the deadline'
    return FetchPageResult(True, url, url, 'ok', 'recovered', (), '')
def forbidden(*args, **kwargs):
    raise AssertionError('unexpected request or sleep')
crawler.fetch_page = fetch
crawler.check_robots = forbidden
crawler.sleep = forbidden
runpy.run_module('engine', run_name='__main__')
"""
    # HOME isolation must not hide dependencies already installed in the
    # invoking interpreter's user site. Reuse its paths, not its user state.
    environment = {
        "PATH": os.environ["PATH"], "HOME": str(home),
        "INSANE_CRAWL_STATE_DIR": str(state), "XDG_STATE_HOME": str(home / "state"),
        "PYTHONPATH": os.pathsep.join(str(Path(entry).resolve()) for entry in sys.path),
    }
    for now, expected in ((1059, "paused_backpressure"), (1060, "completed")):
        process = subprocess.run(
            [sys.executable, "-c", script, str(now), "resume", result.status.job_id],
            cwd=Path(__file__).resolve().parents[1], env=environment,
            capture_output=True, text=True, timeout=15, check=True,
        )
        payload: ResumePayload = json.loads(process.stdout)
        job = payload["job"]
        assert job["state"] == expected
        assert payload["processed_this_run"] == int(now >= 1060)
        assert job["retry_at"] == (1060.0 if now < 1060 else 0.0)
    assert Store(state).page(result.status.job_id, 1)[1] == "recovered"
