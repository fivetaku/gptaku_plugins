from dataclasses import dataclass

from engine import robots


@dataclass
class FakeResponse:
    content: bytes
    status_code: int = 200


def test_check_robots_uses_browser_transport(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_get(url: str, **kwargs) -> FakeResponse:
        captured["url"] = url
        captured["impersonate"] = str(kwargs["impersonate"])
        captured["has_headers"] = str("headers" in kwargs)
        return FakeResponse(b"User-agent: *\nAllow: /\n")

    monkeypatch.setattr(robots.requests, "get", fake_get)
    decision = robots.check_robots(
        "https://example.com/page",
        user_agent="insane-crawl",
        timeout=5,
        allow_private=False,
    )
    assert decision.allowed is True
    assert captured == {
        "url": "https://example.com/robots.txt",
        "impersonate": "safari184",
        "has_headers": "False",
    }
