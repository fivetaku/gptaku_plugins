"""SQLite and filesystem persistence for crawl jobs."""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from .models import EventPayload, JobState, JobStatus, PageRecord
from .store_read import read_events, read_page, read_results, read_status

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    seed_url TEXT NOT NULL,
    state TEXT NOT NULL,
    max_pages INTEGER NOT NULL,
    max_depth INTEGER NOT NULL,
    ignore_robots INTEGER NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS frontier (
    job_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    url TEXT NOT NULL,
    depth INTEGER NOT NULL,
    state TEXT NOT NULL,
    error TEXT NOT NULL DEFAULT '',
    lease_owner TEXT NOT NULL DEFAULT '',
    leased_at REAL,
    PRIMARY KEY (job_id, seq),
    UNIQUE (job_id, url),
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);
CREATE TABLE IF NOT EXISTS pages (
    job_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    url TEXT NOT NULL,
    final_url TEXT NOT NULL,
    status TEXT NOT NULL,
    depth INTEGER NOT NULL,
    title TEXT NOT NULL,
    content_path TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    content_length INTEGER NOT NULL,
    fetched_at TEXT NOT NULL,
    error TEXT NOT NULL,
    PRIMARY KEY (job_id, seq),
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);
CREATE TABLE IF NOT EXISTS events (
    job_id TEXT NOT NULL,
    event_seq INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);
