"""CLI for local, resumable crawl jobs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .crawler import crawl, default_state_root, resume
from .discovery import discover
from .store import Store


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m engine", description="Local research crawler.")
    parser.add_argument("--state-dir", type=Path, default=None, help="Persistent state directory.")
    commands = parser.add_subparsers(dest="command", required=True)

    crawl_parser = commands.add_parser("crawl", help="Create and run a crawl job.")
    crawl_parser.add_argument("url")
    _add_run_options(crawl_parser)
    crawl_parser.add_argument("--max-pages", type=int, default=100)
    crawl_parser.add_argument("--max-depth", type=int, default=3)
    crawl_parser.add_argument("--ignore-robots", action="store_true")

    resume_parser = commands.add_parser("resume", help="Resume a persisted job.")
    resume_parser.add_argument("job_id")
    _add_run_options(resume_parser)

    for name in ("status", "cancel"):
        sub = commands.add_parser(name)
        sub.add_argument("job_id")

    results_parser = commands.add_parser("results", help="List bounded page metadata.")
    results_parser.add_argument("job_id")
    results_parser.add_argument("--limit", type=int, default=20)
    results_parser.add_argument("--offset", type=int, default=0)

    page_parser = commands.add_parser("page", help="Read one stored page without refetching.")
    page_parser.add_argument("job_id")
    page_parser.add_argument("seq", type=int)
    page_parser.add_argument("--offset", type=int, default=0)
    page_parser.add_argument("--limit", type=int, default=20_000)

    events_parser = commands.add_parser("events", help="List bounded job events.")
    events_parser.add_argument("job_id")
    events_parser.add_argument("--limit", type=int, default=50)
    events_parser.add_argument("--offset", type=int, default=0)

    fetch_parser = commands.add_parser("fetch", help="Fetch a one-page crawl job.")
    fetch_parser.add_argument("url")
    _add_run_options(fetch_parser)

    discover_parser = commands.add_parser("discover", help="Report endpoint-discovery readiness.")
    discover_parser.add_argument("url")
    discover_parser.add_argument("--max-bundles", type=int, default=8)
    discover_parser.add_argument("--max-probes", type=int, default=20)
    discover_parser.add_argument("--timeout", type=int, default=15)
    return parser


def _add_run_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-for", type=float, default=45.0)
    parser.add_argument("--max-pages-this-run", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--max-attempts-per-page", type=int, default=8)
    parser.add_argument("--allow-private", action="store_true", help="Local testing only.")


def _emit(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    state_root = args.state_dir or default_state_root()
    store = Store(state_root)
    try:
        match args.command:
            case "crawl":
                result = crawl(
                    args.url,
                    state_root=state_root,
                    max_pages=args.max_pages,
                    max_depth=args.max_depth,
                    max_pages_this_run=args.max_pages_this_run,
                    run_for_seconds=args.run_for,
                    timeout=args.timeout,
                    max_attempts_per_page=args.max_attempts_per_page,
                    ignore_robots=args.ignore_robots,
                    allow_private=args.allow_private,
                )
                _emit(result.to_dict())
            case "fetch":
                result = crawl(
                    args.url,
                    state_root=state_root,
                    max_pages=1,
                    max_depth=0,
                    max_pages_this_run=1,
                    run_for_seconds=args.run_for,
                    timeout=args.timeout,
                    max_attempts_per_page=args.max_attempts_per_page,
                    ignore_robots=False,
                    allow_private=args.allow_private,
                )
                _emit(result.to_dict())
            case "resume":
                result = resume(
                    args.job_id,
                    state_root=state_root,
                    max_pages_this_run=args.max_pages_this_run,
                    run_for_seconds=args.run_for,
                    timeout=args.timeout,
                    max_attempts_per_page=args.max_attempts_per_page,
                    allow_private=args.allow_private,
                )
                _emit(result.to_dict())
            case "status":
                _emit(store.status(args.job_id).to_dict())
            case "results":
                _emit({"items": [item.to_dict() for item in store.results(args.job_id, args.limit, args.offset)]})
            case "page":
                record, content = store.page(args.job_id, args.seq)
                start = max(0, args.offset)
                end = start + max(0, args.limit)
                _emit({"page": record.to_dict(), "content": content[start:end], "next_offset": end if end < len(content) else None})
            case "events":
                _emit({"items": list(store.events(args.job_id, args.limit, args.offset))})
            case "cancel":
                store.cancel(args.job_id)
                _emit(store.status(args.job_id).to_dict())
            case "discover":
                _emit(
                    discover(
                        args.url,
                        state_root=state_root,
                        max_bundles=args.max_bundles,
                        max_probes=args.max_probes,
                        timeout=args.timeout,
                    ).to_dict()
                )
            case unreachable:
                raise AssertionError(unreachable)
    except (KeyError, ValueError, RuntimeError, OSError) as error:
        print(f"insane-crawl: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
