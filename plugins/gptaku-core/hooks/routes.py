"""켜진 gptaku 플러그인의 routing.json을 모아 요청과 대조한다.

각 플러그인은 루트에 routing.json을 두고 자기 스킬의 의도 키워드를 선언한다.
core는 그 목록만 읽으므로 새 플러그인이 추가돼도 여기를 고칠 필요가 없다.
"""
import json, os, re, sys, unicodedata

MARKET = "@gptaku-plugins"
CONFIG = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def _read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _enabled_map():
    """사용자 → 프로젝트 → 프로젝트 로컬 순으로 enabledPlugins를 합친다(뒤가 이긴다).
    사용자 설정을 읽지 못하면 None — 활성 여부를 확정할 수 없으므로 지목하지 않는다."""
    try:
        merged = dict(_read_json(os.path.join(CONFIG, "settings.json")).get("enabledPlugins", {}))
    except Exception:
        return None
    project = os.environ.get("CLAUDE_PROJECT_DIR")
    if project:
        for name in ("settings.json", "settings.local.json"):
            try:
                merged.update(_read_json(os.path.join(project, ".claude", name)).get("enabledPlugins", {}))
            except Exception:
                pass
    return merged


def plugin_dirs():
    # GPTAKU_CORE_PLUGIN_DIRS는 테스트·개발용 덮어쓰기다(활성 여부 검사를 거치지 않는다)
    dirs = [d for d in os.environ.get("GPTAKU_CORE_PLUGIN_DIRS", "").split(os.pathsep) if d]
    enabled = _enabled_map()
    if enabled is None:
        return dirs
    try:
        installed = _read_json(os.path.join(CONFIG, "plugins", "installed_plugins.json"))["plugins"]
    except Exception:
        installed = {}
    for key, entries in installed.items():
        if not key.endswith(MARKET) or enabled.get(key) is False:
            continue
        for e in entries:
            if e.get("scope") == "user" and e.get("installPath"):
                dirs.append(e["installPath"])
                break
    return dirs


LIST_FIELDS = ("keywords", "patterns", "weak", "weak_patterns", "context", "exclude",
               "exclude_override", "weak_exclude", "aliases")


def _valid(r):
    """필수 필드·타입·정규식을 검사한다. 잘못된 라우트 하나 때문에 훅 전체가 멈추지 않게 한다."""
    if not isinstance(r, dict) or not isinstance(r.get("skill"), str) or ":" not in r["skill"]:
        return False
    if not isinstance(r.get("when", ""), str) or not isinstance(r.get("priority", 0), (int, float)):
        return False
    for k in LIST_FIELDS:
        v = r.get(k, [])
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            return False
    try:
        for k in ("patterns", "weak_patterns"):
            for pat in r.get(k, []):
                re.compile(pat)
    except re.error:
        return False
    return True


def load_routes():
    routes, seen = [], set()
    for d in plugin_dirs():
        try:
            data = _read_json(os.path.join(d, "routing.json"))
        except Exception:
            continue
        for r in data.get("routes", []) if isinstance(data, dict) else []:
            if not _valid(r):
                sys.stderr.write(f"gptaku-core: {d}/routing.json의 잘못된 라우트를 건너뜀\n")
                continue
            if r["skill"] not in seen:
                seen.add(r["skill"])
                routes.append(r)
    return routes


def _norm(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s).lower()).strip()


def _span(keyword, text):
    """키워드가 처음 나온 (시작, 끝). 없으면 None."""
    k = _norm(keyword)
    if re.fullmatch(r"[a-z0-9 .+-]+", k):
        # 이메일·도메인·경로 조각(foo@naver.com, 20-knowledge/research/)은 단어로 치지 않는다
        m = re.search(r"(?<![a-z0-9@./_-])" + re.escape(k) + r"(?![a-z0-9/_-])(?!\.[a-z])", text)
    elif re.match(r"[가-힣]", k):
        # 한글은 조사가 뒤에 붙으므로 앞쪽 경계만 본다("크레딧" 속 "레딧"을 막는다)
        m = re.search(r"(?<![가-힣])" + re.escape(k), text)
    else:
        i = text.find(k)
        return (i, i + len(k)) if i >= 0 else None
    return m.span() if m else None


