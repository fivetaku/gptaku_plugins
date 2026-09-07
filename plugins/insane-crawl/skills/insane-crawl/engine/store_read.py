"""Read-only queries and row parsing for crawl state."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from .models import JobStatus, PageRecord, parse_job_state


def read_status(connect: sqlite3.Connection, root: Path, job_id: str) -> JobStatus:
    with closing(connect) as connection:
        job = connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if job is None:
            raise KeyError(job_id)
        counts = connection.execute(
            "SELECT state, COUNT(*) AS count FROM frontier WHERE job_id=? GROUP BY state",
            (job_id,),
        ).fetchall()
    by_state = {str(row["state"]): int(row["count"]) for row in counts}
    return JobStatus(
        job_id=job_id,
        state=parse_job_state(str(job["state"])),
        seed_url=str(job["seed_url"]),
        max_pages=int(job["max_pages"]),
        max_depth=int(job["max_depth"]),
        processed_pages=by_state.get("done", 0),
        pending_pages=by_state.get("pending", 0) + by_state.get("leased", 0),
        failed_pages=by_state.get("failed", 0) + by_state.get("skipped", 0),
        state_dir=str(root),
        ignore_robots=bool(job["ignore_robots"]),
        cancelled=bool(job["cancelled"]),
        pause_reason=str(job["pause_reason"]),
        retry_at=float(job["retry_at"]),
    )


def read_results(
    connect: sqlite3.Connection,
    job_id: str,
    limit: int,
    offset: int,
) -> tuple[PageRecord, ...]:
    with closing(connect) as connection:
        rows = connection.execute(
            "SELECT * FROM pages WHERE job_id=? ORDER BY seq LIMIT ? OFFSET ?",
            (job_id, limit, offset),
        ).fetchall()
    return tuple(page_record(row) for row in rows)


def read_page(connect: sqlite3.Connection, job_id: str, seq: int) -> tuple[PageRecord, str]:
    with closing(connect) as connection:
        row = connection.execute(
            "SELECT * FROM pages WHERE job_id=? AND seq=?",
            (job_id, seq),
        ).fetchone()
    if row is None:
        raise KeyError(f"{job_id}:{seq}")
    record = page_record(row)
    return record, Path(record.content_path).read_text(encoding="utf-8")


def read_events(
    connect: sqlite3.Connection,
    job_id: str,
    limit: int,
    offset: int,
) -> tuple[dict[str, str | int], ...]:
    with closing(connect) as connection:
        rows = connection.execute(
            "SELECT event_seq, created_at, kind, payload FROM events WHERE job_id=? ORDER BY event_seq LIMIT ? OFFSET ?",
            (job_id, limit, offset),
        ).fetchall()
    return tuple(
        {
            "event_seq": int(row["event_seq"]),
            "created_at": str(row["created_at"]),
            "kind": str(row["kind"]),
            "payload": str(row["payload"]),
        }
        for row in rows
    )


def page_record(row: sqlite3.Row) -> PageRecord:
    return PageRecord(
        seq=int(row["seq"]),
        url=str(row["url"]),
        final_url=str(row["final_url"]),
        status=str(row["status"]),
        depth=int(row["depth"]),
        title=str(row["title"]),
        content_path=str(row["content_path"]),
        content_sha256=str(row["content_sha256"]),
        content_length=int(row["content_length"]),
        fetched_at=str(row["fetched_at"]),
        error=str(row["error"]),
    )
