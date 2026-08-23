---
description: API 키 중앙 볼트 — 상태 확인 및 기능 라우터
---

# /tikeytaka — API 키 중앙 관리

`${CLAUDE_PLUGIN_ROOT}/scripts/tkt` 가 코어 CLI다. 인자를 보고 라우팅한다:

- 인자에 "스캔", "탐색", "등록해줘"+기존 프로젝트 맥락 → **scan 스킬**
- 인자에 "추가", "새 키", 특정 서비스명 등록 요청 → **add 스킬**
- 인자에 "목록", "리스트", "뭐 관리" → **list 스킬**
- 인자에 "동기화", "전파", "반영" → **sync 스킬**
- 인자 없음 → 아래 상태 요약을 보여준다:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/tkt" where
bash "${CLAUDE_PLUGIN_ROOT}/scripts/tkt" list 2>/dev/null | wc -l   # 관리 중 키 수
bash "${CLAUDE_PLUGIN_ROOT}/scripts/tkt" sync --check                # 미전파 여부
```

셋업이 안 된 기기(`tkt init` 미실행)면 먼저 init을 안내한다. init은 사용자가 터미널에서 직접 실행:
```
bash "${CLAUDE_PLUGIN_ROOT}/scripts/tkt" init
```

**절대 원칙: 키 값을 채팅으로 받지 않는다.** 사용자가 키를 붙여넣으면 유출로 간주하고 재발급을 권고한 뒤 add 스킬 절차로 유도한다.
