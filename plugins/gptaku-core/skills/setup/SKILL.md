---
name: setup
description: This skill should be used when the user wants gptaku-core to also route requests to skills that are not gptaku plugins — their personal skills in ~/.claude/skills and skills from other plugin marketplaces — so those are picked automatically without being named. It scans installed skills, drafts routing keywords from each skill's trigger phrases, asks for approval, writes ~/.claude/gptaku-core/routes.json, and self-checks the result. Korean triggers: "gptaku-core 셋업", "내 스킬도 라우팅", "내 스킬 자동으로 쓰게", "개인 스킬 라우팅 설정", "라우터에 스킬 추가", "라우트 다시 잡아줘". English triggers: "gptaku-core setup", "route my own skills", "add my skills to the router".
---

# gptaku-core setup — 내 스킬도 자동으로 쓰게

gptaku-core 라우터는 켜진 gptaku 플러그인의 `routing.json`과 함께 **사용자 라우트 파일**
`~/.claude/gptaku-core/routes.json`을 읽는다. 이 셋업은 그 파일을 사용자의 실제 스킬로 채운다.
파일 형식은 플러그인 `routing.json`과 같고, 개인 스킬(`~/.claude/skills/<name>`)은 콜론 없는
이름(`"skill": "my-skill"`), 다른 마켓 플러그인 스킬은 `"plugin:skill"`로 적는다.

도구: `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/user_routes.py" <scan|write|remove|check|list>`

## Step 1 — 스캔

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/user_routes.py" scan
```

결과의 `skills[]` 중 `routed: false`인 것이 대상이다. `explicit_only: true`(모델 자동 호출을 끈
스킬)는 라우트를 만들지 않는다. 각 항목의 `triggers`(설명 속 인용 문구)와 `draft_keywords`(요청 어미를
뗀 초안)를 출발점으로 쓴다.

## Step 2 — 초안 작성

대상마다 라우트 하나를 만든다. 원칙:

- `keywords`에는 **그 스킬만의 표현**만 넣는다. `"루프"`, `"인터뷰"`, `"wrap"`, `"watch"`, `"design review"`처럼
  다른 맥락에서도 흔한 말은 빼거나 `weak`(1점, 같은 절에 강한 근거·`context`가 있을 때만)로 내린다.
- 키워드는 요청 어미를 뗀 줄기로 쓴다(`"윤문해줘"` → `"윤문"`). 영문·숫자는 단어 경계로, 한글은 앞쪽
  경계로 대조된다.
- 코드 작업과 겹치는 스킬이 아니면 `exclude`에 `["코드", "함수", "테스트", "리팩터", "버그", "에러"]`를 넣는다.
- `when`은 세션 규칙에 그대로 들어가는 한 줄 설명이다(한국어, "~할 때").
- `priority`는 기본 20. 같은 일을 하는 스킬이 둘이면 사용자가 주로 쓰는 쪽을 높인다(그 반대는 이름을
  직접 부를 때만 걸리도록 그 이름만 `keywords`에 둔다).
- `"출첵"`처럼 한 단어로 부르는 스킬은 그 단어를 `keywords`에 넣으면 어미 없이도 걸린다.
- 같은 스킬이 `~/.claude/skills`와 플러그인 양쪽에 있으면(예: `cloudflare`와 `cloudflare:cloudflare`)
  사용자가 실제로 부르는 쪽 하나만 만든다.
- 트리거가 없거나 쓰임을 알 수 없는 스킬은 억지로 만들지 말고 표에 "보류"로 남긴다.

## Step 3 — 승인

표(스킬 · when · 대표 keywords · 보류 여부)로 보여 주고 AskUserQuestion으로 "전부 적용 / 고를게 /
취소"를 묻는다. 승인 전에는 파일을 쓰지 않는다. 무응답은 승인이 아니다.

## Step 4 — 쓰기

승인된 라우트만 임시 파일(`{"routes": [...]}`)에 담아 합친다. 같은 스킬은 교체되고 나머지 기존
사용자 라우트는 유지된다.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/user_routes.py" write /tmp/gptaku-user-routes.json
```

`invalid`가 나오면 그 라우트를 고쳐 다시 쓴다.

## Step 5 — 자체 점검

스킬마다 **걸려야 할 문장 2개**와 **걸리면 안 되는 문장 1개**(그 스킬 단어가 들어가지만 다른 일인 문장)를
만들어 한 번에 확인한다.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/user_routes.py" check "문장1" "문장2" ...
```

각 줄은 `지목된 스킬<TAB>문장`(없으면 `-`)이다. 기대와 다르면 키워드를 고쳐 Step 4부터 다시 한다.
gptaku 플러그인 스킬로 가야 할 문장(예: "구글 캘린더 일정 확인해줘")이 사용자 라우트로 빼앗기지
않는지도 한 줄 넣어 확인한다.

## Step 6 — 보고

적용한 스킬 수, 보류한 스킬과 이유, 점검 결과(기대와 다른 줄이 있었다면 고친 내용)를 짧게 보고한다.
새 라우트는 **다음 요청부터** 바로 적용되고, 세션 규칙 목록은 다음 세션 시작(또는 `/clear`)부터 반영된다.

## 관리

- 스킬을 새로 설치했으면 이 셋업을 다시 돌린다(이미 라우트가 있는 스킬은 `routed: true`로 나와 건너뛴다).
- 지우기: `user_routes.py remove <skill>` · 현재 목록: `user_routes.py list`
- 라우터를 잠시 끄기: 환경변수 `GPTAKU_ROUTER=off`
