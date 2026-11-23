#!/bin/bash
# Codex 설치 대조 (AC-01.3, AC-09.2, 가정 A-01). 새 격리 CODEX_HOME에 마켓을 등록하고 플러그인을 설치한 뒤,
#  1) Codex가 읽은 마켓 파일이 .agents/plugins/marketplace.json인지(`codex plugin list` 첫머리),
#  2) 설치한 캐시의 파일 목록이 마켓 항목이 가리키는 태그(url·path·ref)의 파일 목록과 같은지(빈 껍데기 아님)
# 를 본다. 하나라도 어긋나면 종료 코드 1.
# 사용: install_check.sh --source <git URL | owner/repo | 로컬 경로> [--ref <마켓 ref>] [--all | <plugin>...]
set -u
STATE=${CODEX_SMOKE_STATE:-$HOME/gptaku-codex-merge-state/smoke}
TMPL=${CODEX_SMOKE_TMPL:-$HOME/gptaku-codex-merge-state/smoke-tmpl}
SRC=""; MREF=""; ALL=0; NAMES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --source) SRC="$2"; shift ;;
    --ref) MREF="$2"; shift ;;
    --all) ALL=1 ;;
    *) NAMES+=("$1") ;;
  esac
  shift
done
[ -n "$SRC" ] || { echo "usage: install_check.sh --source <src> [--ref r] [--all | plugin...]"; exit 2; }
D="$STATE/install-$(date +%Y%m%d-%H%M%S)-$$"; H="$D/home"; mkdir -p "$H"
cp "$TMPL/config.toml" "$H/"
if [ -n "$MREF" ]; then CODEX_HOME="$H" codex plugin marketplace add "$SRC" --ref "$MREF" > "$D/add.log" 2>&1
else CODEX_HOME="$H" codex plugin marketplace add "$SRC" > "$D/add.log" 2>&1; fi
rc=$?; cat "$D/add.log"; [ $rc -eq 0 ] || { echo "FAIL marketplace add rc=$rc"; exit 1; }
CODEX_HOME="$H" codex plugin list > "$D/list.txt" 2>&1
MFILE=$(awk '/^Marketplace `gptaku-plugins`/{getline; print; exit}' "$D/list.txt")
echo "Codex가 읽은 마켓 파일: $MFILE"
case "$MFILE" in */.agents/plugins/marketplace.json) ;; *) echo "FAIL .agents 마켓을 읽지 않음 (A-01)"; exit 1 ;; esac
if [ $ALL -eq 1 ] || [ ${#NAMES[@]} -eq 0 ]; then
  NAMES=($(python3 -c "import json,sys;print(' '.join(p['name'] for p in json.load(open(sys.argv[1]))['plugins']))" "$MFILE"))
fi
echo "대상 ${#NAMES[@]}개: ${NAMES[*]}"
for p in "${NAMES[@]}"; do CODEX_HOME="$H" codex plugin add "$p@gptaku-plugins" >> "$D/install.log" 2>&1 || echo "install rc!=0 $p" >> "$D/install.log"; done
CODEX_HOME="$H" codex plugin list --json > "$D/list.json" 2>&1
python3 - "$D" "$H" "${NAMES[@]}" <<'PY'
import json, os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
d, home, names = sys.argv[1], sys.argv[2], sys.argv[3:]
inst = {x["name"]: x for x in json.load(open(os.path.join(d, "list.json")))["installed"]}

def files(root):
    out = set()
    for r, dirs, fs in os.walk(root):
        dirs[:] = [x for x in dirs if x != ".git"]
        for f in fs:
            out.add(os.path.relpath(os.path.join(r, f), root))
    return out

def one(n):
    x = inst.get(n)
    if not x or not x.get("installed"):
        return n, False, "설치 안 됨"
    src = x["source"]
    cache = os.path.join(home, "plugins", "cache", "gptaku-plugins", n, x["version"])
    if not os.path.isdir(cache):
        return n, False, f"캐시 없음 {cache}"
    with tempfile.TemporaryDirectory() as t:
        r = subprocess.run(["git", "clone", "-q", "--depth", "1", "--branch", src["ref"], src["url"], t + "/r"],
                           capture_output=True, text=True)
        if r.returncode:
            return n, False, f"태그 clone 실패 {src['ref']}: {r.stderr.strip()[:120]}"
        want = files(os.path.join(t, "r", src.get("path") or ""))
    got = files(cache)
    if ".claude-plugin/plugin.json" not in got:
        return n, False, f"빈 껍데기(plugin.json 없음, 파일 {len(got)}개)"
    # Codex는 설치할 때 4KB 이하·$ARGUMENTS 없는 commands/<c>.md를 스킬로 바꿔
    # .codex-plugin/migrated-command-skills/source-command-<c>/SKILL.md를 만든다(레포 내용이 아님).
    # 태그에 그 명령 파일이 있을 때만 그 생성물을 비교에서 뺀다.
    made = {f for f in got - want
            if re.fullmatch(r"\.codex-plugin/migrated-command-skills/source-command-([^/]+)/SKILL\.md", f)
            and f"commands/{f.split('/')[2][len('source-command-'):]}.md" in want}
    got -= made
    if want != got:
        miss, extra = sorted(want - got)[:5], sorted(got - want)[:5]
        return n, False, f"파일 목록 다름 — 빠짐 {miss} 더 있음 {extra}"
    note = f" (+Codex가 명령에서 만든 스킬 {len(made)}개)" if made else ""
    return n, True, f"{src['ref']} 파일 {len(got)}개 일치{note}"

with ThreadPoolExecutor(8) as ex:
    res = list(ex.map(one, names))
bad = 0
for n, ok, why in res:
    print(f"{'OK  ' if ok else 'FAIL'} {n:18} {why}")
    bad += not ok
print(f"\n결과: 일치 {len(res) - bad} / {len(res)}  (기록 {d})")
sys.exit(1 if bad or not res else 0)
PY
