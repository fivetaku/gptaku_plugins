#!/bin/bash
# 플러그인 서브모듈 릴리즈 워크플로
#
# 전제: worktree에서 작업 완료 → 서브모듈 브랜치에 커밋이 쌓인 상태
# 하는 일: 서브모듈 머지 → 부모 포인터 갱신·커밋 → (선택) 각 레포 푸시
# GitHub release/tag 생성, marketplace/cache 동기화, 세션 활성화는 하지 않음.
#
# 사용:
#   plugin-release.sh <플러그인명> <작업브랜치> [--push]
#   예: plugin-release.sh pumasi feat/cursor-worker --push
set -euo pipefail

fail() { echo "ERROR: $*" >&2; exit 1; }

[ "$#" -ge 2 ] && [ "$#" -le 3 ] || fail "Usage: $0 <plugin> <branch> [--push]"
PLUGIN="$1"
BRANCH="$2"
PUSH="${3:-}"
[ "$#" -eq 2 ] || [ "$PUSH" = "--push" ] || fail "Unknown option: $PUSH"
[[ "$PLUGIN" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || fail "Invalid plugin name: $PLUGIN"
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
SUB="$ROOT/plugins/$PLUGIN"

# Refuse the entire pre-existing parent index before checkout/merge/push in the plugin.
[ "$(git -C "$ROOT" rev-parse --show-toplevel)" = "$ROOT" ] || fail "Script must be in the parent repository's scripts directory"
[ "$(git -C "$ROOT" symbolic-ref -q HEAD)" = "refs/heads/main" ] || fail "Parent must be on main (not detached)"
git -C "$ROOT" diff --cached --quiet --ignore-submodules=none || fail "Parent has staged changes; commit or unstage them first"
[ "$(git -C "$ROOT" ls-files --stage -- "plugins/$PLUGIN" | awk '{print $1}')" = "160000" ] || fail "$PLUGIN is not a tracked submodule"
[ -d "$SUB/.git" ] || [ -f "$SUB/.git" ] || fail "$SUB is not initialized"
[ "$(git -C "$SUB" rev-parse --show-toplevel)" = "$SUB" ] || fail "Unexpected plugin repository root"

for REPO in "$ROOT" "$SUB"; do
  for STATE in MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD rebase-merge rebase-apply sequencer; do
    [ ! -e "$(git -C "$REPO" rev-parse --path-format=absolute --git-path "$STATE")" ] || fail "Unfinished Git operation in $REPO ($STATE)"
  done
done

echo "▶ 1/6 서브모듈 상태 점검 ($PLUGIN)"
cd "$SUB"
git check-ref-format "refs/heads/$BRANCH" || fail "Invalid branch: $BRANCH"
git show-ref --verify --quiet "refs/heads/$BRANCH" || fail "Local branch $BRANCH does not exist"
git show-ref --verify --quiet refs/heads/main || fail "Plugin main branch does not exist"
CURRENT="$(git symbolic-ref -q HEAD)" || fail "Plugin must not be detached"
[ "$CURRENT" = "refs/heads/main" ] || [ "$CURRENT" = "refs/heads/$BRANCH" ] || fail "Plugin must be on main or $BRANCH"
[ -z "$(git status --porcelain --untracked-files=all --ignore-submodules=none)" ] || fail "Plugin has uncommitted changes; commit or stash them first"
command -v python3 >/dev/null || fail "python3 is required"

echo "▶ 2/6 서브모듈 머지 ($BRANCH → main)"
git checkout main -q
git merge --no-ff --no-commit "refs/heads/$BRANCH" -q

echo "▶ 3/6 머지 결과 버전 확인 및 커밋"
# Validate the merged index, not the manifest from the previously checked-out branch.
VER=$(git show :.claude-plugin/plugin.json | python3 -c '
import json, re, sys
manifest = json.load(sys.stdin)
version = manifest.get("version") if isinstance(manifest, dict) else None
pattern = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?"
if not isinstance(version, str) or not re.fullmatch(pattern, version):
    sys.exit("ERROR: merged plugin.json requires a semantic version string")
print(version)
') || fail "Merged manifest validation failed; no release commit/push made. Inspect the plugin merge; use git merge --abort to cancel a pending merge."
echo "   plugin.json version = $VER"
grep -Fq "## $VER" CHANGELOG.md 2>/dev/null || echo "   ⚠ CHANGELOG.md에 '## $VER' 항목이 없음 — 확인 권장"
if git rev-parse --verify -q MERGE_HEAD >/dev/null; then
  git commit -q -m "merge $BRANCH (v$VER)"
fi
echo "   머지 완료: $(git log --oneline -1)"

echo "▶ 4/6 서브모듈 푸시"
if [ "$PUSH" = "--push" ]; then
  git push origin main -q && echo "   pushed"
else
  echo "   (건너뜀 — --push 없음)"
fi

echo "▶ 5/6 부모 레포 포인터 갱신"
cd "$ROOT"
git add -- "plugins/$PLUGIN"
if git diff --cached --quiet --ignore-submodules=none; then
  echo "   포인터 변화 없음 (이미 최신)"
else
  git commit -q --only -m "chore: update $PLUGIN submodule to v$VER" -- "plugins/$PLUGIN"
  echo "   $(git log --oneline -1)"
fi

echo "▶ 6/6 부모 푸시"
if [ "$PUSH" = "--push" ]; then
  git push origin main -q && echo "   pushed"
else
  echo "   (건너뜀 — --push 없음)"
fi

echo
echo "✅ Merge and parent-pointer workflow complete (push only with --push)."
echo "   NOT completed: GitHub release/tag creation, marketplace/cache synchronization, or session activation."
echo "   Follow docs/plugin-release.md for the separate release and installation steps."
