"""켜진 gptaku 플러그인의 routing.json을 모아 요청과 대조한다.

각 플러그인은 루트에 routing.json을 두고 자기 스킬의 의도 키워드를 선언한다.
core는 그 목록만 읽으므로 새 플러그인이 추가돼도 여기를 고칠 필요가 없다.
"""
import json, os, re, unicodedata

MARKET = "@gptaku-plugins"
CONFIG = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def _read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _enabled_map():
    try:
        return _read_json(os.path.join(CONFIG, "settings.json")).get("enabledPlugins", {})
    except Exception:
        return {}


def plugin_dirs():
    dirs = [d for d in os.environ.get("GPTAKU_CORE_PLUGIN_DIRS", "").split(os.pathsep) if d]
    try:
        installed = _read_json(os.path.join(CONFIG, "plugins", "installed_plugins.json"))["plugins"]
    except Exception:
        installed = {}
    enabled = _enabled_map()
    for key, entries in installed.items():
        if not key.endswith(MARKET) or enabled.get(key) is False:
            continue
        for e in entries:
            if e.get("scope") == "user" and e.get("installPath"):
                dirs.append(e["installPath"])
                break
    return dirs


def load_routes():
    routes, seen = [], set()
    for d in plugin_dirs():
        try:
            data = _read_json(os.path.join(d, "routing.json"))
        except Exception:
            continue
        for r in data.get("routes", []):
            if r.get("skill") and r["skill"] not in seen:
                seen.add(r["skill"])
                routes.append(r)
    return routes


def _norm(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s).lower()).strip()


def _hit(keyword, text):
    k = _norm(keyword)
    if re.fullmatch(r"[a-z0-9 .+-]+", k):
        # 이메일·도메인·경로 조각(foo@naver.com, 20-knowledge/research/)은 단어로 치지 않는다
        return re.search(r"(?<![a-z0-9@./_-])" + re.escape(k) + r"(?![a-z0-9/_-])(?!\.[a-z])", text) is not None
    if re.match(r"[가-힣]", k):
        # 한글은 조사가 뒤에 붙으므로 앞쪽 경계만 본다("크레딧" 속 "레딧"을 막는다)
        return re.search(r"(?<![가-힣])" + re.escape(k), text) is not None
    return k in text


def _pasted(prompt):
    """목록·표·헤딩이 여러 줄이면 붙여 넣은 자료로 본다."""
    marks = ("- ", "* ", "| ", "#", "**", "> ")
    return sum(line.strip().startswith(marks) for line in prompt.splitlines()) >= 2


LONG_PROMPT = 500  # 이보다 긴 요청은 붙여 넣은 자료일 때가 많아 명시 호출만 본다
EXPLICIT = re.compile(r"(?<![\w/])/([a-z0-9][a-z0-9-]*(?::[a-z0-9][a-z0-9-]*)?)")


def _explicit(text, routes):
    """문장 어디든 '/plugin:skill' 또는 '/plugin'으로 적힌 스킬을 찾는다."""
    by_full = {r["skill"]: r for r in routes}
    by_plugin = {}
    for r in routes:
        plugin, _, name = r["skill"].partition(":")
        if name == plugin or plugin not in by_plugin:
            by_plugin[plugin] = r
    for m in EXPLICIT.finditer(text):
        tok = m.group(1)
        if tok in by_full:
            return by_full[tok]
        # '/plugin' 또는 라우트에 없는 '/plugin:command'는 그 플러그인의 대표 스킬로 본다
        plugin = tok.split(":")[0]
        if plugin in by_plugin:
            return by_plugin[plugin]
    return None


def score(text, r):
    """(점수, 근거 목록). keywords·patterns는 강한 근거(2점)다. weak는 강한 근거나
    context 단어가 함께 있을 때만 1점씩 더한다("비교 분석"·URL·플러그인 별칭처럼
    그 말만으로는 의도가 갈리는 신호는 단독으로 지목하지 않는다)."""
    if any(_hit(k, text) for k in r.get("exclude", [])):
        return 0, []
    why = [k for k in r.get("keywords", []) if _hit(k, text)]
    why += [p for p in r.get("patterns", []) if re.search(p, text)]
    weak = [k for k in r.get("weak", []) if _hit(k, text)]
    weak += [p for p in r.get("weak_patterns", []) if re.search(p, text)]
    if weak and any(_hit(k, text) for k in r.get("weak_exclude", [])):
        weak = []
    # context는 조사·어미처럼 앞 단어에 붙어 나오므로 경계 없이 부분 문자열로 본다
    if weak and not why and not any(_norm(k) in text for k in r.get("context", [])):
        weak = []
    return len(why) * 2 + len(weak), why + weak


def match(prompt, routes):
    """가장 점수가 높은 스킬 하나를 돌려준다. 근거가 없거나 exclude에 걸리면 None."""
    text = _norm(prompt)
    if not text or text.startswith("/"):
        return None
    hit = _explicit(text, routes)
    if hit or len(text) > LONG_PROMPT or _pasted(prompt):
        return hit
    best = None
    for r in routes:
        sc, _ = score(text, r)
        if sc and (best is None or (sc, r.get("priority", 0)) > best[0]):
            best = ((sc, r.get("priority", 0)), r)
    return best[1] if best else None