def _hit(keyword, text):
    return _span(keyword, text) is not None


# --- 지시와 자료 분리 -------------------------------------------------------
FENCE = re.compile(r"```.*?(?:```|$)", re.S)
INLINE = re.compile(r"`[^`\n]*`")
QUOTED = re.compile(r'"[^"\n]*"|“[^”\n]*”|「[^」\n]*」')
PATHS = re.compile(r"'[~/][^'\n]*'|(?<![\w:/])[~/][^\s/]*/[^\s]*")  # 파일 경로 속 단어는 근거가 아니다
LIST_LINE = re.compile(r"^\s*(?:[-*>|#]|\*\*|\d+[.)])\s?")
LONG_PROMPT = 500  # 지시 부분이 이보다 길면 명시 호출만 본다


def _instruction(prompt):
    """코드 블록·인라인 코드·큰따옴표 인용·목록/표/헤딩 줄은 자료로 보고 빼고, 사용자 지시만 남긴다."""
    s = unicodedata.normalize("NFKC", prompt)
    s = re.sub(r"[ \t\u3000]{2,}", "\n", s)  # 원문의 두 칸 이상 공백은 문장 경계(인용을 지운 자리와 구분하려고 먼저 바꾼다)
    s = FENCE.sub(" ", s)
    s = INLINE.sub(" ", s)
    s = QUOTED.sub(" ", s)
    s = PATHS.sub(" ", s)
    # 줄바꿈은 문장 경계로 남긴다(붙여 넣은 대화가 지시 문장과 한 덩어리가 되지 않게)
    lines = [line for line in s.splitlines() if not LIST_LINE.match(line)]
    lines = [re.sub(r"\s+", " ", x).strip() for x in lines]
    out = []
    for x in filter(None, lines):
        # URL만 있는 줄은 다음 줄의 지시("이 내용 확인해봐")와 한 문장으로 본다
        if out and URL_ONLY.match(out[-1]):
            out[-1] += " " + x
        else:
            out.append(x)
    return "\n".join(out).lower()


URL_ONLY = re.compile(r"^(?:https?://\S+\s*)+$")


# --- 명시 호출 ---------------------------------------------------------------
EXPLICIT = re.compile(r"(?<![\w/.:-])/([a-z0-9][a-z0-9-]*(?::[a-z0-9][a-z0-9-]*)?)(?![a-z0-9/:_-])(?!\.[a-z0-9])")
CANCELLED = re.compile(r"(취소|말고|빼고|대신|하지\s*마|쓰지\s*마|실행하지)")


def _explicit(text, routes):
    """문장 속 '/plugin:skill'·'/plugin'·선언된 별칭만 인정한다. 바로 뒤에서 취소된 명령은 빼고,
    남은 것 중 마지막을 고른다. 등록되지 않은 이름을 다른 스킬로 바꾸지 않는다."""
    table = {}
    for r in routes:
        table[r["skill"]] = r
        plugin, _, name = r["skill"].partition(":")
        if name == plugin:
            table.setdefault(plugin, r)
        for a in r.get("aliases", []):
            table.setdefault(a, r)
    chosen = None
    for m in EXPLICIT.finditer(text):
        if m.group(1) not in table:
            if m.group(1) not in BUILTIN:
                chosen = chosen or FOREIGN
            continue
        r = table.get(m.group(1))
        if r and not CANCELLED.search(text[m.end():m.end() + 15]):
            chosen = r
    return chosen


