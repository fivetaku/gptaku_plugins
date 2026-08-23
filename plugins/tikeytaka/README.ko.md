[English](README.md) | 한국어 | [日本語](README.ja.md) | [Español](README.es.md) | [中文](README.zh.md)

# tikeytaka (티키타카)

API 키 중앙 볼트 플러그인 — 흩어진 `.env`의 키를 암호화 볼트 하나로 모으고, 채팅에 키를 노출하지 않고 등록하며, 갱신 한 번으로 모든 프로젝트에 전파합니다. AI와 티키타카하는 동안 키는 자동으로 조회·연결됩니다.

## Quick Start

### 1. 마켓플레이스 추가

```
/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git
```

### 2. 설치

```
/plugin install tikeytaka
```

### 3. Claude Code 재시작

(새 커맨드는 재시작 후에 등록됩니다.)

### 4. 실행

```
/tikeytaka
```

이후 본인 터미널에서 `bash <플러그인경로>/bin/tkt init`을 1회 실행하고(정확한 경로는 커맨드가 알려줍니다), `/tikeytaka:scan`으로 기존 키를 통합하세요.

## 왜 tikeytaka인가

실제 홈 디렉토리를 스캔해보니 **`.env` 파일 45개**, 같은 키가 6개 파일에 3가지 다른 값으로 존재했고 대부분 죽은 키였습니다. 흩어진 키는 갱신도 폐기도 불가능하고, 뭘 갖고 있는지조차 알 수 없습니다. tikeytaka는 암호화 파일 하나를 정본으로 만들고, 모든 `.env`를 기계가 갱신하는 사본으로 바꿉니다.

- **가입 불필요**: 이미 쓰는 클라우드 폴더(iCloud Drive / Google Drive / OneDrive / Dropbox)를 자동 감지해 암호화 파일 하나를 동기화. 없으면 로컬 단일 기기 모드. 최초 선택 경로는 고정되어 임의로 바뀌지 않습니다.
- **구조적으로 안전**: AES-256-CBC + PBKDF2(60만회, SHA-256) + 자체 무결성 해시(TKT2 포맷). 손상·동기화 미완료 파일은 감지 즉시 중단하며 **절대 덮어쓰지 않고**, 모든 변경 전 `.bak` 한 세대를 보존합니다.
- **OS 통합**: 복호화 암호는 macOS 키체인 / Linux secret-tool / Windows DPAPI에 보관. 셋 다 없으면 명시적 동의(`TKT_ALLOW_FILE_FALLBACK=1`) 하에만 0600 파일 폴백.
- **노출 최소화**: 키 값은 터미널 숨김 입력(`tkt setp`) 또는 stdin(`set-stdin`)으로만 받아 채팅·셸 히스토리·프로세스 목록(argv)에 남기지 않습니다.

## 동작 구조

```
사용자 / Claude  ──►  bin/tkt (단일 bash CLI)
                       ├── secrets.enc   암호화 볼트 — 클라우드 폴더로 이동
                       ├── OS 키체인      마스터 암호 1개 — 기기 밖으로 안 나감
                       └── map.tsv       기기 로컬 배선 — 어떤 .env에 어떤 키
```

클라우드에는 항상 암호문만 다니고, 여는 열쇠는 기기를 떠나지 않습니다. `tkt sync`는 1회 복호화 후 무결성을 검증하고, 매핑된 모든 `.env`를 파일 권한을 보존한 채 갱신합니다.

## 커맨드

| 커맨드 | 기능 |
|---|---|
| `/tikeytaka` | 상태 요약 (키 수, 볼트 위치, 미전파 여부) |
| `/tikeytaka:use` | **키가 필요한 작업에서 볼트 먼저 확인 → 자동 연결·테스트** (묻지 않음) |
| `/tikeytaka:scan` | 기존 프로젝트 .env 탐색 → 키 통합 등록 + 연결 (죽은 키 실측 검증 포함) |
| `/tikeytaka:add` | 새 키를 채팅 노출 없이 등록 |
| `/tikeytaka:list` | 관리 중 서비스·프로젝트 연결 현황 |
| `/tikeytaka:sync` | 볼트 → 연결된 모든 .env 전파 |

## 새 기기 연결

1. 클라우드 폴더 동기화 대기 (볼트 파일 도착)
2. `bash <플러그인경로>/bin/tkt init` — 같은 볼트 암호 입력
3. 프로젝트 연결은 기기별: `/tikeytaka:scan`(또는 `tkt map-add`)으로 이 기기의 .env를 배선 (연결 목록 `map.tsv`는 설계상 기기 로컬)
4. `tkt sync`

## 요구사항

- `bash`, `openssl` (macOS·Linux·Git for Windows에 기본 동봉 — Claude Code의 Windows 셸이 Git Bash)
- 비밀 저장소: macOS 키체인 / Linux `secret-tool` / Windows PowerShell(DPAPI)

| 플랫폼 | 상태 |
|---|---|
| macOS (키체인 + iCloud/기타) | 검증 완료 |
| Windows (Git Bash + OneDrive/Google Drive + DPAPI) | 구현됨, 준검증 |
| Linux (secret-tool + Dropbox 또는 `TIKEYTAKA_DIR` 수동 지정) | 구현됨, 준검증 |

## 알려진 한계 (정직 고지)

- **동시 편집 금지**: 두 기기에서 같은 순간 `set`/`del` 하면 한쪽이 충돌 감지로 중단됩니다(데이터는 안전). 개인 사용 전제.
- macOS 키체인 등록(`security -w`)은 init 1회에 한해 암호가 프로세스 인자로 지나갑니다 — 도구 제약.
- 이 볼트는 개인 사용자용입니다. 팀 공유·권한 분리·감사 로그가 필요하면 시크릿 SaaS(예: Infisical)를 쓰세요.
- 사용자 계정 자체가 이미 침해된 환경(키로거 등)은 어떤 로컬 볼트도 보호하지 못합니다.

## 소스

https://github.com/fivetaku/tikeytaka — [gptaku-plugins](https://github.com/fivetaku/gptaku_plugins) 마켓플레이스 소속.

## 라이선스

[MIT](./LICENSE) — [DISCLAIMER.md](./DISCLAIMER.md) 참조.
