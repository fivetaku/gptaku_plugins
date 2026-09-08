# Plugin release and installation procedure

This is the shared procedure for the Claude Code marketplace. Source revisions,
published releases, the marketplace clone, installed files, and the active
Claude Code session are different states. Report which states were verified.

Run release operations only when the user has authorized them. For an
implementation review, stop at the tested branch; do not publish or replace the
user's installed copy.

## 1. Verify the plugin change

Use the plugin's own repository and a separate working branch. Run its relevant
tests and exercise the changed entry point. Preserve unrelated work in both the
plugin and parent repository.

For a proposed performance, model-routing, or quality improvement, compare the
same task and acceptance checks before and after the change. Record output
quality, elapsed time, cost, and required user intervention where applicable.
Reject changes that introduce a demonstrated regression; a passing unit suite
alone does not establish a quality or performance benefit. Do not promote a
private pilot threshold into a marketplace-wide requirement.

Only after verification, update `.claude-plugin/plugin.json` and the plugin's
release documentation to the same new version. Inspect the staged diff before
committing. A release must not include unrelated staged changes.

## 2. Publish the plugin revision and release

After an authorized merge and push, identify the exact tested commit. Create the
release in the plugin repository, not the parent marketplace repository.

```bash
# ROOT is the parent repository; PLUGIN is the selected plugin name.
SUB="$ROOT/plugins/$PLUGIN"
SHA=$(git -C "$SUB" rev-parse HEAD)
VERSION=$(git -C "$SUB" show "$SHA:.claude-plugin/plugin.json" |
  python3 -c 'import json, sys; print(json.load(sys.stdin)["version"])')
gh -R "fivetaku/$PLUGIN" release create "v$VERSION" \
  --target "$SHA" --title "v$VERSION" --notes-file "$RELEASE_NOTES"
```

The `v<version>` tag must identify the tested commit. If that version already
exists, stop and inspect it; do not delete or move a published tag as a retry.

## 3. Update the parent pointer

Stage only `plugins/<plugin-name>` in the parent repository. Inspect the entire
parent staged diff before an authorized commit and push. The parent gitlink must
match the plugin commit from step 2.

New in-tree or private plugins need an explicit publication decision. Do not
add their directories to the public marketplace just because they exist locally.

## 4. Synchronize the marketplace clone

The Claude Code marketplace clone is
`~/.claude/plugins/marketplaces/gptaku-plugins`.

```bash
MARKET="$HOME/.claude/plugins/marketplaces/gptaku-plugins"
git -C "$MARKET" pull --ff-only
git -C "$MARKET" submodule update --init "plugins/$PLUGIN"
```

Confirm that the clone contains the intended parent revision and plugin pointer.
Do not treat a matching version string as proof of matching contents.

## 5. Prepare and verify the cache

Prefer Claude Code's normal plugin installation/update flow. If a manual repair
is necessary, use `~/.claude/plugins/cache/gptaku-plugins/<plugin>/<version>`.
Never use `.Codex` paths for this marketplace.

Prepare a fresh staging directory before replacing a working installation.
Copy the source directory's contents with `/.` so hidden entries are retained.

```bash
SRC="$MARKET/plugins/$PLUGIN"
STAGING=$(mktemp -d)
cp -R "$SRC/." "$STAGING/"
# A copied submodule .git pointer does not belong in an installation cache.
if test -e "$STAGING/.git"; then
  trash "$STAGING/.git"
fi
diff -rq --exclude=.git "$SRC" "$STAGING"
```

Inspect `.claude-plugin/plugin.json` in staging and require the diff to succeed.
Only then replace the selected cache with the verified staging contents. Do not
overlay an old cache, because files removed from the source could remain there.
Retain only the intended version after the replacement succeeds. Removing old
copies is an authorized installation operation, not part of code verification.

## 6. Match installation metadata and enablement

In `~/.claude/plugins/installed_plugins.json`, the selected plugin entry's
`installPath`, `version`, and `gitCommitSha` must agree with the installed files
and step 2's exact commit. Update `lastUpdated` as part of the installation.

On a manual first installation, also check
`~/.claude/settings.json` -> `enabledPlugins` ->
`"<plugin>@gptaku-plugins"`. A missing entry can leave files installed without
loading their hooks or skills. An explicitly disabled plugin is not a missing
installation; preserve the user's choice.

## 7. Verify the resulting installation

```bash
python3 "$ROOT/tools/gptaku_doctor.py" "$PLUGIN" --all
# Add --network when release-tag verification is part of the authorized check.
```

Check enablement, cache versions, hidden manifest, version metadata, marketplace
revision/content, hook files, and release identity. Report `unverified` as
unverified, not as passed or absent. Exercise the changed command or hook in a
fresh Claude Code session before reporting the installation as operational.

## 8. Activate the installed version

For a normal plugin installation/update, use `/reload-plugins` when supported by
the running Claude Code version, then verify the changed behavior. If a manual
cache replacement or an already-loaded hook does not refresh, restart Claude
Code and repeat the affected command or hook.

A passing filesystem diagnosis does not prove an existing session has loaded
the new code. State the version and the session behavior that were checked.
