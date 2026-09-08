English | [한국어](README.ko.md)

# insane-crawl

Local, resumable research crawling for public pages. It reuses `insane-search`
as the bounded single-page acquisition primitive, then adds deterministic
same-site traversal, SQLite checkpoints, robots admission, stored page
snapshots, and per-job receipts.

## Quick start

```bash
cd skills/insane-crawl
python3 -m engine crawl "https://example.com" --max-pages 20 --run-for 45
python3 -m engine status JOB_ID
python3 -m engine resume JOB_ID --run-for 45
python3 -m engine results JOB_ID --limit 20
python3 -m engine page JOB_ID 1 --limit 20000
```

The control response stays small. Full page bodies remain in local snapshots
and are read only with `page`; they are never dumped into one agent response.

## MVP boundary

- Public pages only; no login or paywall traversal.
- Same-site crawl with normalized URL deduplication.
- Persistent SQLite frontier and append-only events.
- Per-page fetch attempt budget, separate from the crawl page budget.
- `discover` reuses a compatible local `insane-search` endpoint miner, if present.
  Current insane-search releases do not include it; discovery reports
  `unavailable` without affecting crawl/fetch. Mined candidates
  remain `candidate`, and replayed GET JSON endpoints remain `probable`; neither
  becomes a trusted fast-path recipe without page-render attribution.

## Dependencies

`insane-crawl` expects a local `insane-search` engine. In the marketplace both
plugins can be installed together. Resolution prefers `INSANE_SEARCH_SKILL_ROOT`,
then the search plugin's registered `installPath` in
`~/.claude/plugins/installed_plugins.json`, then the development sibling
`plugins/insane-search/skills/insane-search`. Cache versions need not match;
unregistered cache directories are not selected by version ordering.

For optional discovery, `INSANE_SEARCH_ENDPOINT_MINER` can point directly to a
compatible local `endpoint_miner.py`. Otherwise discovery checks the same skill
roots before legacy marketplace/source locations. This plugin does not supply
an endpoint miner or turn missing discovery into a proven fast path.

## State

Default: `~/.local/state/insane-crawl`. Override with `--state-dir` or
`INSANE_CRAWL_STATE_DIR`. State is never written into the target repository or
the installed plugin directory.

## Boundaries

### Server backpressure

An unsuccessful page fetch reporting HTTP 429 or 503 pauses the entire job as
`paused_backpressure`. The page stays pending, not failed or completed, and
browser fallback is not attempted. `status` and crawl/resume JSON expose
`pause_reason` and `retry_at` (Unix seconds). Resume before that deadline returns
without requests; at or after it, an explicit `resume` retries the same page
before later pages. No background polling or cooldown sleep is scheduled.

The cooldown is a fixed, conservative **60 seconds per reported failure**.
The current insane-search `FetchResult` and `Attempt` trace expose status codes,
but neither headers nor Retry-After. Thus the reason is
`http_429_retry_after_unavailable` or `http_503_retry_after_unavailable`; this
pause does not claim to honor an unavailable header or HTTP date. Inside the
search transport, numeric Retry-After is already honored with a 10-second
total retry-sleep cap; HTTP-date values are ignored. Requests/retries within
that bounded search call are unchanged. A final successful fetch is stored
once even if an earlier search attempt was limited. Repeated unsuccessful
manual resumes can each establish a new 60-second pause; there is no automatic
retry loop or lifetime retry limit.

Respect applicable law, site terms, robots rules, rate limits, and content
signals. `--ignore-robots` is explicit and recorded in job metadata. See
`DISCLAIMER.md`.
