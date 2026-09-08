from pathlib import Path

from engine.store import Store


def _job(tmp_path: Path) -> tuple[Store, str]:
    store = Store(tmp_path)
    job_id = store.create_job(
        "https://example.com/",
        max_pages=5,
        max_depth=2,
        ignore_robots=False,
    )
    return store, job_id


def test_lease_records_owner_and_time(tmp_path: Path) -> None:
    store, job_id = _job(tmp_path)
    row = store.lease_next(job_id, owner="worker-1", now=100.0)
    assert row is not None
    leases = store.active_leases(job_id)
    assert [(lease.seq, lease.owner, lease.leased_at) for lease in leases] == [(1, "worker-1", 100.0)]


def test_abandoned_lease_is_reclaimed_after_expiry(tmp_path: Path) -> None:
    store, job_id = _job(tmp_path)
    assert store.lease_next(job_id, owner="dead-worker", now=100.0) is not None
    # Worker died: the row stays leased and no second worker can pick it up.
    assert store.lease_next(job_id, owner="worker-2", now=101.0) is None

    reclaimed = store.reclaim_stale_leases(job_id, older_than_seconds=30.0, now=200.0)
    assert reclaimed == 1

    recovered = store.lease_next(job_id, owner="worker-2", now=201.0)
    assert recovered is not None
    assert int(recovered["seq"]) == 1


def test_live_lease_is_not_reclaimed(tmp_path: Path) -> None:
    store, job_id = _job(tmp_path)
    assert store.lease_next(job_id, owner="worker-1", now=100.0) is not None
    assert store.reclaim_stale_leases(job_id, older_than_seconds=30.0, now=120.0) == 0
    assert store.lease_next(job_id, owner="worker-2", now=121.0) is None


def test_committed_page_clears_lease_bookkeeping(tmp_path: Path) -> None:
    store, job_id = _job(tmp_path)
    row = store.lease_next(job_id, owner="worker-1", now=100.0)
    assert row is not None
    store.commit_page(
        job_id,
        seq=int(row["seq"]),
        url="https://example.com/",
        final_url="https://example.com/",
        depth=0,
        status="ok",
        content="root",
        links=(),
        error="",
    )
    assert store.active_leases(job_id) == ()
    assert store.reclaim_stale_leases(job_id, older_than_seconds=0.0, now=10_000.0) == 0


def test_large_frontier_keeps_counts_deduplication_and_lease_order(tmp_path: Path) -> None:
    store, job_id = _job(tmp_path)
    store.commit_page(
        job_id, seq=1, url="https://example.com/", final_url="https://example.com/",
        depth=0, status="ok", content="root",
        links=tuple(f"https://example.com/{i % 1000}" for i in range(2000)), error="",
    )
    assert store.status(job_id).processed_pages == 1
    assert store.status(job_id).pending_pages == 1000
    leased = [store.lease_next(job_id, owner="worker", now=100.0) for _ in range(5)]
    assert [row["url"] for row in leased if row is not None] == [
        f"https://example.com/{i}" for i in range(5)
    ]
    assert store.status(job_id).pending_pages == 1000
