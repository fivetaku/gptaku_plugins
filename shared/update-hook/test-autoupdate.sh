#!/usr/bin/env bash
# Offline test for the gptaku-plugins auto-update consent flow and notifier hint.
#   - renders setup.sh.template into a temp dir
#   - runs it with HOME and CLAUDE_CONFIG_DIR pointed at throwaway temp dirs
#     (never touches the real ~/.claude or ~/.gptaku-setup)
#   - checks that "autoupdate yes" flips ONLY gptaku-plugins.autoUpdate and preserves every
#     other key/entry, backs up first, writes atomically, and asks at most once
#   - checks the SessionStart notifier drops the auto-update hint when it is already on
# Exit code 0 = all checks passed, 1 = at least one failed.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE="$HERE/setup.sh.template"
CJS="$HERE/gptaku-update-check.cjs"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/gptaku-autoupdate-test.XXXXXX")"
cleanup() { if command -v trash >/dev/null 2>&1; then trash "$WORK" 2>/dev/null; else rm -r -f "$WORK"; fi; }
trap cleanup EXIT

PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "  ok   - $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  FAIL - $1"; }
check() { if eval "$2"; then ok "$1"; else bad "$1"; fi; }

SETUP="$WORK/bin/setup.sh"
mkdir -p "$WORK/bin"
sed -e "s|__PLUGIN__|testplug|g" -e "s|__OWN_REPO__|example/testplug|g" "$TEMPLATE" > "$SETUP"
chmod +x "$SETUP"
cp "$CJS" "$WORK/bin/gptaku-update-check.cjs"

# fresh isolated env: $1 = name, $2 = known_marketplaces.json content ('' = no file)
new_env() {
  E="$WORK/$1"; mkdir -p "$E/home/.claude/plugins"
  export HOME="$E/home" CLAUDE_CONFIG_DIR="$E/home/.claude"
  KM="$CLAUDE_CONFIG_DIR/plugins/known_marketplaces.json"
  MARK="$HOME/.gptaku-setup/gptaku-plugins.autoupdate.json"
  [ -n "$2" ] && printf '%s\n' "$2" > "$KM" && chmod 600 "$KM"
  return 0
}
run() { bash "$SETUP" "$@" 2>&1; }

SAMPLE='{
  "claude-dashboard": {"source": {"source": "github", "repo": "uppinote20/claude-dashboard"},
    "installLocation": "/x/claude-dashboard", "lastUpdated": "2026-09-12T15:42:05.339Z", "autoUpdate": false},
  "gptaku-plugins": {"source": {"source": "git", "url": "https://github.com/fivetaku/gptaku_plugins.git"},
    "installLocation": "/x/gptaku-plugins", "lastUpdated": "2026-11-18T08:20:19.780Z",
    "futureKey": {"nested": [1, 2, "삼"]}},
  "fablize": {"source": {"source": "directory", "path": "/x/fablize"}, "installLocation": "/x/fablize",
    "lastUpdated": "2026-11-22T06:53:19.457Z"}
}'

# Python comparator: everything except gptaku-plugins.autoUpdate must be identical.
cmp_preserved() {  # $1 original file, $2 new file
  python3 - "$1" "$2" <<'PY'
import json, sys
a = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2]))
if set(a) != set(b): sys.exit("entry set changed")
for k in a:
    x, y = dict(a[k]), dict(b[k])
    if k == "gptaku-plugins":
        if y.pop("autoUpdate", None) is not True: sys.exit("autoUpdate not true")
        x.pop("autoUpdate", None)
    if x != y: sys.exit("entry %s changed" % k)
PY
}

echo "# 1. plain 'ask' never emits AUTOUPDATE_ASK nor burns the marker"
new_env t1 "$SAMPLE"
OUT=$(run ask)
check "no AUTOUPDATE_ASK on plain ask" '! printf "%s" "$OUT" | grep -q AUTOUPDATE_ASK'
check "STAR_ASK still emitted on plain ask" 'printf "%s" "$OUT" | grep -q "^STAR_ASK "'
check "no autoupdate marker after plain ask" '[ ! -f "$MARK" ]'

