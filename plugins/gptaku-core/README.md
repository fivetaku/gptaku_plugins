# gptaku-core

gptaku 플러그인들이 공통으로 쓰는 기반 플러그인입니다. 다른 gptaku 플러그인이
`dependencies`로 선언하므로, 아무 gptaku 플러그인이나 설치하면 함께 설치됩니다.

## 하는 일

요청이 gptaku 스킬의 일에 해당하면, 모델이 WebSearch·WebFetch로 바로 가지 않고
그 스킬을 먼저 호출하게 합니다.

- **SessionStart 훅**: 세션 시작·`/clear`·압축 직후마다 켜진 gptaku 스킬의 사용
  규칙을 넣습니다.
- **UserPromptSubmit 훅**: 요청을 각 플러그인이 선언한 키워드와 대조해, 근거가
  있을 때만 맞는 스킬 하나를 지목합니다. `/명령`으로 직접 부른 요청은 건너뜁니다.
- **PostToolUse·PostToolUseFailure 훅(WebFetch)**: WebFetch가 차단·접근 제한(403·429,
  "unable to fetch", 도메인 안전 확인 실패, Cloudflare 확인 페이지 등)으로 페이지를 못 열면
  `insane-search`로 같은 URL을 다시 열게 합니다. 주소가 없거나 연결이 거부된 경우는 넘기지
  않습니다. insane-search가 꺼져 있으면 아무것도 하지 않습니다.

## 내 스킬도 자동으로 쓰게 하기 (사용자 라우트)

gptaku 플러그인이 아닌 스킬 — `~/.claude/skills`의 개인 스킬, 다른 마켓 플러그인의 스킬 — 도 같은
방식으로 지목할 수 있습니다. 다음처럼 요청하면 셋업이 진행됩니다.

```
/gptaku-core:setup
```

("내 스킬도 라우팅 걸어줘"라고 해도 됩니다.) 셋업은 설치된 스킬을 훑어 설명 속 트리거 문구로 키워드
초안을 만들고, 승인받은 것만 `~/.claude/gptaku-core/routes.json`에 쓴 뒤 예문으로 자체 점검합니다.
스킬을 새로 설치하면 다시 돌리면 됩니다.

- 형식은 아래 `routing.json`과 같습니다. 개인 스킬은 콜론 없는 이름(`"skill": "my-skill"`), 다른 마켓
  플러그인은 `"plugin:skill"`로 적습니다.
- 사용자 라우트는 gptaku 플러그인 라우트와 같은 기준으로 순위를 매깁니다. 같은 스킬 이름이 양쪽에
  있으면 플러그인 쪽을 씁니다.
- 파일 위치를 바꾸려면 `GPTAKU_USER_ROUTES` 환경변수를 씁니다.
- 직접 관리: `python3 <플러그인 경로>/hooks/user_routes.py list | remove <skill> | check "문장"`

## 플러그인 쪽에서 할 일

플러그인 루트에 `routing.json`을 두고 `plugin.json`에 `"dependencies": ["gptaku-core"]`를
추가합니다. core는 켜진 gptaku 플러그인의 `routing.json`만 읽으므로 core를 고칠
필요가 없습니다.

```json
{
  "routes": [
    {
      "skill": "plugin-name:skill-name",
      "when": "세션 규칙에 들어갈 한 줄 — 이 스킬을 써야 하는 상황",
      "priority": 10,
      "keywords": ["리서치해", "research"],
      "patterns": ["https?://"],
      "weak": ["리서치", "비교 분석"],
      "context": ["최근", "가격"],
      "exclude": ["코드", "함수"],
      "exclude_override": ["웹", "출처"],
      "weak_exclude": ["플러그인", "업데이트"],
      "aliases": ["plugin-name:command-name"],
      "any_mood": false
    }
  ]
}
```

