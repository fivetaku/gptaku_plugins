from engine.urls import extract_links, normalize_url


def test_normalize_url_removes_fragments_and_tracking() -> None:
    assert normalize_url("HTTPS://Example.com:443/a/../b/?utm_source=x&z=2&a=1#part") == (
        "https://example.com/b/?a=1&z=2"
    )


def test_extract_links_keeps_same_site_document_order() -> None:
    html = """
    <a href="/b?utm_source=x">B</a>
    <a href="https://docs.example.com/c">C</a>
    <a href="https://other.test/no">No</a>
    <a href="/b">duplicate</a>
    """
    assert extract_links(html, "https://example.com/a", "https://example.com/") == (
        "https://example.com/b",
        "https://docs.example.com/c",
    )


def test_link_heavy_page_preserves_first_seen_normalized_order() -> None:
    links = []
    for number in range(500):
        links.extend((
            f'<a href="/p/{number}?utm_source=sample#first">first</a>',
            f'<a href="https://example.com/p/{number}#duplicate">duplicate</a>',
            '<a href="https://other.test/no">outside</a>',
        ))
    assert extract_links("".join(links), "https://example.com/", "https://example.com/") == tuple(
        f"https://example.com/p/{number}" for number in range(500)
    )