# 일을 대신하지 않는 Claude Code 내장 명령은 "다른 도구를 골랐다"로 보지 않는다("/goal로 돌릴 수 있게")
BUILTIN = {"goal", "clear", "compact", "model", "config", "plugin", "plugins", "reload-plugins", "resume",
           "init", "memory", "help", "fast", "effort", "login", "logout", "status", "cost", "doctor",
           "hooks", "permissions", "agents", "mcp", "exit", "loop", "context", "rewind", "export"}
FOREIGN = {"skill": None}  # 사용자가 gptaku 밖의 명령(/chrome, /aside-browser 등)을 직접 지목했다


# --- 절 단위 점수 ------------------------------------------------------------
# 문장부호는 뒤에 공백·끝이 올 때만 자른다(URL 속 . ? 에서 자르지 않는다)
CLAUSE_SPLIT = re.compile(r"[.!?;,]+(?=\s|$)|\n+|(?<=니까)\s|(?<=는데)\s|(?<=지만)\s|(?<=[났었았했])고\s|(?<=하면)\s|(?<=으면)\s")
DROP = re.compile(r"(완료(?:했|됐|된|함|$)|끝났|끝냈|했었|취소|말고|빼고|하지\s*마|하지\s*말|열지\s*마|쓰지\s*마|"
                  r"만들지\s*마|접근하지\s*마|실행하지\s*마|안\s*써|안\s*쓰|필요\s*없|했던\s*(?:거|것|내용)|이?라는\s*(?:단어|용어|말|표현|문장|이름)|번역해|"
                  r"뜻이\s*뭐|무슨\s*뜻|무엇인지|개념만|있었|[었았했]던|(?:하|으)면$|(?:작성|정리|리서치|조사|분석|검토|해|어)\s?(?:한|둔)\s*(?:거|것|내용|자료|결과)|(?:^|\s)한\s*거)")
BACKGROUND = re.compile(r"(니까|으니|는데|지만)$")


def _clauses(text):
    """(절, 가중치). 완료·취소·금지·용어 언급 절은 0, '~했으니까' 같은 배경 절은 0.5."""
    out = []
    for c in CLAUSE_SPLIT.split(text):
        c = c.strip()
        if not c:
            continue
        w = 0.0 if DROP.search(c) else 0.5 if BACKGROUND.search(c) else 1.0
        out.append((c, w))
    return out


def _evidence(c, r):
    """한 절에서 (강한 근거 수, 약한 근거 수, 근거 목록). 겹치는 표현은 한 번만 센다."""
    strong = [(_span(k, c), k) for k in r.get("keywords", [])]
    strong += [(re.search(p, c).span() if re.search(p, c) else None, p) for p in r.get("patterns", [])]
    weak = [(_span(k, c), k) for k in r.get("weak", [])]
    weak += [(re.search(p, c).span() if re.search(p, c) else None, p) for p in r.get("weak_patterns", [])]
    strong = [x for x in strong if x[0]]
    weak = [x for x in weak if x[0]]
    if weak and any(_hit(k, c) for k in r.get("weak_exclude", [])):
        weak = []
    # 약한 근거는 같은 절에 강한 근거나 행동 단어(context)가 있을 때만 인정한다
    if weak and not strong and not any(_norm(k) in c for k in r.get("context", [])):
        weak = []
    taken, n_strong, n_weak, why = [], 0, 0, []
    for kind, items in (("s", strong), ("w", weak)):
        for (a, b), k in sorted(items, key=lambda x: (x[0][0], -(x[0][1] - x[0][0]))):
            if any(a < y and x < b for x, y in taken):
                continue
            taken.append((a, b)); why.append(k)
            if kind == "s": n_strong += 1
            else: n_weak += 1
    return n_strong, n_weak, why