echo "# 2. 'ask autoupdate' asks exactly once"
OUT=$(run ask autoupdate)
check "AUTOUPDATE_ASK emitted with lang" 'printf "%s" "$OUT" | grep -Eq "^AUTOUPDATE_ASK (ko|ja|en)$"'
check "marker records asked" 'grep -q "\"autoupdate_decision\":\"asked\"" "$MARK"'
OUT=$(run ask autoupdate)
check "second ask autoupdate is silent" '[ -z "$OUT" ]'

echo "# 3. 'autoupdate yes' flips only gptaku-plugins.autoUpdate"
cp "$KM" "$WORK/t1.orig.json"
OUT=$(run autoupdate yes)
check "prints AUTOUPDATE_SET on" '[ "$OUT" = "AUTOUPDATE_SET on" ]'
check "all other keys/entries preserved" 'cmp_preserved "$WORK/t1.orig.json" "$KM"'
BK=$(ls "$KM".bak-gptaku-autoupdate-* 2>/dev/null | head -1)
check "backup created and identical to original" '[ -n "$BK" ] && cmp -s "$BK" "$WORK/t1.orig.json"'
check "file mode preserved (600)" '[ "$(stat -f %Lp "$KM" 2>/dev/null || stat -c %a "$KM")" = "600" ]'
check "no temp file left behind" '[ -z "$(ls -A "$CLAUDE_CONFIG_DIR/plugins" | grep "^\.known_marketplaces\.")" ]'
check "marker records yes/on" 'grep -q "\"autoupdate_decision\":\"yes\",\"result\":\"on\"" "$MARK"'
OUT=$(run autoupdate yes)
check "re-running yes is idempotent (already)" '[ "$OUT" = "AUTOUPDATE_SET already" ]'
check "still only one backup" '[ "$(ls "$KM".bak-gptaku-autoupdate-* | wc -l | tr -d " ")" = "1" ]'

echo "# 4. 'autoupdate no' changes nothing"
new_env t4 "$SAMPLE"; cp "$KM" "$WORK/t4.orig.json"
OUT=$(run autoupdate no)
check "prints AUTOUPDATE_SET skipped" '[ "$OUT" = "AUTOUPDATE_SET skipped" ]'
check "file byte-identical" 'cmp -s "$KM" "$WORK/t4.orig.json"'
check "marker records no" 'grep -q "\"autoupdate_decision\":\"no\"" "$MARK"'
check "no backup on no" '! ls "$KM".bak-gptaku-autoupdate-* >/dev/null 2>&1'

echo "# 5. no gptaku-plugins entry (e.g. --plugin-dir install): never ask, never write"
new_env t5 '{"other": {"source": {"source": "github", "repo": "a/b"}, "installLocation": "/x"}}'
cp "$KM" "$WORK/t5.orig.json"
OUT=$(run ask autoupdate)
check "no AUTOUPDATE_ASK without entry" '! printf "%s" "$OUT" | grep -q AUTOUPDATE_ASK'
check "no marker without entry" '[ ! -f "$MARK" ]'
OUT=$(run autoupdate yes)
check "yes reports missing" '[ "$OUT" = "AUTOUPDATE_SET missing" ]'
check "file unchanged when entry missing" 'cmp -s "$KM" "$WORK/t5.orig.json"'
new_env t5b ''
OUT=$(run autoupdate yes)
check "no known_marketplaces.json -> missing, nothing created" '[ "$OUT" = "AUTOUPDATE_SET missing" ] && [ ! -f "$KM" ]'

echo "# 6. user settings declares autoUpdate:false -> respect it"
new_env t6 "$SAMPLE"; cp "$KM" "$WORK/t6.orig.json"
printf '{"extraKnownMarketplaces":{"gptaku-plugins":{"source":{"source":"git","url":"x"},"autoUpdate":false}}}\n' > "$CLAUDE_CONFIG_DIR/settings.json"
OUT=$(run autoupdate yes)
check "reports overridden-by-settings" '[ "$OUT" = "AUTOUPDATE_SET overridden-by-settings" ]'
check "file unchanged" 'cmp -s "$KM" "$WORK/t6.orig.json"'

echo "# 7. already on -> ask autoupdate records already-on and stays silent"
new_env t7 "$(printf '%s' "$SAMPLE" | python3 -c 'import json,sys; d=json.load(sys.stdin); d["gptaku-plugins"]["autoUpdate"]=True; print(json.dumps(d))')"
OUT=$(run ask autoupdate)
check "no AUTOUPDATE_ASK when already on" '! printf "%s" "$OUT" | grep -q AUTOUPDATE_ASK'
check "marker records already-on" 'grep -q "\"autoupdate_decision\":\"already-on\"" "$MARK"'

