#!/usr/bin/env python3
"""사용자 라우트(~/.claude/gptaku-core/routes.json) 관리 — /gptaku-core:setup이 쓰는 도구.

  user_routes.py scan              라우트가 없는 개인 스킬·다른 마켓 플러그인 스킬과 트리거 초안(JSON)
  user_routes.py write <draft>     초안 파일의 routes를 사용자 파일에 합친다(같은 스킬은 교체)
  user_routes.py remove <skill>…   사용자 파일에서 라우트를 뺀다
  user_routes.py check <문장>…     각 문장이 어느 스킬로 지목되는지(플러그인+사용자 라우트 전체 기준)
  user_routes.py list              현재 사용자 라우트
"""
import glob
import json
import os
import re
import sys

sys.dont_write_bytecode = True
HOOKS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HOOKS)
import routes as R  # noqa: E402

QUOTE = re.compile(r'"([^"\n]{2,60})"|“([^”\n]{2,60})”|「([^」\n]{2,60})」')
ENDING = re.compile(r"\s*(?:해\s*줘|해\s*주세요|줘|주세요|해\s*봐|봐\s*줘|해|하자|할래|돌려\s*줘)$")


def _frontmatter(path):
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return {}
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    meta, key = {}, None
    for line in m.group(1).splitlines():
        km = re.match(r"([A-Za-z_-]+):\s*(.*)$", line)
        if km and not line.startswith(" "):
            key, value = km.group(1), km.group(2).strip()
            meta[key] = "" if value in (">", ">-", "|", "|-") else value.strip("'\"")
        elif key:
            meta[key] = (meta[key] + " " + line.strip()).strip()
    return meta


def _triggers(description):
    found = []
    for m in QUOTE.finditer(description):
        phrase = next(g for g in m.groups() if g).strip()
        if phrase.startswith("/") or phrase in found:
            continue
        found.append(phrase)
    return found


def _keyword(phrase):
    k = ENDING.sub("", R._norm(phrase)).strip(" .?!~")
    return k if len(k) >= 2 else None


def _candidates():
    """(스킬 이름, SKILL.md 경로). 개인 스킬은 콜론 없는 이름, 다른 마켓 플러그인은 plugin:skill."""
    out = []
    for path in sorted(glob.glob(os.path.join(R.CONFIG, "skills", "*", "SKILL.md"))):
        name = _frontmatter(path).get("name") or os.path.basename(os.path.dirname(path))
        out.append((name, path))
    enabled = R._enabled_map() or {}
    try:
        installed = R._read_json(os.path.join(R.CONFIG, "plugins", "installed_plugins.json"))["plugins"]
    except Exception:
        installed = {}
    for key, entries in sorted(installed.items()):
        if key.endswith(R.MARKET) or enabled.get(key) is not True:
            continue
        plugin = key.split("@", 1)[0]
        root = next((e.get("installPath") for e in entries if e.get("installPath")), None)
        for path in sorted(glob.glob(os.path.join(root or "/nonexistent", "skills", "*", "SKILL.md"))):
            out.append((f"{plugin}:{os.path.basename(os.path.dirname(path))}", path))
    return out


def _user_file():
    """없으면 빈 목록. 있는데 읽을 수 없으면 None — 빈 목록으로 덮어쓰면 기존 라우트가 사라진다."""
    try:
        data = R._read_json(R.USER_ROUTES)
    except FileNotFoundError:
        return {"routes": []}
    except Exception:
        return None
    return data if isinstance(data, dict) and isinstance(data.get("routes"), list) else None


def _unreadable():
    print(json.dumps({"ok": False, "error": f"{R.USER_ROUTES}를 읽을 수 없어 건드리지 않았다. 파일을 고치거나 옮긴 뒤 다시 실행"},
                     ensure_ascii=False))
    return 1


def _save(data):
    os.makedirs(os.path.dirname(R.USER_ROUTES), exist_ok=True)
    tmp = R.USER_ROUTES + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, R.USER_ROUTES)


def scan():
    routed = {r["skill"] for r in R.load_routes()}
    rows = []
    for skill, path in _candidates():
        meta = _frontmatter(path)
        triggers = _triggers(meta.get("description", ""))
        rows.append({
            "skill": skill,
            "path": path,
            "routed": skill in routed,
            "explicit_only": meta.get("disable-model-invocation", "").lower() == "true",
            "description": meta.get("description", "")[:600],
            "triggers": triggers,
            "draft_keywords": [k for k in dict.fromkeys(_keyword(t) for t in triggers) if k],
        })
    print(json.dumps({"user_routes": R.USER_ROUTES, "skills": rows}, ensure_ascii=False, indent=1))


def write(draft_path):
    draft = R._read_json(draft_path)
    incoming = draft.get("routes", []) if isinstance(draft, dict) else []
    bad = [r.get("skill") if isinstance(r, dict) else r for r in incoming if not R._valid(r, user=True)]
    if bad:
        print(json.dumps({"ok": False, "invalid": bad}, ensure_ascii=False))
        return 1
    data = _user_file()
    if data is None:
        return _unreadable()
    names = {r["skill"] for r in incoming}
    data["routes"] = [r for r in data["routes"] if r.get("skill") not in names] + incoming
    _save(data)
    print(json.dumps({"ok": True, "file": R.USER_ROUTES, "written": sorted(names), "total": len(data["routes"])},
                     ensure_ascii=False))
    return 0


def remove(skills):
    data = _user_file()
    if data is None:
        return _unreadable()
    before = len(data["routes"])
    data["routes"] = [r for r in data["routes"] if r.get("skill") not in set(skills)]
    _save(data)
    print(json.dumps({"ok": True, "removed": before - len(data["routes"]), "total": len(data["routes"])}))
    return 0


def check(prompts):
    table = R.load_routes()
    for p in prompts:
        m = R.match(p, table)
        print(f"{m['skill'] if m else '-'}\t{p}")
    return 0


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "scan":
        scan()
        return 0
    if cmd == "write" and len(rest) == 1:
        return write(rest[0])
    if cmd == "remove" and rest:
        return remove(rest)
    if cmd == "check" and rest:
        return check(rest)
    if cmd == "list":
        data = _user_file()
        if data is None:
            return _unreadable()
        print(json.dumps(data, ensure_ascii=False, indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
