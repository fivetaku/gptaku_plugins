# Kkirikkiri phased redesign

## Contract

The user authorized the proposed redesign only with verification and demonstrated
improvement at each stage before proceeding. Work stays on the existing
`improve/verified-workflows-20260905` branch. Preserve prior changes, including the
Grok discovery clarification. No main merge, version bump, installed-cache
replacement, or publication is performed here.

## Stage gates

1. Repaired baseline: remove contradictory interaction/round/leader instructions;
   prevent session-ledger crossover; require outcome evidence beyond incidental
   file changes. Retain existing command/card/Workflow checks and bounded stopping.
2. Preparation pilot: one Teams payload path only. Derive cards and payloads from
   one validated record. Do not implement a cross-host orchestration framework
   or claim prompt restrictions are enforced runtime permissions.
3. Compare: same plan, models, topology and checks. Measure preparation work and
   first-pass validity. End-to-end quality/token/latency claims require actual
   paired host runs; deterministic payload parity alone does not establish them.
4. Adopt only the proven scope. Record unsupported or unmeasured extensions as
   held, not completed behavior.

## Baseline

- Prior kkirikkiri working-tree difference: Grok environment discovery and
  conditional fallback instructions only.
- `tests/run-gates.sh` passed before redesign using a temporary HOME, with the
  existing workflow, card, done and hook fixtures.
- Existing completion fixtures intentionally permit a changed tree without
  evidence; an outcome-aware opt-in contract will need separate regressions.
- Existing hooks do not store session identity. Legacy test inputs omit it.

## Increment evidence

### Questions and mode approval

- Removed unconditional duplicate interview reference loading at command entry.
- Questions already answered by the request/context are not repeated.
- Execution diagnosis recommends; it cannot override an explicit mode choice.
- Mode/configuration approval is obtained together, not repeated when unchanged.
- Four policy dry-run scenarios produced expected decisions: already approved,
  unavailable selected mode, missing goal, and recommendation without approval.
  This checks instruction consistency, not live UI behavior or token savings.
- Existing Step 3.6 routing regression: 15 passed, 0 failed.

### Round and coordination policy

- First-round acceptance can finish successfully; no compulsory second pass.
- Default ceiling is two rounds. Extra rounds need explicit approval and a
  concrete unresolved criterion. No improvement means stop with unresolved work.
- The requesting host is the default coordinator. A second Leader is not
  automatically spawned just to relay task assignments.
- Four policy dry-run scenarios matched expected actions. This is not a live
  multi-agent speedup measurement.
- The main and external-agent spawn examples now include actual boundary values
  in the payload and distinguish platform team identity from directory names.

### Session ledger identity

- Failing-first tests exposed crossover/missing ownership and worktree detection.
- All 14 focused tests pass: two sessions in one cwd, ancestor drift, closed and
  same-second runs, aliases, missing ownership, ambiguous matches, legacy handling.
- The actual init/spawn/done shell hooks share `gate_ledger.py`; another session's
  bytes remain unchanged. Identified runs never adopt unowned legacy context.
- Concurrent updates within one session remain unserialized. Ambiguity blocks
  rather than choosing a latest ledger; no locking or filesystem isolation is claimed.

### Acceptance-bound completion

- All nine initial test groups failed under the old mutation-only path.
- New session-owned runs automatically receive a completion-contract location.
  Missing or invalid contracts block verification rather than accepting unrelated
  untracked files.
- Twelve new test groups pass. The gate runs criterion argv commands, requires
  the report and declared artifacts, records their hashes and exit results, and
  rejects changed validation inputs. Analysis and justified no-change work can
  pass without artificial edits.
- Session ledger regressions remain 14/14 passing after hook integration.
- Old manually created contractless ledgers retain their explicit legacy mode;
  that mode is not represented as acceptance verification.
- The Stop hook's bounded loop-release still records a failing outcome; ending
  a conversation after the cap does not become successful completion.
- Full repaired-baseline gate regression passed before the preparation pilot.
- Independent review found a timeout mismatch: each check allowed 30 seconds
  but Stop allowed 20. The correction uses one 45-second total budget within a
  60-second Stop hook, with 30 seconds maximum per check and skipped/failed
  remaining criteria after exhaustion.

### Preparation pilot and review corrections

