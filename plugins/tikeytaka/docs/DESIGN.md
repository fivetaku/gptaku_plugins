# tikeytaka 설계 배경 및 검증 기록 (2026-08-23)

실사용 환경(맥 2대, 프로젝트 45개, .env 파편화)에서 하루 동안 실측 검증한 결과를 바탕으로 한 설계 기록.

## 1. 문제

- 홈 디렉토리 스캔 결과 `.env`/`.env.local` 45개 발견, 동일 키(예: Gemini)가 6개 파일에 3가지 다른 값으로 존재.
- API 실측 결과 상당수가 죽은 키였음: Gemini 구키 2종(401/400), Perplexity(401), 플레이스홀더 다수. 살아있는 잉여 키(과거 발급분)도 3종 발견 — 파편화는 유출면적 증가와 "어떤 게 진짜인지 모름" 문제를 동시에 만든다.

## 2. 검토한 대안과 탈락 사유

| 대안 | 결과 |
|---|---|
| **macOS 로그인 키체인** (`security` CLI) | 동작하지만 기기 간 동기화 없음 (iCloud 키체인과 별개 저장소) |
| **iCloud 키체인 직접 쓰기** | CLI에서 OS 차원 차단. ①kSecUseDataProtectionKeychain → `-34018`(entitlement 없음) ②Apple Development 인증서 + keychain entitlement 서명 → AMFI 강제종료(137) ③레거시 synchronizable 경로 → 역시 `-34018`. **Xcode 서명 앱(자동 provisioning)으로는 쓰기/읽기 성공을 실증**했으나, 무료 계정 프로필이 7일 만료라 매주 재빌드 필요 → 운영 불가 판정 |
| **Infisical / Doppler 등 SaaS** | 딥리서치(출처 35건) 결과 크로스플랫폼 1순위는 Infisical(무료 티어 + CLI `secrets get --plain` + MIT 셀프호스팅). 그러나 신규 가입 요구가 개인 사용자에게 진입장벽 → 기본 경로에서 제외, 팀 공유 시 옵션으로만 유지 |
| **pass(GnuPG)** | Windows 네이티브 미지원 탈락. KeePassXC는 비대화형 조회 시 DB 암호 순환 문제 |

## 3. 채택한 설계

**암호화 파일 + 사용자가 이미 가진 클라우드 동기화 폴더** 조합:

- 정본 = `secrets.enc` (AES-256, openssl) 1개 파일. TSV(service\tvalue) 평문을 암호화.
- 위치 = 자동 감지: iCloud Drive → Google Drive → OneDrive → Dropbox → 로컬(`~/.tikeytaka`). 클라우드는 파일 배달부 역할만 하므로 **가입이 필요 없다**.
- 복호화 암호 = OS 비밀 저장소(맥 키체인 / Linux secret-tool / 폴백 600 파일). 클라우드가 털려도 파일만으로는 열 수 없음.
- 전파 = `map.tsv`(파일·변수·서비스 매핑) 기반 `tkt sync`. direnv 대신 .env 직접 갱신 방식을 택한 이유: 데몬·dotenv 로더·비대화형 스크립트가 훅 없이 그대로 동작하고, dotenv의 "기존 env 우선" 규칙과 충돌하지 않음.

## 4. 유출 방지 원칙

- 키 값은 채팅/대화 히스토리에 절대 받지 않는다. 등록은 `tkt setp`(터미널 숨김 입력) 안내로만.
- 채팅에 이미 붙여넣어진 키는 유출로 간주 → 재발급 권고 후 절차 진행.
- 스킬 산출물에서 값 비교가 필요하면 sha256 지문 8자리만 사용.

## 5. 검증 완료 항목 (2026-08-23)

- tkt 전 기능 왕복 테스트: init → set/get 일치 → map-add → sync --check → sync 반영 → del. 격리 볼트에서 통과.
- 실환경 이관: 키 14종 볼트 등록, 죽은 키 9건 교체(교체 후 Gemini 실호출 200 확인), 24개 파일·변수 매핑 전파.
- 함정 기록: zsh 비분리 변수(`${=VAR}` 필요), `grep -v` 전량 제거 시 exit 1로 파이프라인 중단(`|| true` 필수), LibreSSL은 `-pbkdf2` 미지원(고엔트로피 랜덤 암호로 상쇄).

## 6. 향후 옵션

- Windows Credential Manager 네이티브 지원 (현재는 파일 폴백)
- Infisical 백엔드 어댑터 (팀 공유 수요 발생 시)
- 유료 Apple Developer 계정 확보 시 iCloud 키체인 네이티브 백엔드 재검토 (실증 코드는 확보됨)
