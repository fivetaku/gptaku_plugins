"""Isolated CloakBrowser worker; executed by the pinned external runtime."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from cloakbrowser import launch  # pyright: ignore[reportMissingImports]
from curl_cffi import requests  # pyright: ignore[reportMissingImports]


def main() -> int:
    url, output, timeout_text = sys.argv[1:4]
    timeout = int(timeout_text)
    browser = launch(headless=True, locale="ko-KR")
    page = browser.new_page()
    network: list[dict[str, str | int]] = []
    page.on(
        "response",
        lambda response: network.append(
            {
                "status": response.status,
                "resource_type": response.request.resource_type,
                "url": response.url,
                "content_type": response.headers.get("content-type", ""),
            }
        ),
    )
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
        page.wait_for_timeout(min(10_000, timeout * 250))
        html = page.content()
        cookies = page.context.cookies()
        replay_status, replay_bytes, replay_ok = replay(url, cookies, timeout)
        payload = {
            "ok": len(html) >= 300 and page.locator("#sec-if-cpt-container").count() == 0,
            "final_url": page.url,
            "title": page.title(),
            "html": html,
            "cookies": [
                {
                    "name": item["name"],
                    "value": item["value"],
                    "domain": item["domain"],
                    "path": item["path"],
                    "secure": item["secure"],
                    "http_only": item["httpOnly"],
                }
                for item in cookies
            ],
            "network": network,
            "replay_ok": replay_ok,
            "replay_status": replay_status,
            "replay_bytes": replay_bytes,
            "error": "",
        }
    except (OSError, RuntimeError, TimeoutError, ValueError) as error:
        payload = {
            "ok": False,
            "final_url": page.url,
            "title": "",
            "html": "",
            "cookies": [],
            "network": network,
            "replay_ok": False,
            "replay_status": 0,
            "replay_bytes": 0,
            "error": f"{type(error).__name__}: {error}",
        }
    finally:
        browser.close()
    Path(output).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return 0


def replay(url: str, cookies: list[dict[str, object]], timeout: int) -> tuple[int, int, bool]:
    session = requests.Session(impersonate="chrome145")
    for item in cookies:
        session.cookies.set(
            str(item["name"]),
            str(item["value"]),
            domain=str(item["domain"]),
            path=str(item["path"]),
        )
    response = session.get(
        url,
        headers={"Referer": url, "Accept-Language": "ko-KR,ko;q=0.9"},
        timeout=timeout,
    )
    lowered = response.text.lower()
    replay_ok = response.status_code < 400 and "sec-if-cpt-container" not in lowered and len(response.content) >= 300
    return response.status_code, len(response.content), replay_ok


if __name__ == "__main__":
    raise SystemExit(main())
