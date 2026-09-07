# GPTaku Plugins

This repository is the Claude Code plugin marketplace. Published entries are
listed in `.claude-plugin/marketplace.json`; plugin repositories live under
`plugins/` as Git submodules. A local directory is not proof of publication.

## Changes and verification

- Keep unrelated working-tree and staged changes intact.
- Work on a separate branch or worktree; do not edit `main` as an experiment.
- Reproduce a behavioral defect before fixing it. Keep only improvements with
  passing relevant checks and evidence from the affected entry point.
- Do not bump versions until behavior is verified.
- A command file is an execution instruction. Reading a skill file supplies
  reference material; it is not proof that its tools ran.
- Pumasi tasks use the caller project's `.pumasi/pumasi.config.yaml`, never a
  configuration file inside the installed plugin.

## Release procedure

Read [docs/plugin-release.md](docs/plugin-release.md) before any release,
installation repair, or cache replacement. It is the single release procedure
for all agents. Do not duplicate its steps in agent-specific instructions.

Commits, merges, pushes, releases, and changes to an installed plugin are
separate operations; a request to inspect or edit code does not authorize them.

## Local checks

```bash
python3 tools/validate_marketplace.py
python3 tools/validate_commands.py
python3 tools/validate_skill_contracts.py
python3 tools/test_gptaku_doctor.py
```

`python3 tools/gptaku_doctor.py --all` reads the local installation. Its
`unverified` results are not successful checks or failures.
