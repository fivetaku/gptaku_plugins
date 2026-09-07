# Installed Kkirikkiri 0.25.0 live test

## Scope

The user requested a real background Claude Code run of the deployed plugin and
a summary of the improvements' observed behavior. This was a test, not
authorization to patch or redeploy the plugin. No plugin source or installed
cache was edited in this run.

- Installed plugin:
  `/Users/chulrolee/.claude/plugins/cache/gptaku-plugins/kkirikkiri/0.25.0`.
- Isolated project: `/tmp/kkirikkiri-live-420476af`.
- Driver and raw log: `/tmp/kkirikkiri-live-420476af-evidence/`.
- Claude session: `712e9312-0ee3-4105-86a5-dbca1ef17dac`.
- Actual entry: `/kkirikkiri:kkirikkiri`, with plugin hooks enabled, explicit
  Agent Teams and opt-in preparation approval, two Sonnet producers, one Opus
  critic, and the current Claude host as coordinator.
- Ambient user/project settings were excluded, while the installed plugin was
  explicitly loaded. Existing auth was used; no credentials were copied.
- The fixture contained two throwing stubs and immutable acceptance tests.
  Its initial Git commit is a disposable fixture baseline, not a project release.

## Verdict

**Functional implementation passed; operational completion/reporting is partial.**

The two modules were implemented and all 13 tests passed both in the child host
and when independently rerun by the outer OMO session. Only the two permitted
tracked source files changed. The test file, README and .gitignore remained
unchanged.

However, the final ledger simultaneously reports successful `outcome` and
failed `outcome_gate`. Preparation needed two retries, and the host used
unnecessary scheduled wakeups instead of simply awaiting agent notifications.
The child host's statement that all improvements were fully followed is too broad.

## Observed successful behavior

| Improvement | Direct evidence |
| --- | --- |
| Installed version actually loaded | Init events identify kkirikkiri 0.25.0 at the installed cache path |
| No repeated interview for approved choices | Zero AskUserQuestion calls |
| Host remains coordinator | Three actual Agent calls: duration-builder/sonnet, slug-builder/sonnet, critic/opus; no extra Leader |
| Preparation used | Actual `prepare-team.js` invocation, resulting cards and launch.json |
| Generated instructions preserved | Each actual Agent prompt is byte-identical to the corresponding prepared prompt; model fields also match |
| Producers stay within scope | Actual worker Write calls target only src/duration.cjs and src/slug.cjs respectively |
| Critic behaves read-only | Its recorded tools: four Read, two Glob, two Grep; no Write/Edit/Bash |
| Independent verification | Critic followed both producers; host ran acceptance tests and the standalone completion checker |
| Real functional result | Baseline 0/13; final independently rerun 13/13 |
| No forced second round | One implementation round; no extra iteration after acceptance passed |
| Session-owned ledger | A single ledger has the exact session ID and three correct ownership declarations |

Read-only behavior is not proof of runtime permission restriction. The critic's
tool allowlist was declared in its prompt, not passed as an enforced tool-policy
field. Actual Agent inputs also added `name` alongside the generated fields;
that was not described as a required runtime control by the preparation tool.

## Remaining problems, in priority order

### 1. Final outcome and gate receipt disagree

The ledger's final state is:

```json
{
  "outcome": {
    "status": "success",
    "verdict": "criteria_passed",
    "rounds": 1
  },
  "outcome_gate": {
    "done_gate_exit": 1,
    "block_count": 2,
    "report": {
      "pass": false,
      "verdict": "criteria_unverified",
      "violations": [{"rule": "D4-completion-contract"}]
    }
  }
}
```

The actual sequence in `session.jsonl`:

- Line 258: completion contract was written, after agent execution and review.
- Line 288/289: manual `done-gate.js` command genuinely returned
  `criteria_passed`, with the 13-test result and artifact/report hashes.
