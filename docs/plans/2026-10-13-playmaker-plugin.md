# playmaker 플러그인 계획과 현황 (v0.1.0)

- 작성: 2026-10-13
- 위치: `plugins/playmaker/` (in-tree, 아직 마켓 미등재·미커밋)
- 근거: GPT Pro 리뷰 `.insane-review/response_goalboard-review_20261012_224606_31593_9bf1a0.md`, mods CLI 실측 `RESEARCH/claude_code_mods_usecases_20261006_103053/outputs/03_cli_test_results.md`
- 이전 시험판: `prototypes/goalboard-mod/` (2열 마일스톤 보드, 대체됨)

## 결정

| 항목 | 결정 |
|---|---|
| 이름 | playmaker (오너 결정, 골잡이와 축구 은유 짝) |
| 배포 단위 | goaljaby와 별도 opt-in 플러그인. 보드 장애가 골 생성에 번지지 않게 하고, 화면 없는 환경(Paseo 등)에는 설치하지 않아도 되게 한다 |
| 보드 축 | 상태 3열(대기·진행·완료), 카드=세부 작업, 마일스톤은 태그, 사람 대기는 ⏸ |
| 폭 | `bodyColumns` 72 이상이면 3열, 미만이면 진행→대기→완료 세로 |
| 보조 보기 | 마일스톤별 체크리스트 토글, 완료 접기/펼치기 |
| 데이터 | PLAN.md 체크리스트 우선, 없으면 PROGRESS·Scope에서 추정(흐린 카드). progress.json 없음 |

## v0.1.0에서 한 일 (리뷰 P0/P1 반영)

