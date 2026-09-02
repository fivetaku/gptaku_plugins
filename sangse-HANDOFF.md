# sangse 핸드오프 (2026-09-02)

> ideation-workspace 세션에서 하루 동안 개발·검증 후 이 마켓플레이스에 편입됨. 다음 세션은 **이 문서만 읽고** 표준 정합 → 문서 세트 완성 → 0.6.0 릴리스를 이어가면 된다. 개발 히스토리(왜 이 형식인가)는 `plugins/sangse/CHANGELOG.md`와 `plugins/sangse/skills/sangse/references/reference-patterns.md`에 있다.

## 1. 이게 뭔가

**상세페이지 제작 플러그인.** 제품 정보(텍스트·파일·URL)를 받아 국내 커머스 실제 형식인 **이미지 컷 시트**(폭 1000 세로 컷 12~20장, 카피는 이미지 안, 법정 표시는 HTML 블록)를 만든다. 컷은 "고객이 결제 전 조용히 던지는 8가지 질문" 순서로 편성한다.

- 진입점: `commands/sangse.md` (`/sangse <제품정보>`, `/sangse 카피만 …`, `/sangse check <dir>`). 자연어 "상세페이지 만들어줘"로 자동 트리거.
- 스킬 1개: `skills/sangse/SKILL.md` (단일 스킬 플러그인 예외 — 플러그인명=스킬명).
- 흐름: Step 0 의존성 점검(`scripts/check_deps.sh`) → 제품 인터뷰(불확실 슬롯만, 4문항×2라운드) → 오퍼 점검 → 컷 시트(`cuts.md`+`legal.md`) → **게이트 1** `check_cuts.py`(결정론) → **게이트 2** 리뷰어 에이전트 4인 → 카피 승인 → 컷 이미지(`/pumasi:image`, 앵커→`--ref`, 텍스트+물리 정합성 검수) → HTML 조립 → **게이트 3** Playwright 렌더+5초 테스트 → 스코어카드.
- Iron Law: 입력에 없는 사례·수치·후기·환불·기한은 만들지 않는다 → `[자료 필요]`.
- 의존: `pumasi@gptaku-plugins`(이미지, 필수에 가깝지만 없으면 카피·HTML 플레이스홀더까지), Codex CLI `image_generation`, python3, Node+Playwright(게이트 3, 선택).
- 라이브 예시: https://fivetaku.github.io/sangse/ (가상 건기식 3종, 14컷×3, 전 과정 산출물 `examples/`).

## 2. 편입 상태 (실측)

- 개별 레포 `fivetaku/sangse` (public, MIT) — 최신 커밋 `0d57240` (0.5.0). 이 레포에 `.claude-plugin/plugin.json`, `commands/`, `skills/`, `setup/`, README.md·README.ko.md, CHANGELOG, DISCLAIMER, LICENSE.
- 마켓플레이스: `plugins/sangse` **submodule**로 추가 + `.claude-plugin/marketplace.json` 항목(category `marketing`) — 커밋 `0937fe6` 푸시 완료. `python3 validate_plugins.py` → sangse 이슈 0.
- 설치 검증: `claude plugin marketplace update gptaku-plugins` → `claude plugin install sangse@gptaku-plugins` 성공(0.5.0 캐시), 설치본에서 `check_deps.sh`·`check_cuts.py` 정상.
- 개발 체크아웃: `~/sangse` (구 `~/.claude/skills/sangse` — 플러그인과 이름 충돌로 이동). GitHub Pages는 `fivetaku/sangse` main 루트에서 서빙.
- 주의: 이 마켓 레포의 working tree에 **내 것이 아닌 미커밋 변경**이 있다 — `.claude-plugin/marketplace.json`의 `insane-crawl` 항목, `.gitignore`, 여러 submodule 포인터(docs-guide·git-teacher·insane-design·nopal·show-me-the-prd·skillers-suda), `.agents/`·`.antigravitycli/`. sangse 커밋 때 의도적으로 제외했다. 건드리지 말 것.

## 3. 다음 작업: 다른 플러그인 기준에 맞추기

pumasi·tikeytaka 등 성숙 플러그인의 문서 세트와 비교한 갭:

