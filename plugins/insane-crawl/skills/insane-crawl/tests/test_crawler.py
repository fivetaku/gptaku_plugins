from pathlib import Path

from engine import crawler
from engine.fetcher import FetchPageResult
from engine.store import Store


def test_crawl_pauses_and_resumes_in_deterministic_order(tmp_path: Path, monkeypatch) -> None:
    pages = {
        "https://example.com/": ("root", ("https://example.com/a", "https://example.com/b")),
        "https://example.com/a": ("a", ()),
        "https://example.com/b": ("b", ()),
    }

    def fake_fetch(url: str, **_kwargs) -> FetchPageResult:
        content, links = pages[url]
        return FetchPageResult(True, url, url, "weak_ok", content, links, "")

    monkeypatch.setattr(crawler, "fetch_page", fake_fetch)
    monkeypatch.setattr(crawler, "check_robots", lambda *_args, **_kwargs: type("D", (), {"allowed": True})())

    first = crawler.crawl(
        "https://example.com/",
        state_root=tmp_path,
        max_pages=3,
        max_pages_this_run=1,
    )
    assert first.status.state == "paused_budget"
    assert first.status.processed_pages == 1

    second = crawler.resume(first.status.job_id, state_root=tmp_path, max_pages_this_run=5)
    assert second.status.state == "completed"
    assert [page.url for page in Store(tmp_path).results(first.status.job_id, 10, 0)] == [
        "https://example.com/",
        "https://example.com/a",
        "https://example.com/b",
    ]


def test_crawl_records_robots_skip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(crawler, "check_robots", lambda *_args, **_kwargs: type("D", (), {"allowed": False, "reason": "robots_disallow"})())
    result = crawler.crawl("https://example.com/", state_root=tmp_path, max_pages=1)
    assert result.status.state == "completed"
    assert result.status.failed_pages == 1
    assert result.status.processed_pages == 0


def test_exhausted_failed_frontier_completes_job(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        crawler,
        "check_robots",
        lambda *_args, **_kwargs: type("D", (), {"allowed": False, "reason": "robots_disallow"})(),
    )
    result = crawler.crawl(
        "https://example.com/",
        state_root=tmp_path,
        max_pages=1,
        max_pages_this_run=1,
    )
    assert result.status.state == "completed"
    assert result.next_step == "results"