echo "# 8. Claude Code CLI still parses the file written in step 3 (read-only listing)"
if command -v claude >/dev/null 2>&1; then
  export HOME="$WORK/t1/home" CLAUDE_CONFIG_DIR="$WORK/t1/home/.claude"
  LJ=$(claude plugin marketplace list --json 2>/dev/null); RC=$?
  check "claude plugin marketplace list --json exit 0 and lists gptaku-plugins" \
    '[ $RC -eq 0 ] && printf "%s" "$LJ" | grep -q "\"gptaku-plugins\""'
  python3 -c 'import json,sys; assert json.load(open(sys.argv[1]))["gptaku-plugins"]["autoUpdate"] is True' "$CLAUDE_CONFIG_DIR/plugins/known_marketplaces.json" \
    && ok "CLI did not strip autoUpdate" || bad "CLI did not strip autoUpdate"
else
  echo "  skip - claude CLI not on PATH"
fi

echo "# 9. notifier hint: shown when auto-update is off, hidden when on"
if command -v node >/dev/null 2>&1 && command -v git >/dev/null 2>&1; then
  N="$WORK/notifier"; mkdir -p "$N"
  git init -q --bare "$N/remote.git"
  git clone -q "$N/remote.git" "$N/seed" 2>/dev/null
  git -C "$N/seed" -c user.name=t -c user.email=t@t commit -q --allow-empty -m one
  git -C "$N/seed" push -q origin HEAD 2>/dev/null
  # local clones are made first, then a new remote commit is pushed -> clones are behind
  mkdir -p "$N/cfg-false/plugins/marketplaces" "$N/cfg-true/plugins/marketplaces"
  for v in false true; do
    git clone -q "$N/remote.git" "$N/cfg-$v/plugins/marketplaces/gptaku-plugins" 2>/dev/null
    printf '{"gptaku-plugins":{"source":{"source":"git","url":"x"},"installLocation":"x","autoUpdate":%s}}\n' "$v" > "$N/cfg-$v/plugins/known_marketplaces.json"
  done
  git -C "$N/seed" -c user.name=t -c user.email=t@t commit -q --allow-empty -m two
  git -C "$N/seed" push -q origin HEAD 2>/dev/null
  ctx() { echo '{}' | CLAUDE_CONFIG_DIR="$N/cfg-$1" node "$WORK/bin/gptaku-update-check.cjs" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin).get("hookSpecificOutput",{}).get("additionalContext",""))'; }
  OFF=$(ctx false); ON=$(ctx true)
  echo "    [off] $OFF"
  echo "    [on ] $ON"
  check "off: names the update command" 'printf "%s" "$OFF" | grep -qF "/plugin marketplace update gptaku-plugins"'
  check "off: includes auto-update hint" 'printf "%s" "$OFF" | grep -qF "Turn on auto-update"'
  check "on: still names the update command" 'printf "%s" "$ON" | grep -qF "/plugin marketplace update gptaku-plugins"'
  check "on: omits auto-update hint" '! printf "%s" "$ON" | grep -qF "Turn on auto-update"'
else
  echo "  skip - node or git not available"
fi

echo "# 10. settings.json corruption guard (first run)"
check "template carries the guard" 'grep -q "process.exit(0)" "$TEMPLATE" && grep -q "renameSync(tmp,p)" "$TEMPLATE"'
if command -v node >/dev/null 2>&1; then
  new_env t10a ''
  printf '{ "model": "x", // jsonc comment\n  "hooks": {} }\n' > "$CLAUDE_CONFIG_DIR/settings.json"
  cp "$CLAUDE_CONFIG_DIR/settings.json" "$WORK/t10a.orig"
  run >/dev/null
  check "unparseable settings.json left byte-identical" 'cmp -s "$CLAUDE_CONFIG_DIR/settings.json" "$WORK/t10a.orig"'
  check "first-run marker still written" '[ -f "$HOME/.gptaku-setup/testplug.json" ]'
  new_env t10b ''
  printf '[1,2]\n' > "$CLAUDE_CONFIG_DIR/settings.json"
  run >/dev/null
  check "non-object settings.json left untouched" '[ "$(cat "$CLAUDE_CONFIG_DIR/settings.json")" = "[1,2]" ]'
  new_env t10c ''
  printf '{"model":"keep-me","hooks":{"Stop":[{"hooks":[{"type":"command","command":"x"}]}]}}\n' > "$CLAUDE_CONFIG_DIR/settings.json"
  run >/dev/null
  check "valid settings.json: hook added, other keys preserved, no temp left" 'python3 -c "
