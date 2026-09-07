"""Minimal RFC-style robots group and longest-match parser."""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True, slots=True)
class Rule:
    allow: bool
    pattern: str


def can_fetch(text: str, url: str, user_agent: str) -> bool:
    """Apply merged best-matching groups and longest octet match."""
    groups: list[tuple[list[str], list[Rule]]] = []
    agents: list[str] = []
    rules: list[Rule] = []
    seen_rule = False
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, value = (part.strip() for part in line.split(":", 1))
        match field.lower():
            case "user-agent":
                if seen_rule and agents:
                    groups.append((agents, rules))
                    agents, rules, seen_rule = [], [], False
                agents.append(value.lower())
            case "allow" | "disallow":
                if agents and value:
                    rules.append(Rule(field.lower() == "allow", value))
                    seen_rule = True
            case _:
                continue
    if agents:
        groups.append((agents, rules))

    token = user_agent.lower().split("/", 1)[0]
    exact = [group_rules for group_agents, group_rules in groups if token in group_agents]
    selected = exact or [group_rules for group_agents, group_rules in groups if "*" in group_agents]
    path = urlsplit(url).path or "/"
    matches: list[Rule] = []
    for group_rules in selected:
        matches.extend(rule for rule in group_rules if _matches(rule.pattern, path))
    if not matches:
        return True
    longest = max(len(rule.pattern.rstrip("$")) for rule in matches)
    tied = [rule for rule in matches if len(rule.pattern.rstrip("$")) == longest]
    return any(rule.allow for rule in tied)


def _matches(pattern: str, path: str) -> bool:
    escaped = re.escape(pattern.rstrip("$"))
    expression = "^" + escaped.replace(r"\*", ".*")
    if pattern.endswith("$"):
        expression += "$"
    return re.search(expression, path) is not None
