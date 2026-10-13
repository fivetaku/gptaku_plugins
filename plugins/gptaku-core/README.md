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
      "keywords": ["리서치", "research"],
      "patterns": ["https?://"],
      "exclude": ["코드", "함수"]
    }
  ]
}
```

- `keywords`: 영문·숫자는 단어 경계로, 한글은 부분 문자열로 대조합니다.
- `patterns`: 정규식입니다.
- `exclude`: 하나라도 걸리면 이 스킬을 지목하지 않습니다.
- 여러 스킬이 맞으면 맞은 개수가 많은 쪽, 같으면 `priority`가 높은 쪽을 고릅니다.

## 지목 규칙

- 문장 어디든 `/플러그인:스킬` 또는 `/플러그인`이 적혀 있으면 그 스킬을 지목합니다.
- 500자가 넘거나 목록·표가 여러 줄인 요청은 붙여 넣은 자료로 보고 명시 호출만 봅니다.
- 플러그인 별칭(품앗이, 골잡이 등)·URL·"비교 분석"처럼 그 말만으로 의도가 갈리는
  신호는 `weak`로 두고, 행동 단어(`context`)가 함께 있을 때만 셉니다.

## 끄기

환경변수 `GPTAKU_ROUTER=off`를 주면 두 훅 모두 아무것도 넣지 않습니다. 플러그인을
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

## 라이선스

MIT. [DISCLAIMER.md](DISCLAIMER.md)를 함께 확인하세요.
