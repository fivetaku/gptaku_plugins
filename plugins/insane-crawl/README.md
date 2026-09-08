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
- `discover` reuses the local `insane-search` endpoint miner. Mined candidates
  remain `candidate`, and replayed GET JSON endpoints remain `probable`; neither
  becomes a trusted fast-path recipe without page-render attribution.

## Dependencies

`insane-crawl` expects a local `insane-search` engine. In the marketplace both
plugins can be installed together. For source development, the sibling
`plugins/insane-search/skills/insane-search` directory is detected
automatically; `INSANE_SEARCH_SKILL_ROOT` overrides it.

## State

Default: `~/.local/state/insane-crawl`. Override with `--state-dir` or
`INSANE_CRAWL_STATE_DIR`. State is never written into the target repository or
the installed plugin directory.

## Boundaries

Respect applicable law, site terms, robots rules, rate limits, and content
signals. `--ignore-robots` is explicit and recorded in job metadata. See
`DISCLAIMER.md`.