SENTENCE_SPLIT = re.compile(r"[.!?]+(?=\s|$)|\n+|\s{2,}")
TRAIL = re.compile(r"[\s?!.~…ㅋㅎㅠㅜ^)]+$")
# 요청·제안으로 끝나는 문장: ~해줘 ~봐 ~하자 ~할래 ~가져와 ~만들어 ~할까 ...
REQUEST_END = re.compile(r"(줘|봐|해|라|자|래|와|어|아|려|놔|싶음|싶어|싶다|세요|래요|까요|봐요|줘요|부탁|(?<=[할볼갈될줄낼쓸만올])까)$")  # "~니까"는 요청이 아니다
NOT_REQUEST = re.compile(r"(잖아|[었았했겠]어|거야|건가요|던데)$")


def _sentences(text):
    return [x.strip() for x in SENTENCE_SPLIT.split(text) if x and x.strip()]


URL = re.compile(r"https?://\S+")
# URL을 주고 묻는 문장("https://… 이거 무슨 내용이야")은 요청형 어미가 없어도 그 페이지를 읽어 달라는 요청이다
URL_QUESTION = re.compile(r"(무슨|뭐|뭘|무엇|어떤|어떻|어디|언제|누가|얼마|몇)")


def _is_request(sentence):
    """문장 안 어느 절이든 요청형으로 끝나면 요청이다("그려줘, 주제는 ~" · "요약해줘 https://…")."""
    if URL.search(sentence) and URL_QUESTION.search(URL.sub(" ", sentence)):
        return True
    s = URL.sub(" ", sentence)
    ends = [TRAIL.sub("", c) for c in CLAUSE_SPLIT.split(s) if c and c.strip()]
    return any(REQUEST_END.search(e) and not NOT_REQUEST.search(e) for e in ends)


def score(text, r):
    """(점수, 근거). 강한 근거 2점, 약한 근거 1점에 절 가중치를 곱한다.

    - 요청형으로 끝나는 문장 안의 근거만 센다("~나을거같음", "~했냐?" 같은 피드백·질문은 지목하지 않는다).
      도움말·불평형 스킬은 routing.json에 "any_mood": true로 예외를 둔다.
    - exclude가 걸린 절은 그 라우트의 근거에서 빠진다(exclude_override 단어가 요청 어디든 있으면 무시).
    - weak_exclude는 요청 전체에서 본다(플러그인 자체를 고치는 이야기면 별칭을 근거로 쓰지 않는다)."""
    override = any(_hit(k, text) for k in r.get("exclude_override", []))
    dev_talk = any(_hit(k, text) for k in r.get("weak_exclude", []))
    total, why = 0.0, []
    for sent in _sentences(text):
        if not r.get("any_mood") and not _is_request(sent):
            continue
        for c, w in _clauses(sent):
            if not w or (not override and any(_hit(k, c) for k in r.get("exclude", []))):
                continue
            s, k, ws = _evidence(c, dict(r, weak=[] if dev_talk else r.get("weak", []),
                                         weak_patterns=[] if dev_talk else r.get("weak_patterns", [])))
            total += w * (2 * s + k)
            why += ws
    return total, why


def match(prompt, routes):
    """가장 점수가 높은 스킬 하나를 돌려준다. 근거가 없거나, 1·2위가 완전히 동점이면 None."""
    raw = _norm(prompt)
    if not raw or raw.startswith("/"):
        return None  # 맨 앞 슬래시 명령은 Claude Code가 직접 처리한다
    text = _instruction(prompt)
    hit = _explicit(text, routes)
    if hit is FOREIGN:
        return None
    if hit or len(text) > LONG_PROMPT:
        return hit
    ranked = sorted(((score(text, r)[0], r.get("priority", 0), r) for r in routes),
                    key=lambda x: (x[0], x[1]), reverse=True)
    if not ranked or ranked[0][0] <= 0:
        return None
    if len(ranked) > 1 and ranked[1][0] > 0 and (ranked[0][0], ranked[0][1]) == (ranked[1][0], ranked[1][1]):
        return None  # 의미로 가를 수 없는 동점은 파일 순서로 정하지 않고 지목을 포기한다
    return ranked[0][2]
