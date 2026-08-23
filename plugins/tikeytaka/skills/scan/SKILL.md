---
name: scan
description: 기존 프로젝트들의 .env 파일을 탐색해 API 키를 중앙 볼트로 등록하고, 각 .env를 볼트와 연결한다. 트리거 — "/tikeytaka:scan", "env 스캔해줘", "흩어진 키 정리해줘", "프로젝트 키 통합해줘".
---

# tikeytaka:scan — 파편화된 .env 키를 볼트로 통합

코어 CLI: `bash "${CLAUDE_PLUGIN_ROOT}/bin/tkt"` (이하 `tkt`)

## 절차

1. **탐색**: 홈 디렉토리에서 `.env`/`.env.local` 파일을 찾는다. `node_modules`, `Library`, `.Trash`, 백업/Downloads류는 제외한다.

2. **인벤토리**: 각 파일의 변수 이름만(값 제외) 추출해 보여준다. **키 값은 절대 채팅에 출력하지 않는다** — 값 비교가 필요하면 sha256 앞 8자리 지문으로만 다룬다.

3. **분류**: 변수를 세 종류로 나눈다.
   - 공유 시크릿(같은 키가 여러 프로젝트에서 쓰임 / API 키·토큰류) → 볼트 등록 대상
   - 프로젝트 전용 설정(URL, 모델명, 플래그, 포트) → 제외
   - 자동 갱신형 토큰(스크립트가 주기적으로 rewrite하는 것) → 제외하고 사유 고지

4. **충돌 검증**: 같은 이름의 키가 파일마다 다른 값이면, 가능한 경우 각 서비스의 무료 인증 확인 엔드포인트로 유효성을 실측해 살아있는 값을 정본으로 고른다(예: Gemini `GET /v1beta/models?key=`, OpenAI `GET /v1/models`, Telegram `getMe`). 실측 불가하면 최근 수정 파일의 값을 쓰되 사용자에게 고지한다.

5. **등록·연결** (파일 수정 전 반드시 원본을 `~/.config/tikeytaka/backup-<날짜>/`에 백업):
   ```bash
   tkt set <service> "$값"            # 값은 셸 변수로만 전달
   tkt map-add '<파일>' <변수> <service>
   tkt sync --check                    # 드라이런 확인 후
   tkt sync
   ```
   서비스명은 `<provider>-api-key` 케밥케이스로 통일한다.

6. **보고**: 등록 수 / 교체된 죽은 키 수 / 살아있는 잉여 키(콘솔에서 폐기 권장) / 제외 항목을 요약한다.
