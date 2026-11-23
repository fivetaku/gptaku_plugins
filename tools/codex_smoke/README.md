# codex_smoke — Codex 격리 실측 도구

gptaku 플러그인을 Codex에서 실제로 돌려 판정한다. 모든 실행은 `~/gptaku-codex-merge-state/smoke/` 아래
새 `CODEX_HOME`(설정은 `smoke-tmpl/config.toml` 복사, 로그인 파일 없음 — 모델은 로컬 프록시 경유)과
가짜 `HOME`(가짜 `.claude`·`.gptaku-setup`)에서 돈다. 오너의 `~/.codex`·`~/.claude`는 쓰지 않는다.

| 명령 | 하는 일 |
|--|--|
| `run.sh --all` / `run.sh <plugin>...` | 작업 사본을 로컬 마켓으로 설치해 `prompts.tsv` 요청을 숨은 tmux TUI로 1회 보내고 행별 판정 표를 낸다(`--workers N`, 기본 8) |
| `core_ab.sh` | gptaku-core 분기 A/B — origin/main 판(A)과 작업 사본(B)을 같은 요청으로 비교 |
| `install_check.sh --source <src> [--all]` | 마켓 등록·설치 후 Codex가 `.agents` 마켓을 읽었는지, 캐시 파일이 태그와 같은지 대조 |

판정 기준은 `scan.py` 머리말에 있다. 요청 문장과 "질문이 나와야 하는가"는 `prompts.tsv`에서 고친다.
필요한 것: `codex` CLI, `tmux`, 로컬 모델 프록시가 설정된 `smoke-tmpl/config.toml`.
