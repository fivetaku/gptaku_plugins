# Verified workflow improvements

## Scope and state

- User request: improve the reviewed items sequentially on a branch, validate
  them, and retain only changes with demonstrated benefit.
- Worktree: `/Users/chulrolee/gptaku_plugins-improve-20260905`.
- Parent and submodule branch: `improve/verified-workflows-20260905`.
- Parent baseline: `463544e42720e0e442a310e3bc78673ffd33be77`.
- Original checkout remains on `main` at that commit.
- No project commit, merge, push, version bump, release, or installation repair
  has been performed. Test commits and pushes used disposable local repositories.
- The crawler is a copy of the existing untracked development source. Its
  baseline was 32 text files and 21 passing tests. It was not added to the
  public marketplace. Do not stage the entire worktree as a public release.
- Private slide/video repositories have isolated worktrees, but their original
  uncommitted work was not imported.

## Decisions on the 18 review items

| Item | Decision | Evidence or boundary |
| --- | --- | --- |
| 1. Release instructions | Adopt | Shared AGENTS/CLAUDE instructions reference one procedure; hidden-file-preserving copy and staged replacement are documented. |
| 2. Release change isolation | Adopt | An unrelated staged file was committed before the fix; real temporary-repository tests now reject that operation before mutation. |
| 3. Cache-content verification | Adopt, with runtime correction | Equal SHA no longer bypasses content comparison. Exact documented runtime-only directories do not count as source drift. |
| 4. Crawler dependency resolution | Adopt in private development copy | Registered installPath works without a development sibling. Missing optional endpoint miner remains unavailable. |
| 5. Crawler backpressure | Adopt in private development copy | Failed 429/503 pauses persist for 60 seconds, preserving the pending page and ordered resume. |
| 6. Evaluation false positives | Partial adoption | Exact claim-ID boundaries are fixed. The full-text replacement was rejected because it missed a shortened unverified assertion that the old heuristic detected. Shared-topic heuristic false positives remain. |
| 7. Slide command declaration | Hold | The reported defect exists only in substantial uncommitted private work. The isolated committed command passes validation and was not changed. |
| 8. Product/document consistency | Adopt | All five READMEs show 18 public entries, platform exceptions are explicit, and the MIT link has a root LICENSE target. |
| 9. Evidence-based acceptance | Partial adoption | Proven release-isolation and source-boundary regression suites are connected to CI; no private pilot threshold or new benchmark framework was adopted. |
| 10. Optional handoffs | Adopt as a document contract | Existing assumption ledgers are carried into PLAN/VALIDATION/PROGRESS without inventing a ledger or forcing another interview. |
| 11. Research status registry | No change | Existing research observation/provenance mechanisms were found; no demonstrated defect justified another registry. |
| 12. Output quality systems | No change | Existing design/slide/video checks were inspected; video best-generation regression tests pass. No newly generated visual artifact was claimed accepted. |
| 13. Context routing | No change | DD already routes before large-body analysis; actual size/preview functions were exercised without accessing the clipboard. |
| 14. Resume/completion consistency | Adopt as a document contract | Earlier failed phases precede later pending phases; completion labels cannot substitute for required verification evidence. |
| 15. Tool-aware onboarding | Adopt as a document contract | Grok discovery uses the real runner's check path, and selection is conditional on availability. |
| 16. Public-source boundary | Adopt | Listed ignored, research, outside, and symlink-escaping sources are rejected; all 18 existing public entries still pass. |
| 17. More promotional material | No change | Existing Try prompts and usage/self-check examples already connect capability to use; no benefit justified more copy. |
| 18. Verification record integrity | Adopt | Failed or interrupted rechecks revoke previous success; missing inputs/markers record failure without fabricated coverage, and repaired inputs can pass again. |

The document-contract changes were checked for consistency, syntax, and their
illustrative routing behavior. They were not replayed end-to-end in a live
Claude Code interview. No latency, token-saving, or visual-quality gain is
claimed for those prose changes.

## Captured verification

Commands below use `ROOT=/Users/chulrolee/gptaku_plugins-improve-20260905`.
Python 3.12 is `/opt/homebrew/bin/python3.12`. Default Python 3.14 has no pytest;
the existing Python 3.12 installation was used without adding dependencies.

