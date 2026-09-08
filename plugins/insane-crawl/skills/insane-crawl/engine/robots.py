"""Conservative robots.txt admission for crawl jobs."""
from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlsplit

from curl_cffi import requests  # pyright: ignore[reportMissingImports]

from .robots_parser import can_fetch

_MAX_ROBOTS_BYTES = 512 * 1024


@dataclass(frozen=True, slots=True)
class RobotsDecision:
    allowed: bool
    reason: str


@dataclass(slots=True)
class RobotsCache:
    """Per-authority robots documents for one crawl run.

    RFC 9309 expects crawlers to reuse a fetched robots file rather than
    requesting it again for every page of the same authority.
    """

    entries: dict[str, RobotsDecision | str] = field(default_factory=dict)

    def get(self, authority: str) -> RobotsDecision | str | None:
        return self.entries.get(authority)

    def put(self, authority: str, value: RobotsDecision | str) -> None:
        self.entries[authority] = value


def _status_decision(status_code: int) -> RobotsDecision | None:
    """Map a robots transport status to an admission decision.

    RFC 9309 section 2.3.1.3 treats an unavailable (4xx) robots file as
    "no restrictions", while section 2.3.1.4 treats an unreachable server as
    a reason to stay out. Access-restricted responses stay conservative: the
    authority answered, and it answered that we may not read the policy.
    """
    if status_code in {401, 403}:
        return RobotsDecision(False, f"robots_restricted_{status_code}")
    if 400 <= status_code < 500:
        return RobotsDecision(True, f"robots_unavailable_{status_code}")
    if status_code >= 500:
        return RobotsDecision(False, f"robots_unreachable_{status_code}")
    return None


def check_robots(
    url: str,
    *,
    user_agent: str,
    timeout: int,
    allow_private: bool,
    cache: RobotsCache | None = None,
) -> RobotsDecision:
    """Evaluate authority-local robots rules, reusing one fetch per authority."""
    parsed = urlsplit(url)
    if allow_private:
        return RobotsDecision(True, "allow_private_test")
    authority = f"{parsed.scheme}://{parsed.netloc}"
    cached = cache.get(authority) if cache is not None else None
    if isinstance(cached, RobotsDecision):
        return cached
    if isinstance(cached, str):
        return _evaluate(cached, url, user_agent)

    try:
        response = requests.get(
            f"{authority}/robots.txt",
            impersonate="safari184",
            timeout=timeout,
        )
        body = response.content[: _MAX_ROBOTS_BYTES + 1]
        if len(body) > _MAX_ROBOTS_BYTES:
            decision = RobotsDecision(False, "robots_too_large")
            if cache is not None:
                cache.put(authority, decision)
            return decision
        status_decision = _status_decision(int(response.status_code))
        if status_decision is not None:
            if cache is not None:
                cache.put(authority, status_decision)
            return status_decision
    except OSError as error:
        return RobotsDecision(False, f"robots_unreachable:{type(error).__name__}")

    document = body.decode("utf-8", "replace")
    if cache is not None:
        cache.put(authority, document)
    return _evaluate(document, url, user_agent)


def _evaluate(document: str, url: str, user_agent: str) -> RobotsDecision:
    allowed = can_fetch(document, url, user_agent)
    return RobotsDecision(allowed, "robots_allow" if allowed else "robots_disallow")
