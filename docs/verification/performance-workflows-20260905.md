# Performance improvement experiments

## Scope

The user authorized performance improvements after the read-only assessment.
Continue on `improve/verified-workflows-20260905` in
`/Users/chulrolee/gptaku_plugins-improve-20260905`.

Preserve all prior verified, uncommitted changes documented in
`verified-workflows-20260905.md`. Original main, installations, private original
worktrees, versions, and publication state remain untouched.

Process candidates sequentially. Keep only measured improvements with preserved
outputs, correctness checks, and quality boundaries. A smaller prompt is not
proof of fewer billed tokens or equivalent model behavior. Offline timing does
not establish live network or model performance.

## Starting measurements

These are pre-implementation synthetic or historical observations, not shipped
improvement claims.

- Evaluator: 200 claims, 40,000-character verified text, 20,000-character body;
  three-run medians 1.269 seconds versus 0.2187 seconds for an in-memory
  equivalent exclusion-set reuse candidate. Outputs matched.
- Crawler links: 5,000 unique anchors; five-run medians 195.566 ms versus
  96.205 ms for an in-memory ordered-list plus membership-set candidate.
  Ordered outputs matched.
- Search import: five fresh processes, median 232.75 ms, excluding interpreter
  startup; repeated crawler loader median 0.138 ms. Whole-engine repeated import
  is not the demonstrated per-page bottleneck.
- Crawler SQLite: a successful page iteration traced four connections and
  57 statements, including 32 setup statements. In-memory timing does not
  establish on-disk WAL or full crawl throughput.

## Candidate ledger

| Candidate | Status |
| --- | --- |
| Evaluator exclusion-set reuse | Adopted; identical full evaluation output, 67 research tests pass |
| Ordered crawler link deduplication | Adopted; identical ordered URLs, link-heavy parity test |
| Search result/trace without duplicate retrieval | Adopted; optional --json-content plus first-call trace guidance; legacy JSON unchanged |
| Kkirikkiri preparation and gate repair | Held: live matched-model A/B unavailable after child-provider usage limit; no token/quality claim from shorter prose |
| Pumasi context/result delivery | Partial adoption: optional compact results only; worker input selection held pending quality A/B |
| Pumasi common gate reuse | Adopted opt-in: deterministic shared_readonly successes within one invocation; failures and invalidations retained |
| Search escalation/browser lifecycle | Held: no live recall/readiness corpus establishes equivalent collection; no wait or gate removal |
| Search lazy optional parsers | Adopted for PDF parsers; actual HTML/PDF/fallback regressions pass |
| Crawler database lifecycle/index | Partial adoption: secondary index built on writes after frontier growth; connection/transaction ownership unchanged |
| Research pre-dispatch duplicate work | Held: paired model/source-recall evaluation is needed to distinguish waste from independent verification |
| Design capture readiness/reuse | Held: no visual freshness/readiness corpus demonstrates safe wait removal or cross-run reuse |
| Review pack reuse | Held: complete selection/config/version invalidation and measured net packing benefit are not established |
| Private slide incremental rendering | Held: required newer manifest/readiness work is uncommitted private WIP, not this branch baseline |
| Private video detector decode reuse | Adopted: one decode with three independent filter branches, identical detector and verdict outputs |
| Goaljaby initial compact generation | Held: live Korean/English PRD quality/turn-count A/B unavailable; protected clauses remain unchanged |

## Measured adopted changes

Evaluator/link/SQLite and video timing drivers used the resident Python 3.14.3
kernel. Fresh-process import comparisons and Python regression commands used
Python 3.12. Before and after within each comparison used the same interpreter.

- Evaluator: full calculation with in-memory input loaders, 200 verified claims
  of 200 characters and 200 unresolved claims of 100 characters; five alternating
  trials. Median 1.7379 s to 0.6033 s, complete output equality. This is local
  evaluator computation, not end-to-end research latency. All 67 tests pass.
- Links: five alternating trials. 5,000 unique anchors: 225.523 ms to 99.651 ms.
  10,000 anchors with 5,000 normalized unique URLs: 452.398 ms to 180.728 ms.
  Ordered tuples match; additional set memory is the tradeoff.
- Search: real CLI entry point with an instrumented retrieval boundary reports
  `fetch_calls=1` with body, trace, and untrusted-content metadata. The new mode
  also masks sensitive final/trace/referer URL fields; legacy JSON behavior stays unchanged.
  Three CLI tests and the URL-masking suite cover this boundary. This eliminates a duplicate retrieval path;
  no live-network time saving is claimed.