| 필드 | 뜻 |
|---|---|
| `keywords`·`patterns` | 강한 근거(2점). 영문·숫자는 단어 경계, 한글은 앞쪽 경계로 대조하고 `patterns`는 정규식 |
| `weak`·`weak_patterns` | 그 말만으로는 의도가 갈리는 신호(1점). 같은 절에 강한 근거나 `context` 단어가 있을 때만 센다 |
| `exclude` | 이 단어가 있는 절의 근거는 버린다. `exclude_override` 단어가 요청 어디든 있으면 무시 |
| `weak_exclude` | 요청 어디든 있으면 `weak`를 쓰지 않는다(플러그인 자체를 고치는 이야기) |
| `aliases` | 명시 호출로 인정할 다른 이름. 여기 없는 `/plugin:command`는 지목하지 않는다 |
| `any_mood` | `true`면 요청형이 아닌 질문·불평에도 지목(도움말·문제 진단 스킬용) |

잘못된 라우트(필수 필드 누락, 잘못된 정규식 등)는 그 라우트만 건너뛰고 나머지는 동작합니다.

## 지목 규칙

1. 맨 앞이 `/`인 요청은 Claude Code가 직접 처리하므로 건너뜁니다.
2. 코드 블록·인라인 코드·큰따옴표 인용·파일 경로·목록/표 줄은 자료로 보고 뺀 뒤, 남은 지시 문장만 봅니다.
3. 지시 문장 속 `/플러그인:스킬`·`/플러그인`·선언된 별칭을 명시 호출로 봅니다. 토큰 뒤에 경로·확장자가
   붙으면 명령이 아니고, 바로 뒤에서 "취소/말고/대신"으로 물린 명령은 빼며, 남은 것 중 마지막을 고릅니다.
   gptaku 밖의 도구(`/chrome`, `/aside-browser` 등)를 직접 지목한 요청은 키워드로 덮어쓰지 않습니다
   (`/goal`·`/clear` 같은 내장 명령은 예외).
4. 명시 호출이 없으면 점수로 고릅니다. 요청형(~해줘·~봐·~하자·~할래 등)으로 끝나는 문장과, URL에 의문사(무슨·뭐·어떤 등)를
   붙여 묻는 문장("https://… 이거 무슨 내용이야")의 근거만 세고,
   완료·취소·금지·용어 언급("~라는 단어", "번역해")·과거 이야기("~해둔 거", "~하고 있었는데")·조건("~하면")
   절은 버리며, "~했으니까" 같은 배경 절은 절반만 셉니다. 줄바꿈은 문장 경계로 보므로 붙여 넣은 대화 속
   단어는 지시 문장의 근거가 되지 않습니다.
5. 1·2위가 완전히 동점이면 파일 순서로 정하지 않고 지목하지 않습니다.
6. 지시 문장이 500자를 넘으면 명시 호출만 봅니다.

## 끄기

환경변수 `GPTAKU_ROUTER=off`를 주면 모든 훅이 아무것도 넣지 않습니다. 플러그인을
비활성화하면 이 플러그인에 의존하는 gptaku 플러그인까지 꺼질 수 있으니 이 방법을
쓰세요. `claude -p`로 돌리는 봇·자동화는 대화형 세션과 환경이 구분되지 않으므로,
라우팅이 필요 없으면 그 프로세스에 `GPTAKU_ROUTER=off`를 주세요.

## 이미 gptaku 플러그인을 쓰고 있었다면

`claude plugin update`만으로는 새로 추가된 의존성이 설치되지 않습니다. 업데이트 후
세션에서 `/reload-plugins`를 한 번 실행하거나(Claude Code 문서 기준), 쓰던 플러그인을
`claude plugin install <이름>@gptaku-plugins`로 다시 설치하면 gptaku-core가 함께
설치됩니다.

## 테스트

```bash
python3 tools/test_gptaku_core_routes.py
```

`GPTAKU_CORE_PLUGIN_DIRS`는 테스트·개발용 덮어쓰기라 활성 여부 검사를 거치지 않습니다.

## 라이선스

MIT. [DISCLAIMER.md](DISCLAIMER.md)를 함께 확인하세요.
