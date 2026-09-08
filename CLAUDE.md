# gptaku-plugins 마켓플레이스

## 프로젝트 구조

```
gptaku_plugins/           # 마켓플레이스 (parent repo)
  plugins/                # 각 플러그인은 git submodule (신규는 in-tree 임시 허용)
    dd/                   # 클립보드 드롭 (/dd, /ㅇㅇ)
    ddiring/              # 멀티세션 완료 알림 (띠링)
    docs-guide/
    gaseo/                # Paseo 세션 등록
    git-teacher/
    goaljaby/
    insane-design/
    insane-research/
    insane-review/        # GPT Pro 웹 브릿지 코드 리뷰
    insane-search/
    kkirikkiri/
    nopal/
    pumasi/
    sangse/               # 상세페이지 컷 시트 제작 (/sangse)
    show-me-the-prd/
    skillers-suda/
    tikeytaka/            # API 키 중앙 볼트
    vibe-sunsang/
    # 이외 in-tree WIP/프라이빗: insane-crawl(WIP), insane-slide·insane-video(프라이빗, gitignore)
```

## 플러그인 버전 업데이트 체크리스트

플러그인 코드를 수정하고 버전을 올릴 때 반드시 아래 순서를 따른다.
**하나라도 빠지면 캐시 불일치로 구버전이 로드된다.**

### Step 1: 서브모듈 내에서 작업

```bash
cd plugins/<plugin-name>
# 코드 수정 완료 후
# 1) plugin.json 버전 업데이트
# 2) git add + commit + push
```

### Step 2: 서브모듈에 GitHub 릴리즈 생성

플러그인은 각자 자기 레포(서브모듈)이므로 **릴리즈도 서브모듈 레포에** 단다.
버전 bump 커밋을 push한 직후, 그 커밋을 가리키는 태그 + 릴리즈를 만든다.

```bash
cd plugins/<plugin-name>
# tag(v<new-version>)는 gh가 자동 생성한다. 별도 git tag 불필요.
gh release create v<new-version> \
  --title "v<new-version> — <한 줄 요약>" \
  --notes "<변경 내용 요약 (커밋 메시지 재활용 가능)>" \
  --target main
```

- 태그 컨벤션: `v<plugin.json의 version>` (예: `v0.21.3`). plugin.json 버전과 **반드시 일치**.
- 이미 같은 태그가 있으면 실패하므로, 재릴리즈가 필요하면 `gh release delete v<ver> --cleanup-tag` 후 다시 생성한다.

### Step 3: 부모 저장소에서 서브모듈 포인터 업데이트

```bash
cd /Users/chulrolee/gptaku_plugins
git add plugins/<plugin-name>
git commit -m "chore: update <plugin-name> submodule to v<new-version>"
git push
```

### Step 4: 마켓플레이스 클론 동기화

```bash
cd ~/.claude/plugins/marketplaces/gptaku-plugins
git pull
git submodule update --init plugins/<plugin-name>
```

### Step 5: 캐시 교체

```bash
# 1) 이전 버전 캐시 삭제
trash ~/.claude/plugins/cache/gptaku-plugins/<plugin-name>/<old-version>

# 2) 새 버전 캐시 생성 (마켓플레이스에서 복사)
cp -R ~/.claude/plugins/marketplaces/gptaku-plugins/plugins/<plugin-name> \
      /tmp/<plugin-name>-staging
mkdir -p ~/.claude/plugins/cache/gptaku-plugins/<plugin-name>/<new-version>
cp -R /tmp/<plugin-name>-staging/* \
      ~/.claude/plugins/cache/gptaku-plugins/<plugin-name>/<new-version>/
trash /tmp/<plugin-name>-staging
```

### Step 6: installed_plugins.json 업데이트 (+ enabledPlugins 확인)

⚠️ **신규 플러그인 첫 설치를 수동 파이프라인으로 했다면 `~/.claude/settings.json`의
`enabledPlugins`에 `"<plugin>@gptaku-plugins": true`가 있는지 반드시 확인한다.**
`/plugin install`은 이 항목을 자동으로 넣지만 수동 설치(캐시+installed_plugins.json)는
건너뛰므로, 없으면 훅·스킬이 전혀 로드되지 않은 채 "설치돼 보이는" 상태가 된다
(2026-08-24 ddiring 실사례 — 훅 미발화 원인이 코드가 아니라 미enable이었음).