- Pumasi compact results: the actual CLI fixture returns 285,714 bytes in legacy
  JSON versus 1,006 bytes in compact mode. Reports, gates, statuses, and source
  artifact contents match. Raw files remain available. This is byte reduction,
  not measured model-token savings.
- Pumasi shared gates: three task attributions require one actual successful
  common check instead of three. Opt-in only; unmarked checks, failures, active
  workers, different working directories, later calls, and intervening mutating
  checks are tested. Ten Node tests and 18 existing worker assertions pass.
  A final producer-to-consumer test caught and fixed start's omission of the
  shared flag. That test uses JSON (a YAML subset) and substitutes worker spawning;
  real gate/result CLI tests execute independently with real temporary files.
- PDF loading: five alternating fresh-process comparisons use the same source
  loader for baseline/current fetch_chain. Filesystem caches were not flushed;
  interpreter startup is excluded. Median 267.512 ms to 108.098 ms; initial PDF
  module loads fall from two to zero. Cost moves to first PDF use. Three loading
  tests, 18 content-rescue tests, and six PDF fallback tests pass.
- SQLite: actual temporary on-disk WAL databases, five alternating trials,
  including creation/bulk insertion, 100 status calls, and 50 leases.
  At 10,000 frontier URLs: median total 550.931 ms to 372.611 ms; status calls
  408.412 ms to 216.854 ms, while seeding increases 42.984 ms to 49.891 ms.
  At 1,000 URLs: total 305.016 ms to 274.744 ms. At 100 URLs: 256.278 ms versus
  251.317 ms, effectively unchanged in this small sample. Ordered results and
  counts match; the full crawler suite passes 44 tests.
- An unconditional index candidate was rejected: it slowed the 100-row
  workload. The retained version avoids building the index for small-only
  databases and does not repeat its DDL on every read connection.
- Video: five alternating trials on local generated MPEG4 fixtures. Full
  machine-check results are identical for normal, frozen, black, and short
  clips. Final normal 6-second 320x180 clip: 183.757 ms to 104.044 ms. A 10-second
  1280x720 30-fps clip: 523.674 ms to 434.868 ms. A two-video-stream fixture:
  223.343 ms to 131.431 ms. Decoder invocations fall from
  three to one, with a separate unchanged ffprobe call. All 13 existing/new
  machine-check tests pass, including actual CLI output, holds, aspect, duration,
  freeze, black defects and automatic stream selection. RGB rawvideo detector
  outputs were also equal. This does not measure paid generation latency.

## Review and limits

- The initial implementation and feasibility subagents stopped with
  `The usage limit has been reached`. The lead completed the local work.
- The older stability gate approval predates these performance edits and must
  not be presented as an approval of the newer performance changes.
- A separate text-only review was available. It identified a real regression in
  the initial complex-filter candidate: `[0:v]` selected the first stream rather
  than the legacy automatic stream. The new test reproduced a false black
  detection. The retained simple `-vf` graph uses implicit automatic selection,
  split branches with null sinks, and one output. Native multi-stream tests and
  complete-result comparisons passed after correction. Follow-up text review
  reported no remaining concrete blocker in the supplied corrective code.
  That review did not run tools or independently execute the test suites.
- Search/video LSP comparison: search fetch_chain retains 25 baseline errors
  (including optional-import environment and legacy annotations); video decreases
  from 11 baseline errors to five. New syntax/behavior is exercised by real
  Python/Node/ffmpeg entry points. JavaScript LSP is unavailable; Node syntax and
  native tests are used. No diagnostic suppression was added.
- No paid generation, live browser-route change, model-tier reduction, version
  bump, project commit, main merge, publication, or installation repair occurred.
- Final marketplace validation: all 18 entries pass, with the existing
  untracked crawler warning. All 29 command files and 28 skill-contract
  assertions pass. Parent and all affected submodule diff checks pass.
- Original main remains `463544e42720e0e442a310e3bc78673ffd33be77`.
  Eight bounded candidates were adopted; seven model/live/private-WIP candidates
  were held. Prior stability changes are preserved.

## Verification requirements

- Capture the current branch implementation before each experimental change.
- Performance checks report workload, repetitions, before/after timings and
  output parity. Do not enforce wall-clock speed thresholds in regression tests.
- Reuse existing test suites and execute the affected real CLI or public API.
- Run diagnostics; distinguish pre-existing warnings from newly introduced ones.
- Reject performance candidates that remove coverage, lose content, change
  extraction/normalization, hide failures, or reuse stale state.
- Record held candidates with the precise missing evidence or scope conflict.