import json,sys; d=json.load(open(sys.argv[1]))
assert d[\"model\"]==\"keep-me\" and d[\"hooks\"][\"Stop\"]
assert any(\"gptaku-update-check\" in h[\"command\"] for e in d[\"hooks\"][\"SessionStart\"] for h in e[\"hooks\"])
" "$CLAUDE_CONFIG_DIR/settings.json" && [ -z "$(ls -A "$CLAUDE_CONFIG_DIR" | grep "tmp-gptaku")" ]'
  check "first run installed the notifier script" 'cmp -s "$CLAUDE_CONFIG_DIR/scripts/gptaku-update-check.cjs" "$CJS"'
  new_env t10d ''
  run >/dev/null
  check "missing settings.json: created with the hook" 'grep -q gptaku-update-check "$CLAUDE_CONFIG_DIR/settings.json"'
else
  echo "  skip - node not available"
fi

echo "# 11. every-run refresh of an installed notifier script"
BREV=$(sed -n 's/.*gptaku-update-check-rev: *\([0-9][0-9]*\).*/\1/p' "$CJS" | head -n 1)
check "canonical cjs carries a numeric rev" '[ -n "$BREV" ]'
# installed-before env: setup marker present (first-run block skipped) + settings snapshot
prep_installed() {  # $1 = env name, $2 = installed cjs content ('' = not installed)
  new_env "$1" "$SAMPLE"
  mkdir -p "$HOME/.gptaku-setup" "$CLAUDE_CONFIG_DIR/scripts"
  printf '{"setup":true,"plugin":"testplug","ts":1}\n' > "$HOME/.gptaku-setup/testplug.json"
  printf '{"hooks":{}}\n' > "$CLAUDE_CONFIG_DIR/settings.json"
  cp "$CLAUDE_CONFIG_DIR/settings.json" "$WORK/$1.settings"
  DST="$CLAUDE_CONFIG_DIR/scripts/gptaku-update-check.cjs"
  [ -n "$2" ] && printf '%s\n' "$2" > "$DST"
  return 0
}
prep_installed t11a "// old notifier text, gptaku-update-check-rev: 1"
OUT=$(run)
check "older rev is refreshed to bundled copy" 'cmp -s "$DST" "$CJS"'
check "refresh is silent" '[ -z "$OUT" ]'
check "refresh never touches settings.json" 'cmp -s "$CLAUDE_CONFIG_DIR/settings.json" "$WORK/t11a.settings"'
check "no temp file left in scripts/" '[ "$(ls -A "$CLAUDE_CONFIG_DIR/scripts")" = "gptaku-update-check.cjs" ]'
prep_installed t11b "// legacy notifier without any rev marker"
run star no >/dev/null
check "legacy (no rev) copy refreshed, also in star mode" 'cmp -s "$DST" "$CJS"'
prep_installed t11c ""
run >/dev/null
check "not installed before -> nothing created" '[ ! -e "$DST" ]'
check "not installed: settings.json untouched" 'cmp -s "$CLAUDE_CONFIG_DIR/settings.json" "$WORK/t11c.settings"'
prep_installed t11d "// newer notifier, gptaku-update-check-rev: 9999999999"
cp "$DST" "$WORK/t11d.cjs"
run >/dev/null
check "newer installed rev is never downgraded" 'cmp -s "$DST" "$WORK/t11d.cjs"'
prep_installed t11e "$(cat "$CJS")"
OUT=$(run ask autoupdate)
check "identical copy: no-op, ask flow unaffected" 'cmp -s "$DST" "$CJS" && printf "%s" "$OUT" | grep -q "^AUTOUPDATE_ASK "'

echo
echo "passed: $PASS  failed: $FAIL"
[ "$FAIL" -eq 0 ]