"""


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _migrate_lease_columns(connection: sqlite3.Connection) -> None:
    """Add lease bookkeeping columns to databases created before they existed."""
    existing = {str(row["name"]) for row in connection.execute("PRAGMA table_info(frontier)")}
    if "lease_owner" not in existing:
        connection.execute("ALTER TABLE frontier ADD COLUMN lease_owner TEXT NOT NULL DEFAULT ''")
    if "leased_at" not in existing:
        connection.execute("ALTER TABLE frontier ADD COLUMN leased_at REAL")
    connection.commit()


@dataclass(frozen=True, slots=True)
class Lease:
    """One frontier row currently handed out to a worker."""

    seq: int
    url: str
    owner: str
    leased_at: float


@dataclass(frozen=True, slots=True)
class Store:
    root: Path

    @property
    def database(self) -> Path:
        return self.root / "crawl.sqlite3"

    def connect(self) -> sqlite3.Connection:
        self.root.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        connection.executescript(_SCHEMA)
        _migrate_lease_columns(connection)
        return connection

    def create_job(
        self,
        seed_url: str,
        *,
        max_pages: int,
        max_depth: int,
        ignore_robots: bool,
    ) -> str:
        job_id = uuid4().hex[:16]
        now = utc_now()
        with closing(self.connect()) as connection:
            connection.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)",
                (job_id, seed_url, "running", max_pages, max_depth, int(ignore_robots), now, now),
            )
            connection.execute(
                "INSERT INTO frontier(job_id, seq, url, depth, state) VALUES (?, 1, ?, 0, 'pending')",
                (job_id, seed_url),
            )
            connection.commit()
        self.event(job_id, "job_created", {"seed_url": seed_url})
        return job_id

    def event(self, job_id: str, kind: str, payload: EventPayload) -> None:
        with closing(self.connect()) as connection:
            connection.execute(
                "INSERT INTO events(job_id, created_at, kind, payload) VALUES (?, ?, ?, ?)",
                (job_id, utc_now(), kind, json.dumps(payload, ensure_ascii=False, sort_keys=True)),
            )
            connection.commit()

    def status(self, job_id: str) -> JobStatus:
        return read_status(self.connect(), self.root, job_id)

    def lease_next(self, job_id: str, *, owner: str, now: float) -> sqlite3.Row | None:
        """Hand out the next pending row, recording who took it and when."""
        with closing(self.connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT seq, url, depth FROM frontier WHERE job_id=? AND state='pending' ORDER BY seq LIMIT 1",
                (job_id,),
            ).fetchone()
            if row is not None:
                connection.execute(
                    "UPDATE frontier SET state='leased', lease_owner=?, leased_at=? WHERE job_id=? AND seq=?",
                    (owner, now, job_id, row["seq"]),
                )
            connection.commit()
            return row

    def active_leases(self, job_id: str) -> tuple[Lease, ...]:
        """Return rows currently handed out, oldest lease first."""
        with closing(self.connect()) as connection:
            rows = connection.execute(
                "SELECT seq, url, lease_owner, leased_at FROM frontier"
                " WHERE job_id=? AND state='leased' ORDER BY seq",
                (job_id,),
            ).fetchall()
        return tuple(
            Lease(
                seq=int(row["seq"]),
                url=str(row["url"]),
                owner=str(row["lease_owner"]),
                leased_at=float(row["leased_at"] if row["leased_at"] is not None else 0.0),
            )
            for row in rows
        )

    def reclaim_stale_leases(self, job_id: str, *, older_than_seconds: float, now: float) -> int:
        """Return abandoned leases to the frontier so a crash or hang cannot drop pages.

        A worker that dies never clears its row, and a worker that hangs looks identical
        to a dead one. Both are recovered by age, not by process liveness.
        """
        cutoff = now - max(0.0, older_than_seconds)
        with closing(self.connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            reclaimed = connection.execute(
                "UPDATE frontier SET state='pending', lease_owner='', leased_at=NULL"
                " WHERE job_id=? AND state='leased'"
                " AND COALESCE(leased_at, 0) <= ?",
                (job_id, cutoff),
            ).rowcount
            connection.commit()
        if reclaimed:
            self.event(job_id, "leases_reclaimed", {"count": reclaimed})
        return int(reclaimed)

    def commit_page(
        self,
        job_id: str,
        *,
        seq: int,
        url: str,
        final_url: str,
        depth: int,
        status: str,
        content: str,
        links: tuple[str, ...],
        error: str,
    ) -> None:
        pages_dir = self.root / "pages" / job_id
        pages_dir.mkdir(parents=True, exist_ok=True)
        digest = sha256(content.encode("utf-8", "surrogatepass")).hexdigest()
        content_path = pages_dir / f"{seq:08d}-{digest[:12]}.txt"
        content_path.write_text(content, encoding="utf-8")
        fetched_at = utc_now()
        title = next((line.strip("# ") for line in content.splitlines() if line.strip()), "")[:300]
        with closing(self.connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT OR REPLACE INTO pages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    job_id,
                    seq,
                    url,
                    final_url,
                    status,
                    depth,
                    title,
                    str(content_path),
                    digest,
                    len(content),
                    fetched_at,
                    error,
                ),
            )
            frontier_state = "done" if status == "ok" else "failed"
            connection.execute(
                "UPDATE frontier SET state=?, error=?, lease_owner='', leased_at=NULL"
                " WHERE job_id=? AND seq=?",
                (frontier_state, error, job_id, seq),
            )
            next_seq = int(
                connection.execute(
                    "SELECT COALESCE(MAX(seq), 0) + 1 FROM frontier WHERE job_id=?",
                    (job_id,),
                ).fetchone()[0]
            )
            for link in links:
                inserted = connection.execute(
                    "INSERT OR IGNORE INTO frontier(job_id, seq, url, depth, state) VALUES (?, ?, ?, ?, 'pending')",
                    (job_id, next_seq, link, depth + 1),
                ).rowcount
                if inserted == 1:
                    next_seq += 1
            connection.execute("UPDATE jobs SET updated_at=? WHERE job_id=?", (fetched_at, job_id))
            connection.commit()
        self.event(job_id, "page_committed", {"seq": seq, "url": final_url, "status": status})

    def skip_page(self, job_id: str, *, seq: int, reason: str) -> None:
        with closing(self.connect()) as connection:
            connection.execute(
                "UPDATE frontier SET state='skipped', error=?, lease_owner='', leased_at=NULL"
                " WHERE job_id=? AND seq=?",
                (reason, job_id, seq),
            )
            connection.commit()
        self.event(job_id, "page_skipped", {"seq": seq, "reason": reason})

    def set_state(self, job_id: str, state: JobState) -> None:
        with closing(self.connect()) as connection:
            connection.execute(
                "UPDATE jobs SET state=?, updated_at=? WHERE job_id=?",
                (state, utc_now(), job_id),
            )
            connection.commit()
        self.event(job_id, "state_changed", {"state": state})

    def cancel(self, job_id: str) -> None:
        with closing(self.connect()) as connection:
            connection.execute(
                "UPDATE jobs SET state='cancelled', cancelled=1, updated_at=? WHERE job_id=?",
                (utc_now(), job_id),
            )
            connection.commit()
        self.event(job_id, "cancelled", {})

    def results(self, job_id: str, limit: int, offset: int) -> tuple[PageRecord, ...]:
        return read_results(self.connect(), job_id, limit, offset)

    def page(self, job_id: str, seq: int) -> tuple[PageRecord, str]:
        return read_page(self.connect(), job_id, seq)

    def events(self, job_id: str, limit: int, offset: int) -> tuple[dict[str, str | int], ...]:
        return read_events(self.connect(), job_id, limit, offset)