| Scenario | Command or action | Observed result |
| --- | --- | --- |
| Release helper, real Git fixtures | `python3.12 "$ROOT/tools/test_plugin_release.py" -v` | `Ran 17 tests in 234.608s` followed by `OK`; local bare-remote pushes included. |
| Release red reproduction | Original helper with an unrelated staged file | Returned success and committed both `plugins/demo` and `unrelated.txt`. |
| Cache diagnosis fixtures | `python3.12 "$ROOT/tools/test_gptaku_doctor.py"` | `18/18` fixture cases, then `Ran 14 tests in 7.767s`, `OK`. |
| Same-SHA red reproduction | Altered cached command with matching metadata | Original checker reported all relevant axes as OK. |
| Runtime-directory red reproduction | Isolated search observations and Pumasi jobs/dependencies | Both produced exit 1 before the runtime-only correction. |
| Crawler full suite | `python3.12 -m pytest -q -p no:cacheprovider -o pythonpath="$ROOT/plugins/insane-crawl/skills/insane-crawl" "$ROOT/plugins/insane-crawl/skills/insane-crawl/tests"` | Final review corrections: `42 passed in 39.09s`. |
| Crawler actual entry points | Isolated registered search import, crawl/page/discover, fresh resume/status/events processes | Registered content persisted; missing miner reported unavailable; early resume performed zero requests; due resume recovered the preserved page. |
| Backpressure red reproduction | Failed 429 and 503 responses | Old coordinator requested the next page instead of stopping; both cases failed. |
| Research full suite | `python3.12 -m pytest -q -p no:cacheprovider "$ROOT/plugins/insane-research/tests"` | `64 passed in 36.09s`. |
| Evaluation comparison | Original versus full-text candidate on the same shortened assertion | Original detected it; candidate missed it. That candidate was not retained. |
| Verification-state red reproduction | Successful CLI check, delete verified input, recheck | CLI exited 2 but persisted `passed=true`; new regression failed with `assert True is False`. |
| Public-source boundary | `python3.12 "$ROOT/tools/test_validate_marketplace.py" -v` | Final 16 tests passed in 14.326s, including Windows path semantics. The earlier 15-test suite also passed on Python 3.14. |
| Public-source red reproduction | Listed ignored source in a disposable Git repository | Old validator returned 0 instead of 1. |
| Windows path red/green | Actual validator with stdlib `ntpath`; only unavailable filesystem/Git I/O substituted | All three valid source forms failed before the correction. They now reach the native `C:\repo\plugins\demo` lookup while retaining the POSIX Git path. |
| Provider contract | `bash "$ROOT/plugins/kkirikkiri/tests/test-provider-args.sh"` | `23 passed, 0 failed`, using fake generation CLIs. |
| Missing Grok | Runner `check grok` with isolated HOME and system-only PATH | Exit 1, `grok: not found`; no generation/authentication call. |
| Existing video regression | `python3.12 "$ROOT/plugins/insane-video/tests/test_regression_best.py"` | 2 tests, `OK`. |
| Existing DD functions | Import and call size/preview functions with 30, 7000, 20000, 50000 characters | small/medium/large/huge; large and huge marked for summaries; previews bounded to 124 characters including suffix. |
| Resume code example | Execute the documented example with failed/in-progress/pending states | Earlier failed/in-progress phase 2 selected before pending phase 3. |
| Documentation/config | Markdown rendering, five Bash blocks through `bash -n`, YAML parsing, badge-to-manifest count and license-target checks | Passed; five README badge counts equal the 18-entry manifest. |
| Final marketplace/command/contracts | `validate_marketplace.py`, `validate_commands.py`, `validate_skill_contracts.py` | 18 entries pass, 29 command files pass, 28 assertions pass. The sole marketplace warning is the untracked, unregistered crawler. |

The first native release-suite invocation hit an outer 180-second watcher limit
after nine tests had passed. The complete run above used a 600-second watcher
budget; no tests were skipped, weakened, or given polling delays.

## Live installation diagnosis

The improved doctor was run read-only against the real installation:

```text
Before runtime-only correction:
ok 129, warn 1, fail 2, unverified 20

After runtime-only correction:
ok 130, warn 1, fail 1, unverified 20
```

- Search's added `skills/insane-search/observations` directory was a normal
  runtime artifact, not source corruption; that false positive is corrected.
- Pumasi still differs in `skills/pumasi/package.json` dependencies and
  `package-lock.json`; an additional `.codegraph` directory is also present.
  This existing installation difference is reported, not repaired.
- The warning is the intentionally disabled `git-teacher` entry.
- Release/network checks remain unverified. Exit 0 is not a claim that every
  optional axis was checked.

Runtime allowances are exact plugin-relative directories, only when absent
from the source. Same-named directories elsewhere, shipped observation data,
regular files at runtime names, and source changes remain failures.

## Limits and gate review

- Insane-search does not expose Retry-After headers to the crawler. Its internal
  retry transport has a bounded numeric-header policy; the crawler truthfully
  reports its own 60-second default. HTTP-date handling was not added.
- The evaluation heuristic is not semantic verification; partial-word false
  positives, quotation/negation ambiguity, and paraphrase limits remain.
- Existing doctor LSP errors concern optional `__doc__` and the `min` key.
  The existing fixture also has an `enable=None` typing diagnostic. These were
  not suppressed or broadened into unrelated type refactoring.
- A Python-3.12-aware check of selected new files reported 0 errors and 73
  warnings, including existing untyped tests and JSON-boundary warnings. This
  is not an all-warning-free type-check claim.
- Shell/YAML/Markdown language servers were unavailable. Shell syntax, YAML
  parsing, and document rendering were used without installing tooling.
- Native Windows hardware and Windows Git were not executed. The portability
  regression was reproduced and corrected through actual validator execution
  with the standard library's Windows path semantics.
- The first independent gate review rejected a Windows separator regression in
  the new source guard. Manifest paths now use POSIX normalization; filesystem
  paths are joined from native components. Traversal/ignore/symlink tests remain.
- The review's fixture note was also corrected: the unregistered higher-version
  miner is now placed under the real `insane-search/99.0.0` fixture path. New
  SQLite casts were replaced by the neighboring code's concrete conversions.
- Final marketplace/command/contract checks passed. The fresh independent
  re-review returned **APPROVE**, with no remaining criterion-linked blockers.
- Re-review independently passed the 16-test marketplace suite and 15 targeted
  crawler tests. All 18 entries reached native Windows lookup with POSIX Git
  arguments; restoring either old predicate caused 0/18 to reach lookup.
- The re-review result is recorded in
  `.omo/evidence/verified-workflows-20260905-gate-recheck.md`. The reviewer could
  not write that file in its own environment, so the lead recorded its delivered
  result without substituting source edits or inventing evidence.
