[English](README.md) | 한국어

# insane-crawl

공개 웹페이지를 로컬에서 재개 가능한 방식으로 수집하는 리서치 크롤러입니다.
`insane-search`를 페이지 하나를 가져오는 유계 획득 프리미티브로 재사용하고,
동일 사이트 탐색, SQLite 체크포인트, robots 판정, 페이지 스냅샷과 작업 영수증을
별도 계층으로 제공합니다.

## 빠른 시작

```bash
cd skills/insane-crawl
python3 -m engine crawl "https://example.com" --max-pages 20 --run-for 45
python3 -m engine status JOB_ID
python3 -m engine resume JOB_ID --run-for 45
python3 -m engine results JOB_ID --limit 20
python3 -m engine page JOB_ID 1 --limit 20000
```

제어 응답은 작게 유지합니다. 페이지 본문은 로컬 스냅샷에 저장되며 `page` 명령으로
필요한 범위만 읽습니다. 전체 크롤 본문을 한 번에 에이전트 컨텍스트로 넣지 않습니다.

## v0.1.0 경계

- 로그인·페이월을 넘지 않는 공개 페이지 전용
- URL 정규화와 중복 제거를 적용한 동일 사이트 크롤
- SQLite 프론티어와 append-only 이벤트
- 페이지별 fetch 시도 예산과 전체 크롤 페이지 예산 분리
- `discover`는 호환되는 로컬 `insane-search`의 endpoint miner가 있을 때 재사용.
  현재 insane-search 배포본에는 이 스크립트가 없어 `unavailable`을 반환하며,
  crawl/fetch에는 영향을 주지 않음. 텍스트에서 찾은 후보는
  `candidate`, GET JSON 재생에 성공한 후보는 `probable`이며, 렌더 귀속 검증 전에는
  신뢰 fast-path 레시피로 승격하지 않음

## 의존성

`INSANE_SEARCH_SKILL_ROOT`를 우선하고, 다음으로
`~/.claude/plugins/installed_plugins.json`에 등록된 insane-search의 `installPath`,
마지막으로 개발용 형제 디렉토리 `plugins/insane-search/skills/insane-search`를 찾습니다.
두 플러그인의 캐시 버전은 같을 필요가 없으며, 미등록 캐시를 버전순으로 고르지 않습니다.

선택 기능인 discovery는 `INSANE_SEARCH_ENDPOINT_MINER`로 호환되는 로컬
`endpoint_miner.py`를 직접 지정할 수 있습니다. 그 외에는 같은 skill 경로와
기존 marketplace/source 경로를 확인합니다. 이 플러그인은 endpoint miner를
새로 제공하지 않으며, 스크립트가 없으면 실제로 `unavailable`을 반환합니다.

## 상태 위치

기본값은 `~/.local/state/insane-crawl`입니다. `--state-dir` 또는
`INSANE_CRAWL_STATE_DIR`로 바꿀 수 있습니다. 사용자 프로젝트나 설치된 플러그인
디렉토리에는 상태를 쓰지 않습니다.

## 사용 경계

관련 법, 사이트 약관, robots 규칙, 요청 속도, 콘텐츠 신호를 준수해야 합니다.
`--ignore-robots` 사용 여부는 작업 메타데이터에 명시적으로 기록됩니다.
