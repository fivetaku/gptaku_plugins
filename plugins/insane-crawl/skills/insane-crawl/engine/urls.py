"""URL normalization and same-site link admission."""
from __future__ import annotations

import posixpath
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

_TRACKING_KEYS = frozenset({"fbclid", "gclid", "mc_cid", "mc_eid"})


class _LinkParser(HTMLParser):
    """Collect href values without executing page content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for name, value in attrs:
            if name == "href" and value:
                self.links.append(value)


def normalize_url(url: str) -> str:
    """Return a stable HTTP(S) URL fingerprint."""
    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    if scheme not in {"http", "https"} or not host:
        return ""
    port = parsed.port
    default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    authority = host if port is None or default_port else f"{host}:{port}"
    path = parsed.path or "/"
    normalized_path = posixpath.normpath(path)
    if path.endswith("/") and normalized_path != "/":
        normalized_path += "/"
    if not normalized_path.startswith("/"):
        normalized_path = "/" + normalized_path
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in _TRACKING_KEYS
    ]
    query.sort()
    return urlunsplit((scheme, authority, normalized_path, urlencode(query), ""))


def same_site(seed_url: str, candidate_url: str) -> bool:
    """Restrict traversal to the seed hostname and its subdomains."""
    seed_host = (urlsplit(seed_url).hostname or "").lower()
    candidate_host = (urlsplit(candidate_url).hostname or "").lower()
    return bool(seed_host and candidate_host) and (
        candidate_host == seed_host or candidate_host.endswith("." + seed_host)
    )


def extract_links(html: str, base_url: str, seed_url: str) -> tuple[str, ...]:
    """Extract unique normalized same-site links in document order."""
    parser = _LinkParser()
    parser.feed(html)
    links: list[str] = []
    seen: set[str] = set()
    for raw in parser.links:
        normalized = normalize_url(urljoin(base_url, raw))
        if normalized and same_site(seed_url, normalized) and normalized not in seen:
            seen.add(normalized)
            links.append(normalized)
    return tuple(links)
