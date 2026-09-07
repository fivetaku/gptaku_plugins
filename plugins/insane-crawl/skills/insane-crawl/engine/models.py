"""Typed contracts shared by the crawler and CLI."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final, Literal, TypedDict

JobState = Literal["running", "paused_budget", "paused_backpressure", "completed", "cancelled", "failed"]
FrontierState = Literal["pending", "leased", "done", "failed", "skipped"]
DiscoveryState = Literal["unavailable", "candidate", "probable", "proven"]

DEFAULT_USER_AGENT: Final = "insane-crawl"


class EventPayload(TypedDict, total=False):
    seed_url: str
    seq: int
    url: str
    status: str
    reason: str
    state: str
    count: int
    authority: str
    delay_seconds: float
    retry_at: float


@dataclass(frozen=True, slots=True)
class PageRecord:
    seq: int
    url: str
    final_url: str
    status: str
    depth: int
    title: str
    content_path: str
    content_sha256: str
    content_length: int
    fetched_at: str
    error: str

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class JobStatus:
    job_id: str
    state: JobState
    seed_url: str
    max_pages: int
    max_depth: int
    processed_pages: int
    pending_pages: int
    failed_pages: int
    state_dir: str
    ignore_robots: bool
    cancelled: bool
    pause_reason: str = ""
    retry_at: float = 0.0

    def to_dict(self) -> dict[str, str | int | float | bool]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CrawlResult:
    status: JobStatus
    processed_this_run: int
    next_step: str

    def to_dict(self) -> dict[str, dict[str, str | int | float | bool] | int | str]:
        return {
            "job": self.status.to_dict(),
            "processed_this_run": self.processed_this_run,
            "next_step": self.next_step,
        }


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    state: DiscoveryState
    candidates: tuple[str, ...]
    reason: str
    report_path: str = ""
    json_endpoints: int = 0

    def to_dict(self) -> dict[str, str | int | list[str]]:
        return {
            "state": self.state,
            "candidates": list(self.candidates),
            "reason": self.reason,
            "report_path": self.report_path,
            "json_endpoints": self.json_endpoints,
        }


def parse_job_state(value: str) -> JobState:
    """Parse persisted state without a type-system escape hatch."""
    match value:
        case "running" | "paused_budget" | "paused_backpressure" | "completed" | "cancelled" | "failed":
            return value
        case _:
            raise RuntimeError(f"unknown persisted job state: {value}")
