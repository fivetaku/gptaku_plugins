from pathlib import Path

from engine import fetcher
from engine.browser_capture import BrowserCaptureResult, CookieRecord, NetworkRecord


class FailedSearchResult:
    ok = False
    content = "challenge"
    final_url = "https://example.com/blocked"
    verdict = "challenge"
    summary = "blocked"
    stop_reason = "budget"


def test_failed_http_fetch_escalates_to_browser(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(fetcher, "_load_search_fetch", lambda: lambda *_args, **_kwargs: FailedSearchResult())
    monkeypatch.setattr(
        fetcher,
        "capture_page",
        lambda *_args, **_kwargs: BrowserCaptureResult(
            ok=True,
            final_url="https://example.com/blocked",
            title="Recovered",
            html="<html><a href='/next'>next</a></html>",
            cookies=(CookieRecord("session", "value", ".example.com", "/", True, True),),
            network=(NetworkRecord(200, "xhr", "https://example.com/api/items", "application/json"),),
            replay_ok=True,
            replay_status=200,
            replay_bytes=1024,
            error="",
        ),
    )
    result = fetcher.fetch_page(
        "https://example.com/blocked",
        seed_url="https://example.com/",
        timeout=10,
        max_attempts=2,
        allow_private=False,
        browser_fallback=True,
        receipt_dir=tmp_path,
    )
    assert result.ok is True
    assert result.verdict == "browser_ok"
    assert result.links == ("https://example.com/next",)
    assert result.receipt_path.endswith("browser-receipt.json")
    assert Path(result.receipt_path).exists()


def test_browser_fallback_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setattr(fetcher, "_load_search_fetch", lambda: lambda *_args, **_kwargs: FailedSearchResult())
    result = fetcher.fetch_page(
        "https://example.com/blocked",
        seed_url="https://example.com/",
        timeout=10,
        max_attempts=2,
        allow_private=False,
        browser_fallback=False,
        receipt_dir=None,
    )
    assert result.ok is False
    assert result.verdict == "challenge"