```python
# ~/.claude/plugins/installed_plugins.json 에서 해당 플러그인 항목 수정:
# - installPath: 새 버전 경로로 변경
# - version: 새 버전으로 변경
# - gitCommitSha: 서브모듈 최신 커밋 SHA로 변경
# - lastUpdated: 현재 시간으로 변경
```

### Step 7: 검증

```bash
python3 tools/gptaku_doctor.py <plugin-name> --all
# 인자 없이 부르면 전체 플러그인. --network 를 붙이면 GitHub 릴리즈 태그까지 대조.
```

7축을 한 번에 대조한다 — enabledPlugins 등록 / 캐시 단일 버전 / `.claude-plugin` 닷파일 /
plugin.json↔installed_plugins.json 버전 / 마켓 클론 SHA **및 내용 diff** / 훅 스크립트 실체 /
릴리즈 태그. 불일치마다 복붙 가능한 처방을 출력하고, `fail`이 있으면 종료코드 1이다.

- **`unverified`는 실패가 아니라 "검증 안 함"이다.** (네트워크 미사용, 프라이빗 플러그인 등)
  없음으로 반올림하지 말 것.
- **버전이 같아도 캐시가 스테일할 수 있다** — bump 없이 배포한 fix는 캐시 교체를 유발하지
  않으므로 버전 대조만으로는 영원히 안 잡힌다. SHA 축이 내용 diff까지 하는 이유
  (2026-08-31 최초 실행에서 이 유형 9종 적발).
- 판정 로직 자체의 회귀는 `python3 tools/test_gptaku_doctor.py`(결함 주입 17케이스·7축 전부, CI 게이트).

### Step 8: Claude Code 재시작

캐시를 교체해도 **현재 세션**은 이미 로드된 구 버전을 사용한다.
반드시 Claude Code를 재시작해야 새 버전이 반영된다.

## 핵심 원칙

- **버전을 올릴 때는 반드시 동작 확인 후** 올린다. 미확인 상태에서 버전만 반복 업데이트하지 않는다.
- **버전 bump = 릴리즈 발행**이 기본이다. Step 1에서 버전을 올렸으면 Step 2에서 같은 버전 태그의 GitHub 릴리즈를 반드시 만든다. 태그(`v<version>`)는 plugin.json 버전과 1:1로 일치시킨다.
- **캐시는 단일 버전만 유지**한다. 구 버전 디렉토리는 즉시 삭제한다.
- **installed_plugins.json의 installPath, version, gitCommitSha**가 모두 일치해야 한다.
- **커맨드 파일이 실행 지시서**다. Read로 읽은 스킬 파일은 참고 자료일 뿐 도구 호출을 트리거하지 않는다.

## pumasi 사용 규칙

### 프로젝트별 config — `.pumasi/pumasi.config.yaml`

pumasi 실행 시 플러그인 내부 config를 **절대 수정하지 않는다.**
프로젝트 루트의 `.pumasi/pumasi.config.yaml`을 사용한다.

```
gptaku_plugins/
  .pumasi/
    pumasi.config.yaml   ← 이 파일에 tasks 작성
```

pumasi-job.js가 CWD의 `.pumasi/pumasi.config.yaml`을 자동으로 감지하므로
별도 `--config` 옵션 없이 `pumasi.sh start "컨텍스트"` 만으로 동작한다.

---

## 플러그인별 주요 파일

### show-me-the-prd

| 파일 | 역할 |
|------|------|
| `commands/show-me-the-prd.md` | **실행 지시서** — AskUserQuestion 인라인 호출 포함 |
| `skills/show-me-the-prd/SKILL.md` | 참고 문서 (Read로 읽히면 참고 자료 취급) |
| `.claude-plugin/plugin.json` | 버전 정보 |
| `references/` | 인터뷰 가이드, 문서 템플릿, 리서치 전략 |

<!-- insane-harness:begin -->
<!-- ih-rule:rule-cache-copy-001 -->
## 캐시 복사 규칙 (insane-harness 진단으로 추가)

- 플러그인 캐시 교체 시 `cp -R <staging>/*` 금지 — 셸 글롭이 `.claude-plugin/` 같은 닷 엔트리를 누락시킨다 (2026-07-08 insane-harness 배포에서 실제 발생).
- 항상 `cp -R "$SRC/." "$DST/"` 형태로 복사하고, 복사 후 `trash "$DST/.git"`(서브모듈 gitlink 제거) → `diff -rq "$SRC" "$DST" --exclude=.git`으로 대조 검증한다.
<!-- /ih-rule:rule-cache-copy-001 -->
<!-- insane-harness:end -->
