---
name: list
description: 중앙 볼트에서 관리 중인 API 키 서비스 목록과 프로젝트 연결 현황을 보여준다. 트리거 — "/tikeytaka:list", "무슨 키 관리 중이야", "키 목록", "어떤 서비스 연결돼 있어".
---

# tikeytaka:list — 관리 현황

코어 CLI: `bash "${CLAUDE_PLUGIN_ROOT}/bin/tkt"` (이하 `tkt`)

```bash
tkt list        # 볼트의 서비스명 목록 (값은 안 나옴)
tkt map-list    # 어떤 프로젝트의 어떤 변수가 어느 서비스에 연결됐는지
tkt sync --check  # 미전파(볼트와 어긋난 .env) 여부
tkt where       # 볼트 파일 위치 (어느 클라우드로 동기화 중인지)
```

## 출력 형식

서비스별로 묶어 표로 보여준다: 서비스명 | 연결된 프로젝트 수 | 연결 파일들. `sync --check`에서 어긋남이 있으면 맨 위에 경고하고 `tkt sync` 실행을 제안한다. 키 값은 어떤 경우에도 출력하지 않는다.
