#!/bin/bash
# 플러그인 서브모듈 릴리즈 워크플로
#
# 전제: worktree에서 작업 완료 → 서브모듈 브랜치에 커밋이 쌓인 상태
# 하는 일: 서브모듈 머지·푸시 → 부모 포인터 갱신·커밋 → (선택) 푸시
#
# 사용:
#   plugin-release.sh <플러그인명> <작업브랜치> [--push]
#   예: plugin-release.sh pumasi feat/cursor-worker --push
set -euo pipefail

PLUGIN="${1:?플러그인명 필요 (예: pumasi)}"
BRANCH="${2:?작업 브랜치 필요 (예: feat/xxx)}"
PUSH="${3:-}"
ROOT="$HOME/gptaku_plugins"
SUB="$ROOT/plugins/$PLUGIN"

[ -d "$SUB/.git" ] || [ -f "$SUB/.git" ] || { echo "ERROR: $SUB 는 서브모듈이 아님"; exit 1; }

echo "▶ 1/6 서브모듈 상태 점검 ($PLUGIN)"
cd "$SUB"
git rev-parse --verify "$BRANCH" >/dev/null 2>&1 || { echo "ERROR: 브랜치 $BRANCH 없음"; exit 1; }
DIRTY=$(git status --porcelain | wc -l | tr -d ' ')
[ "$DIRTY" = "0" ] || { echo "ERROR: 서브모듈에 미커밋 $DIRTY개 — 먼저 커밋하거나 stash"; git status --short | head -5; exit 1; }

echo "▶ 2/6 버전 확인"
VER=$(python3 -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'])" 2>/dev/null || echo "?")
echo "   plugin.json version = $VER"
grep -q "^## $VER" CHANGELOG.md 2>/dev/null || echo "   ⚠ CHANGELOG.md에 '## $VER' 항목이 없음 — 확인 권장"

echo "▶ 3/6 서브모듈 머지 ($BRANCH → main)"
git checkout main -q
git merge --no-ff "$BRANCH" -m "merge $BRANCH (v$VER)" -q
echo "   머지 완료: $(git log --oneline -1)"

echo "▶ 4/6 서브모듈 푸시"
if [ "$PUSH" = "--push" ]; then
  git push origin main -q && echo "   pushed"
else
  echo "   (건너뜀 — --push 없음)"
fi

echo "▶ 5/6 부모 레포 포인터 갱신"
cd "$ROOT"
git add "plugins/$PLUGIN"
if git diff --cached --quiet; then
  echo "   포인터 변화 없음 (이미 최신)"
else
  git commit -q -m "chore: update $PLUGIN submodule to v$VER"
  echo "   $(git log --oneline -1)"
fi

echo "▶ 6/6 부모 푸시"
if [ "$PUSH" = "--push" ]; then
  git push origin main -q && echo "   pushed"
else
  echo "   (건너뜀 — --push 없음)"
fi

echo
echo "✅ 완료. 정리하려면:"
echo "   cd $SUB && git branch -d $BRANCH"
echo "   Paseo 워크스페이스는 앱에서 archive"
