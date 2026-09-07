from engine.robots_parser import can_fetch


def test_robots_merges_groups_and_prefers_allow_on_equal_length() -> None:
    text = """
    User-agent: insane-crawl
    Disallow: /private/*

    User-agent: insane-crawl
    Allow: /private/public$
    """
    assert can_fetch(text, "https://example.com/private/public", "insane-crawl") is True
    assert can_fetch(text, "https://example.com/private/other", "insane-crawl") is False


def test_specific_agent_group_wins_over_wildcard() -> None:
    text = """
    User-agent: *
    Disallow: /
    User-agent: insane-crawl
    Allow: /
    """
    assert can_fetch(text, "https://example.com/", "insane-crawl") is True
