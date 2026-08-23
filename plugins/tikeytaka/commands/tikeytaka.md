---
description: API 키 중앙 볼트 — 상태 확인 및 기능 라우터
---

# /tikeytaka — API 키 중앙 관리

`${CLAUDE_PLUGIN_ROOT}/bin/tkt` 가 코어 CLI다. 인자를 보고 라우팅한다:

- 인자에 "스캔", "탐색", "등록해줘"+기존 프로젝트 맥락 → **scan 스킬**
- 인자에 "추가", "새 키", 특정 서비스명 등록 요청 → **add 스킬**
- 인자에 "목록", "리스트", "뭐 관리" → **list 스킬**
- 인자에 "동기화", "전파", "반영" → **sync 스킬**
- 인자에 "써줘", "연결", "가져다", 또는 API 작업 맥락에서 키가 필요 → **use 스킬** (볼트 먼저 확인, 묻지 않기)
- 인자 없음 → 아래 상태 요약을 보여준다:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/bin/tkt" where
if out="$(bash "${CLAUDE_PLUGIN_ROOT}/bin/tkt" list 2>&1)"; then
  echo "관리 중 키: $(printf '%s\n' "$out" | wc -l | tr -d ' ')개"
else
  case "$?" in
    2) echo "볼트 없음 — init 필요";;
    *) echo "⚠️ 볼트를 열 수 없음(암호 불일치/손상) — 키 0개가 아님: $out";;
  esac
fi
bash "${CLAUDE_PLUGIN_ROOT}/bin/tkt" sync --check                # 미전파 여부
```

(복호화 실패를 "키 0개"로 보고하는 것 금지 — exit code로 구분한다.)

셋업이 안 된 기기(`tkt init` 미실행)면 먼저 init을 안내한다. init은 사용자가 터미널에서 직접 실행:
```
bash "${CLAUDE_PLUGIN_ROOT}/bin/tkt" init
```

**절대 원칙: 키 값을 채팅으로 받지 않는다.** 사용자가 키를 붙여넣으면 유출로 간주하고 재발급을 권고한 뒤 add 스킬 절차로 유도한다. 자동화 경로에서 값을 다뤄야 하면 `set-stdin`을 쓴다 (`set <service> <값>`은 argv·히스토리에 남으므로 스킬에서 사용 금지).