- [ ] **README 다국어**: `README.ja.md`, `README.es.md`, `README.zh.md` 추가 (pumasi 패턴: 첫 줄 language toggle 전 언어 상호 링크). 현재 en·ko만 있음. 첫 줄 토글도 5개 언어로 갱신.
- [ ] **VERSIONING.md 규칙 대조**: CHANGELOG 형식(날짜·섹션명)과 plugin.json 버전이 이 레포 규칙과 같은지 확인. 0.5.0 → 다음 릴리스는 0.6.0(아래 §4 병합 시).
- [ ] **CLAUDE.md "플러그인 버전 업데이트 체크리스트"** 절차대로 릴리스 리허설 1회: 서브모듈 안에서 버전 올리고 push → 부모 레포 submodule 포인터 커밋 → `claude plugin marketplace update` → 캐시 버전 확인. 이 절차를 `plugins/sangse/CHANGELOG.md` 상단이나 README 개발 섹션에 1줄로 링크.
- [ ] **tests/**: pumasi처럼 `tests/` 디렉토리. 후보: `check_cuts.py`를 `examples/` 3종에 돌려 PASS를 확인하는 `tests/test-gates.sh`, `assemble_html.py` 컷 모드 스모크, `check_deps.sh` exit 0. (`examples/`가 이미 픽스처 역할.)
- [ ] **commands/sangse.md 표준 대조**: PLUGIN_STANDARD §4 frontmatter(`argument-hint`, `allowed-tools`)와 다른 플러그인 라우터의 "No argument → AskUserQuestion" 패턴 일치 확인. `Skill`·`Agent` 도구가 allowed-tools에 들어간 것이 다른 플러그인과 일관되는지 검토.
- [ ] **setup/setup.sh**: pumasi 것을 PLUGIN/OWN_REPO만 바꿔 복사했다. `gptaku-update-check.cjs` 훅 등록 경로·마커 파일명이 sangse로 잘 갈리는지 1회 실행 확인(`bash setup/setup.sh ask` → 출력 없음 또는 `STAR_ASK`).
- [ ] **.gitignore**: 표준 항목(`.claude/*.local.md`, `node_modules/`) 포함됨. `sangse/`(사용자 프로젝트 산출물 폴더명)와 `RESEARCH/` 제외가 의도대로인지 확인.
- [ ] **assets/**: 마켓 README 카드용 대표 이미지(다른 플러그인은 `assets/`에 로고·스크린샷). 예시 페이지 첫 컷 스크린샷을 후보로.
- [ ] 루트 `README.md`(마켓플레이스 소개, 5개 언어) 플러그인 목록에 sangse 1줄 추가 — 현재 미반영.
- [ ] `CLAUDE.md` 프로젝트 구조 트리에 `sangse/  # 상세페이지 컷 시트 제작` 1줄 추가.

## 4. 미완 콘텐츠 (별도 세션 재실행 필요 — 서버 rate limit으로 중단)

2026-09-02 22시경 API 429(전 계정 소진, ~1시간)로 에이전트 5개가 산출물 없이 종료됨. 캡처·조각 파일은 남아 있다.

| 작업 | 상태 | 재실행 입력 |
|---|---|---|
| 컴플라이언스 화장품(화장품법 13조·실증·기능성) | 미착수(죽음) | `~/ideation-workspace/RESEARCH/카테고리-컴플라이언스_20260902_213000/` 세션. 프롬프트 골격은 이 세션 트랜스크립트 참고 — 1차 소스 우선, 치환표 20쌍, 금지어 정규식 ban 15/warn 10, 결과 `artifacts/agent_results/A_cosmetics.md` |
| 의료기기·의약외품 | 동일 | `B_meddevice.md` |
| 금융·투자·보험·대출 | 동일 | `C_finance.md` |
| 교육·자격·취업 | 동일 | `D_education.md` |
| 전자제품·생활용품(전안법 KC) | 미착수 | `E_electronics.md` |
| 올리브영(뷰티) 해부 | 36조각 판독 후 파일 쓰기 직전 죽음 | 조각 `~/ideation-workspace/RESEARCH/상세페이지-레퍼런스-해부_20260902_203000/captures2/oliveyoung-cuts/` 36장 → `artifacts/agent_results/H_oliveyoung.md` |

완료된 해부: 무신사(F, 스킬에 F1~F8 반영 완료), 크몽(G_kmong.md — **템플릿 G1~G8이 아직 `assets/cut-templates.json`·`cut-sheet.md`에 미반영**).

병합 방법: 컴플라이언스 결과 → `skills/sangse/references/compliance.md` §6 인덱스 자리에 업종별 상세 섹션 + `assets/banned-words.json`에 카테고리 키 추가 + `check_cuts.py LEGAL_REQUIRED`와 `interview.md` Q-규제 옵션 갱신. 해부 결과 → `cut-templates.json` 템플릿 추가 + `cut-sheet.md` §3 시퀀스 + `reference-patterns.md` §7 비교표. 그다음 0.6.0.

## 5. 참고 자료 위치

- 리서치 세션(로컬 전용): `~/ideation-workspace/RESEARCH/상세페이지-작성방법론_20260902_190200/`(CRO·카피 근거 36소스), `상세페이지-레퍼런스-해부_20260902_203000/`(캡처·조각·해부 A~G), `카테고리-컴플라이언스_20260902_213000/`(state.json만).
- 예시 산출물 전 과정: `plugins/sangse/examples/{punggi-red-ginseng-stick,gwangyang-maesil-jelly,jeju-greentea-catechin}/` — cuts.md·legal.md·images/·qa/(게이트 결과·5초 테스트·홍삼 고객 시뮬 리뷰 r1/r2)·legacy-v0.3/.
- 운영 교훈(스킬에 이미 반영): 이미지 생성 에이전트는 포그라운드 실행·재개 규칙 / 컷 검수는 텍스트+물리 정합성(매실 앵커 젤리 노출 사례) / 헤드리스 Chrome CLI 최소 창 폭 500px 함정 / 스마트스토어 자동화 로그인 벽·쿠팡은 사용자 크롬 세션(paseo)만 통함 / `set -o pipefail`에서 `codex … | grep -q` SIGPIPE 오탐.