- Line 293: the host manually changed `outcome` to success.
- The previous failed `outcome_gate` was not updated.

The failure receipt says the completion contract did not yet exist. It was
created late rather than before execution. `gate_ledger.py` selects only
ledgers with empty outcome; closing the outcome excludes the run from a later
Stop recheck. The standalone checker returns evidence but does not write the
ledger itself.

**Recommended correction:** one finalization path should validate and atomically
record the result and gate receipt before marking a run successful. Test an
initial missing-contract failure followed by repair/success, and also a failed
final recheck. Create the completion contract before launching work.

This test does not say the produced code failed: the manual checker really
passed. It shows a persisted-status consistency defect that unit tests missed.

### 2. Asynchronous waiting still creates unnecessary work

The raw trace contains three ScheduleWakeup registrations and three cancellations:

- Registration lines 138, 155, 174.
- Cancellation lines 149, 164, 180.
- All three cancellation results confirm cancellation.
- Line 183 also runs `sleep 1; echo done`.

The agent launch receipts already say completion notifications arrive
automatically. These scheduled calls were unnecessary. The host later reported
only two mistaken registrations; the trace shows three.

**Recommended correction:** give background waiting a clear host-runtime
contract; do not substitute `/loop` scheduling for agent notifications. Account
for observed waiting/repair actions in the final report rather than claiming
perfect compliance.

### 3. Preparation is deterministic, but plan assembly still retries

Actual preparation attempts:

1. Line 65/66 failed because the critic had Bash and card-incompatible stop text.
   The validator correctly blocked the invalid plan.
2. Line 91/92 failed because the requested output's parent directory was absent.
3. Line 96/97 succeeded after the parent directory was created.

**Recommended correction:** align the plan-authoring example with the accepted
critic/stop schema, and either explicitly create parent directories in the
workflow or support their creation while preserving output-overwrite refusal.
Do not weaken the critic check to hide the first failure.

This confirms that fast deterministic serialization alone does not remove the
model's plan-generation and repair cost.

### 4. Workflow roles and acceptance coverage need more accurate reporting

- Both producers executed the entire acceptance file, in addition to the host's
  executions. The fixture request assigned actual test execution to the host,
  but generated producer instructions told them to run it themselves.
- The final report said the host was the test executor without fully accounting
  for this duplication.
- The completion contract has one executable criterion, `acceptance-tests`.
  Scope preservation and actual Agent/reviewer participation were independently
  observed but not represented as executable criteria in that contract.

**Recommended correction:** assign task-local versus final integration checks
explicitly, and distinguish code-enforced criteria from manually observed
evidence. Do not equate a declared tool list with an enforced permission list.

## Runtime and evidence limits

- Log creation to its final write: approximately 436.6 seconds, about 7m17s.
  This includes startup, preparation, waiting, implementation and verification.
- Final CLI-reported total cost: $2.03379115. The same cumulative cost appears
  in three result events; it was not summed three times. This is not asserted
  to be the actual incremental subscription charge.
- Model usage identifies claude-sonnet-5 and claude-opus-5. There were three
  actual Agent launches; intermediate result events were waiting turns, not
  final task success.
- This is one deliberately small forced-team fixture, not a representative
  throughput benchmark or a before/after comparison of full workflows.
- Of 306 JSONL lines, 304 were parsed through the file-read tool. Lines 12 and
  18 are oversized SKILL Read responses exceeding the reader's 50KB single-line
  limit. All actual tool-call records and final results were readable.
- The two SKILL Read calls were a full read followed by offset 823/limit 500;
  this was continuation reading, not proven redundant full rereading.
- The raw log and child report were retained without correcting their claims.
  This audit is the authoritative interpretation of this test.

## Change boundary

Only disposable fixture and audit artifacts were created. No Kkirikkiri source
fix, version bump, release, cache replacement, or user-project change was made.
The operational findings are proposed follow-up work, not silently repaired here.
