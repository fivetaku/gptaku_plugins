from pathlib import Path

from engine import crawler, robots
from engine.fetcher import FetchPageResult
from engine.robots import RobotsDecision


def _allow_robots(*_args, **_kwargs) -> RobotsDecision:
    return RobotsDecision(True, "robots_allow")


def _fetch_from(pages: dict[str, tuple[str, tuple[str, ...]]]):
    def fake_fetch(url: str, **_kwargs) -> FetchPageResult:
        content, links = pages[url]
        return FetchPageResult(True, url, url, "weak_ok", content, links, "")

    return fake_fetch


def test_successful_pages_are_paced_per_authority(tmp_path: Path, monkeypatch) -> None:
    """Pacing must apply between consecutive successes, not only after failures."""
    pages = {
        "https://example.com/": ("root", ("https://example.com/a", "https://example.com/b")),
        "https://example.com/a": ("a", ()),
        "https://example.com/b": ("b", ()),
    }
    slept: list[float] = []

    monkeypatch.setattr(crawler, "fetch_page", _fetch_from(pages))
    monkeypatch.setattr(crawler, "check_robots", _allow_robots)
    monkeypatch.setattr(crawler, "sleep", slept.append)
    # Frozen clock: no wall time passes between pages, so every wait observed
    # here is the pacer holding the crawler back rather than elapsed runtime.
    monkeypatch.setattr(crawler, "monotonic", lambda: 0.0)

    result = crawler.crawl(
        "https://example.com/",
        state_root=tmp_path,
        max_pages=3,
        max_pages_this_run=3,
        run_for_seconds=1000.0,
        delay_seconds=2.0,
    )

    assert result.status.processed_pages == 3
    # First request needs no wait; each later same-host request waits the full delay.
    assert slept == [2.0, 2.0]


def test_first_request_to_a_host_is_not_delayed(tmp_path: Path, monkeypatch) -> None:
    slept: list[float] = []
    monkeypatch.setattr(
        crawler,
        "fetch_page",
        _fetch_from({"https://example.com/": ("only", ())}),
    )
    monkeypatch.setattr(crawler, "check_robots", _allow_robots)
    monkeypatch.setattr(crawler, "sleep", slept.append)
    monkeypatch.setattr(crawler, "monotonic", lambda: 0.0)

    crawler.crawl(
        "https://example.com/",
        state_root=tmp_path,
        max_pages=1,
        max_pages_this_run=1,
        run_for_seconds=1000.0,
        delay_seconds=5.0,
    )
    assert slept == []


def test_robots_is_fetched_once_per_authority(tmp_path: Path, monkeypatch) -> None:
    pages = {
        "https://example.com/": ("root", ("https://example.com/a", "https://example.com/b")),
        "https://example.com/a": ("a", ()),
        "https://example.com/b": ("b", ()),
    }
    fetched: list[str] = []

    def fake_get(url: str, **_kwargs):
        fetched.append(url)

        class _Response:
            content = b"User-agent: *\nAllow: /\n"
            status_code = 200

        return _Response()

    monkeypatch.setattr(robots.requests, "get", fake_get)
    monkeypatch.setattr(crawler, "fetch_page", _fetch_from(pages))
    monkeypatch.setattr(crawler, "sleep", lambda _seconds: None)

    result = crawler.crawl(
        "https://example.com/",
        state_root=tmp_path,
        max_pages=3,
        max_pages_this_run=3,
        run_for_seconds=1000.0,
        delay_seconds=0.0,
    )

    assert result.status.processed_pages == 3
    assert fetched == ["https://example.com/robots.txt"]


def test_missing_robots_file_allows_crawling(monkeypatch) -> None:
    """RFC 9309 treats an unavailable (4xx) robots file as no restrictions."""

    class _NotFound:
        content = b""
        status_code = 404

    monkeypatch.setattr(robots.requests, "get", lambda *_a, **_k: _NotFound())
    decision = robots.check_robots(
        "https://example.com/page",
        user_agent="insane-crawl",
        timeout=5,
        allow_private=False,
    )
    assert decision.allowed is True
    assert decision.reason == "robots_unavailable_404"


def test_forbidden_and_server_error_robots_still_deny(monkeypatch) -> None:
    for status, reason in ((403, "robots_restricted_403"), (503, "robots_unreachable_503")):
        class _Response:
            content = b""
            status_code = status

        monkeypatch.setattr(robots.requests, "get", lambda *_a, **_k: _Response())
        decision = robots.check_robots(
            "https://example.com/page",
            user_agent="insane-crawl",
            timeout=5,
            allow_private=False,
        )
        assert decision.allowed is False
        assert decision.reason == reason