- `prepare-team.js` is an opt-in artifact generator, not an execution runtime.
  It supports 2-6 total producers and critics, exact relative scopes or
  directory/**, explicit models and approval revision, and complete criterion
  assignment. Producer and review stages are explicit.
- The first implementation generated artifacts but required review corrections:
  root-level filenames could be lost by the old scope heuristic, and stop text
  could be accepted by preparation but rejected by card-lint.
- Canonical JSON scope arrays now survive the actual spawn hook, including
  Makefile, .gitignore and main.c. Legacy prose extraction remains separate.
- Preparation calls the existing card-lint function before any output creation.
  No second independent interpretation is claimed authoritative.
- The first authoritative-validator test used `[unknown]`, which the old
  parser actually accepts. It was corrected to `[]`, whose C1-effort rejection
  was measured directly. No `[unknown]` rejection is claimed.
- The final preparation suite passes 16 tests, including real card/spawn hooks,
  read-only analysis, invalid plans, overlap, exact payload fields, and overwrite
  refusal. Prior artifacts are not overwritten.

### Runtime binding probe

- The initial named-team probe returned UNSUPPORTED and executed no agents:
  Claude Code reported team_name as deprecated/ignored with one implicit team.
  Its additional interpretation that this precluded all team execution was not
  accepted without a separate probe.
- An implicit-session probe executed two producers followed by a critic. The
  final generator omits deprecated runtime team_name/name fields, retains
  task_id outside the input, and emits description/model/subagent_type/prompt.
- A final live Claude Code 2.1.259 host executed all three final requests.
  Captured Agent arguments preserved the exact generated prompts, models and
  types. Both producer tool results arrived before the critic call.
- The read-only fixture returned counts 3 and 4, and the independent critic
  confirmed the mismatch. The parent reported 28,046ms and $0.2324738; the cost
  field is CLI-reported accounting, not a claim of incremental subscription billing.
- These probes used explicitly enabled Agent/Read tools and disabled ambient
  hooks/MCP auto-execution. Existing gates were exercised separately. This is
  one actual implicit-session Agent path, not proof of general collaboration,
  runtime scope enforcement, or every host's tool contract.

### Matched-plan preparation measurement

The plan already contained approved tasks, roles, models, scopes, stop conditions
and acceptance criteria. Neither arm performed planning or task execution.

- An initial under-specified serialization probe used archetypes as runtime
  agent types. It was excluded from the matched comparison and not described
  as the current repaired baseline.
- The matched model arm received the repaired manual template and explicit
  runtime mapping. Its first result took 24,653ms but failed the existing card
  linter on three multiline stop mappings. Actual validator feedback prompted
  one model repair taking 16,639ms. Both calls are included: 41,292ms,
  7,491 cache-creation input tokens, 4 ordinary input tokens and 5,926 output
  tokens; CLI-reported cost $0.094718.
- The final preparation CLI, including file creation and its real card
  validation, had a median 50.382ms across five local executions and used zero
  model calls. An earlier in-process probe was faster but is not the headline
  comparison because it excluded process startup and file I/O.
- Both final arms passed the same card gate and all three actual spawn hooks.
  Models, runtime types, exact task instructions, stop criteria and declared
  scopes matched the input. The prototype was deterministic across repeats.
- The reproducible local comparison command is:

```bash
node plugins/kkirikkiri/tests/measure-preparation.cjs \
  .omo/evidence/kkirikkiri-prepare-pilot/plan.json \
  .omo/evidence/kkirikkiri-prepare-pilot/repaired-baseline/launch.json
```

This is one tiny serialization workload. The model arm was not repeatedly
sampled; its final payloads were not separately replayed as an end-to-end
workflow A/B. Thus these observations justify eliminating model re-serialization
in the narrow opt-in path, not a general total-workflow speedup or quality gain.

## Final disposition

- Adopt the repaired local policies, session ledger identity, and new-run
  acceptance-bound completion contract.
- Retain the preparation path as opt-in only, documented in
  `skills/kkirikkiri/references/prepare-team-pilot.md`.
- Hold automatic replacement of all Teams preparation, other execution shapes,
  model-tier changes, batching changes and a cross-host orchestration rewrite.
  Their end-to-end non-inferiority is unmeasured.
- Final new suites: 28 Node cases (16 preparation + 12 completion), all passing;
  14 session hook cases, all passing.
- Existing gate suite: ALL GATES PASS. Existing routing: 15 passed, 0 failed.
  Marketplace command validation: 29 files pass; existing skill contracts:
  28 assertions pass.
- Independent review originally returned HOLD on three concrete findings.
  After corrections it approved the narrow pilot conditional on final suites.
  Those final suites have now passed.
- JavaScript/Bash/YAML LSPs were unavailable. Syntax/runtime tests and Python
  diagnostics were used; no suppressions or tool installations were added.
- Concurrent same-session ledger updates remain unserialized; approvals and
  permission restrictions remain host-managed declarations. The pilot does
  not certify trusted authorization or filesystem enforcement.
- This work did not change original main, installed caches or versions, and
  performed no project commits, merges, pushes or releases. Final observation
  found original main had advanced independently to `d0f2650` (insane-search
  v0.16.2 pointer update). The improvement worktree remains based on `463544e`;
  its kkirikkiri submodule remains based on `542afa7` with uncommitted changes.
  Do not overwrite or implicitly merge that concurrent main update.

## Subsequent authorized deployment (2026-09-06)

The user subsequently requested deployment of Kkirikkiri. This section supersedes
the pre-deployment status above, not the historical verification limits.

- Released **v0.25.0**:
  https://github.com/fivetaku/kkirikkiri/releases/tag/v0.25.0
- Plugin main/release commit:
  `f902015d1b55a87a8d68f8d3f43d6816fd4da026`.
- Feature commit `410d2e7`; executable-hook mode preservation commit `f902015`.
- Parent pointer-only commit:
  `2417a893bb99a757a6f5c3f84dbd56126db0b5ec`, based on `d0f2650`.
- Plugin CI `34028108648` and parent CI `34028164281` completed successfully.
- Marketplace clone and installed registry already synchronized through Claude's
  automatic updater. Their exact commit and version were measured before deciding
  not to overwrite the registry or recopy a correct cache.
- Cached files match marketplace source, excluding Git/runtime metadata.
  The old `0.24.6` cache was moved to Trash; `0.25.0` is the sole cached version.
- Installed `installPath`, `version`, `gitCommitSha`, and enabledPlugins agree.
- `python3 tools/gptaku_doctor.py kkirikkiri --all --network`:
  8 OK, 0 warnings, 0 failures, 0 unverified.
- Running the tests from the installed cache passed 28 Node cases and 14
  session-hook cases.
- Fresh Claude Code session `c633075c-b603-4f18-920d-f22fc0b50d60`, explicitly
  loading the installed directory, reported plugin version `0.25.0` in init
  metadata and read its manifest through the actual Read tool.
- Existing interactive Claude Code sessions were not terminated. They need
  `/reload-plugins` where supported or a restart to adopt already-loaded content.
- No other plugin's pending branch changes or private pilot fixtures were deployed.