| 리뷰 지적 | 처리 |
|---|---|
| `[>]` `[!]` 미파싱, 작업에 상태 필드 없음 | 마커 4종을 상태 4종으로. `Task.state`, `inferred` 추가 |
| UI가 작업을 그리지 않음 | 상태 열에 작업 카드 렌더 |
| 혼합형·비표준 PLAN 누락, `###` 본문 미독 | 모든 줄에서 canonical·loose 헤딩을 함께 수집하고 다음 헤딩까지를 본문으로 |
| 이름 부분문자열로 완료 오판 | 완료 섹션의 최상위 bullet이 M ID를 쓰거나 이름으로 시작할 때만 인정 |
| allDone이 전부 덮음 | 체크리스트가 있으면 작업에서 상태를 계산하고, PROGRESS와 다르면 ⚠ 불일치 표시 |
| 최근 검증이 ```` ```text ```` | 펜스·표 구분선 건너뜀 (실데이터 확인) |
| 병렬 진행 중 첫 번째만 요약 | `진행 M4·M5` 모두 표시 (실데이터 확인) |
| mtime 합산 충돌 | `mtime:size` 두 쌍 문자열로 비교 |
| active가 PROGRESS mtime만 봄 | PLAN·PROGRESS 중 최신, 미래 시각은 0으로 |
| 타이머 중복 | 이전 타이머 cancel 후 1개만 |
| fs 예외 전파 | 탐색·주기마다 격리 |
| 탐색 비결정적 | 이름순 정렬, 동률은 경로로 |
| 사람 대기 추정 | 기존 형식에서는 "현재 마일스톤" 산문 중 그 M ID 구간에 대기·동석·사람 측정 등이 있으면 ⏸ |

## 검증 결과 (2026-10-13, Claude Code 2.1.296)

- `claude plugin validate` 통과.
- `claude plugin test` 27/27: 파서 9(마커 4종, 펜스, 실패 없음, 불일치, 기존 형식 병렬·대기, 산문 오판 방지, 괄호 쉼표, 표 PLAN, 혼합 헤딩), 명령 2, 터미널·데스크톱 각 6(3열, 세로 순서, 완료 접기/펼치기, 마일스톤 보기, 추정 안내, band), band 기본 1, 세션 시작 자동 열림 3.
- 실제 골 폴더 5곳 파싱: popup-auction 5/5 작업 23/23, tesladesk media-path-fix 3/5 진행 M4·M5 사람 대기, sales-prep 2/4, 표 형식 PRD 6개 마일스톤, app-portfolio-orch(산문만, M 표기 없음) 0/5 대기.
- 헤드리스 `claude -p "/playmaker <폴더>" --plugin-dir`: 로드 오류 없음, 요약 텍스트 정상, 비용 0.

## 문서·이미지 (2026-10-13)

- 대표 이미지 `assets/playmaker-hero-01.png` (1254×1254, pumasi:image Codex, goaljaby 대표 이미지를 스타일 앵커로 사용). 제목 "플레이메이커"와 전술판 "대기·진행·완료" 글자 대조 통과.
- README 5개 언어(en·ko·zh·ja·es), CHANGELOG, LICENSE(MIT), DISCLAIMER.
- Paseo 실측: 시험용 커스텀 프로바이더 env `CLAUDE_CODE_PLUGIN_DIRS`로 로드, `/playmaker` 텍스트 요약 정상, pane은 Paseo가 그리지 않음. 프로젝트 `.claude/skills/`에 넣는 방식은 로드되지 않음(자동 로드는 사용자 skills 폴더만).

## 웹 보기·Paseo 연결 (2026-10-13)

- `web/server.mjs`: 의존성 없는 로컬 보드(127.0.0.1, 2초 갱신, 6시간 무접속 종료). Linear 방식 화면: 상단 바·마일스톤 다이아몬드 탭·상태 아이콘(대기 회색 링/진행 노랑 반원/완료 인디고/사람 대기 주황)·3단 카드·리스트 보기·단축키 1/2/D. 로고 `assets/logo.svg`.
- Paseo 자동: `PASEO_AGENT_ID`로 감지 → 세션 시작 때 서버를 켜고 `paseo` MCP로 탭을 연다(같은 주소 탭 재사용). 채팅에는 한 줄 요약만. 탭을 오른쪽 분할에 놓는 API는 없음(`browser_new_tab`은 url만, intent background) — 사용자가 한 번 옮기면 이후 재사용.
- 세션 연결: 상단 칩에 메시지를 받을 골 작업 세션, 카드 클릭 → 상세 패널(상태별 빠른 행동·직접 쓰기·보낸 기록) → `paseo send --no-wait`. 보낸 뒤 세션이 답을 마칠 때까지 그 작업의 버튼 잠금(오너 실측 확인). 쓰기 요청은 토큰+Origin 검사. PLAN.md는 여전히 에이전트만 고친다(오너 결정).
- 실측: 마커 변경 2초 내 반영, `paseo send` 전달·응답, Paseo 새 세션 자동 탭, 오너가 잠금 동작 확인.

## 터미널 카드 행동 (2026-10-15)

- 카드 누름 → 카드 아래 행동 줄(상태별 버튼 + 직접 쓰기 + 닫기) → `$.prompt.submit`로 지금 세션에 지시. AskUserQuestion 대화상자 방식은 기각(모델 질문과 헷갈리고, 떠 있는 동안 친 글자가 Other로 새어 나감 — 오너 실측 "안내넣어").
- tmux 실측(`/tui fullscreen`, 160칸): 오른쪽 도킹, Ctrl+X Tab 포커스, 카드 Enter로 행동 줄, 첫 버튼 자동 포커스, 직접 쓰기 시 입력칸 포커스(`$.ui.focus` — 없으면 글자가 입력창으로 감), 지시 전송·세션 답변·잠금 해제 확인. 낡은 버튼 손잡이 press 오류는 삼킨다.
- 테스트 33/33.

## 남은 일

1. **오너가 실제 화면 확인** (터미널 `/tui fullscreen` 도킹, 좁은 inline, 데스크톱 Code 탭). 테스트는 트리 구조까지만 본다.
2. goaljaby 0.7.0 수정(`docs/plans/2026-10-13-goaljaby-task-checklist.md`)과 실전 1회로 에이전트가 마커를 꾸준히 갱신하는지 확인.
3. 배포: 별도 레포 `fivetaku/playmaker` 생성 → 서브모듈 등록 → marketplace.json 등재 → CLAUDE.md 배포 8단계. 오너 확인 후.
4. 웹 서버 자동 테스트(연결·토큰·전송) 추가. README 5개 언어는 2026-10-15 반영 완료.
5. 보류: 터미널 pane 버튼에서 `$.prompt.submit`으로 같은 행동 보내기, R&R 버킷 보기.
