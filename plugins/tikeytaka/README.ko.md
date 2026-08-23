# tikeytaka

API 키 중앙 볼트 플러그인 — 흩어진 `.env`의 키를 암호화 볼트 하나로 모으고, 채팅에 키를 노출하지 않고 등록하며, 갱신 한 번으로 모든 프로젝트에 전파합니다.

- **가입 불필요**: 이미 쓰는 클라우드 폴더(iCloud Drive / Google Drive / OneDrive / Dropbox)를 자동 감지해 암호화 파일(AES-256)을 동기화. 없으면 로컬 단일 기기 모드.
- **OS 통합**: 복호화 암호는 macOS 키체인 / Linux secret-tool에 보관.
- **유출 방지**: 키 값은 터미널 숨김 입력(`tkt setp`)으로만 받고, 채팅·히스토리에 남기지 않음.

## 커맨드

| 커맨드 | 기능 |
|---|---|
| `/tikeytaka` | 상태 요약 (키 수, 볼트 위치, 미전파 여부) |
| `/tikeytaka:scan` | 기존 프로젝트 .env 탐색 → 키 통합 등록 + 연결 (죽은 키 실측 검증 포함) |
| `/tikeytaka:add` | 새 키를 채팅 노출 없이 등록 |
| `/tikeytaka:list` | 관리 중 서비스·프로젝트 연결 현황 |
| `/tikeytaka:sync` | 볼트 → 연결된 모든 .env 전파 |

## 새 기기 연결

1. 클라우드 폴더 동기화 대기 (볼트 파일 도착)
2. `bash <플러그인경로>/scripts/tkt init` — 같은 볼트 암호 입력
3. `tkt sync` — 끝
