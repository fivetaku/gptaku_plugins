#!/usr/bin/env python3
"""validate_marketplace.py — 마켓플레이스/매니페스트 정합성 게이트.

cursor/plugins 의 scripts/validate-plugins.mjs 를 이 레포 관례(stdlib-only)로
이식 + 우리 실전 함정 검사를 추가한 것.

검사 항목:
  1. marketplace.json 파싱 + 필드 스키마(허용 키 외 거부, 필수 키, 타입)
  2. 엔트리별: source 디렉토리 존재, .claude-plugin/plugin.json 존재·파싱
  3. plugin.json 스키마: 허용 키, 타입, name 케밥케이스, version semver
     - `agents`는 파일 경로 "배열" (문자열이면 claude plugin validate 실패 — 실전 함정)
     - `skills`/`commands`는 디렉토리 "문자열"
  4. marketplace 엔트리 name == plugin.json name
  5. 선언된 컴포넌트 경로 실존 (agents 파일, skills/commands 디렉토리, hooks 파일)
  6. plugins/ 하위의 tracked 디렉토리 중 마켓 미등재 검출 (gitignored 는 제외)
  7. .gitmodules 의 path 가 index gitlink 와 일치 (잔존 항목 검출)
  8. --check-releases: 서브모듈 origin 에 v<version> 태그 존재 (네트워크, 옵트인)

사용:
    python3 tools/validate_marketplace.py                  # 1~7
    python3 tools/validate_marketplace.py --check-releases # 1~8
Exit 0 = clean, 1 = 위반. 의존성 없음(stdlib + git CLI).
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKETPLACE = os.path.join(ROOT, ".claude-plugin", "marketplace.json")

NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9._-]*[a-z0-9])?$")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)

MARKETPLACE_TOP_KEYS = {"name", "description", "owner", "plugins", "metadata", "$schema"}
MARKETPLACE_TOP_REQUIRED = {"name", "owner", "plugins"}
ENTRY_KEYS = {"name", "description", "source", "category", "tags", "strict"}
ENTRY_REQUIRED = {"name", "source"}
OWNER_KEYS = {"name", "url", "email"}

PLUGIN_KEYS = {
    "$schema", "name", "version", "description", "author", "license",
    "keywords", "homepage", "repository", "category", "tags",
    "commands", "skills", "agents", "hooks", "mcpServers",
}
PLUGIN_REQUIRED = {"name", "version", "description", "author", "license"}

errors = []
warnings = []


def fail(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def git(*args):
    """Run git in ROOT; return stdout ('' on failure)."""
    try:
        out = subprocess.run(
            ["git", "-C", ROOT, *args],
            capture_output=True, text=True, timeout=60,
        )
        return out.stdout if out.returncode == 0 else ""
    except Exception:
        return ""


def check_type(ctx, obj, key, expected, required=False):
    if key not in obj:
        if required:
            fail(f"{ctx}: 필수 키 누락 `{key}`")
        return None
    v = obj[key]
    if not isinstance(v, expected):
        names = expected.__name__ if isinstance(expected, type) else "/".join(t.__name__ for t in expected)
        fail(f"{ctx}: `{key}` 는 {names} 이어야 함 (현재 {type(v).__name__})")
        return None
    return v


def validate_component_paths(ctx, plugin_dir, manifest):
    # agents: 파일 경로 배열 (문자열이면 claude plugin validate 가 Invalid input)
    if "agents" in manifest:
        agents = manifest["agents"]
        if not isinstance(agents, list):
            fail(f"{ctx}: `agents` 는 파일 경로 배열이어야 함 — 문자열이면 "
                 f"`claude plugin validate` 가 실패한다 (현재 {type(agents).__name__})")
        else:
            for a in agents:
                if not isinstance(a, str):
                    fail(f"{ctx}: `agents` 항목이 문자열이 아님: {a!r}")
                elif not os.path.isfile(os.path.join(plugin_dir, a)):
                    fail(f"{ctx}: `agents` 경로 실존 안 함: {a}")
    # skills/commands: 디렉토리 문자열
    for key in ("skills", "commands"):
        if key in manifest:
            v = manifest[key]
            if not isinstance(v, str):
                fail(f"{ctx}: `{key}` 는 디렉토리 문자열이어야 함 (현재 {type(v).__name__})")
            elif not os.path.isdir(os.path.join(plugin_dir, v)):
                fail(f"{ctx}: `{key}` 디렉토리 실존 안 함: {v}")
    # hooks: 파일 경로 문자열 또는 인라인 객체
    if "hooks" in manifest:
        v = manifest["hooks"]
        if isinstance(v, str) and not os.path.isfile(os.path.join(plugin_dir, v)):
            fail(f"{ctx}: `hooks` 파일 실존 안 함: {v}")
        elif not isinstance(v, (str, dict)):
            fail(f"{ctx}: `hooks` 는 경로 문자열 또는 객체여야 함")
    # 경로 탈출 금지
    for key in ("skills", "commands", "hooks"):
        v = manifest.get(key)
        if isinstance(v, str) and (".." in v or v.startswith("/")):
            fail(f"{ctx}: `{key}` 경로가 플러그인 밖을 가리킴: {v}")
    for a in manifest.get("agents", []) if isinstance(manifest.get("agents"), list) else []:
        if isinstance(a, str) and (".." in a or a.startswith("/")):
            fail(f"{ctx}: `agents` 경로가 플러그인 밖을 가리킴: {a}")


def validate_plugin_manifest(entry_name, source):
    plugin_dir = os.path.normpath(os.path.join(ROOT, source))
    ctx = f"plugin `{entry_name}`"
    if not os.path.isdir(plugin_dir):
        fail(f"{ctx}: source 디렉토리 없음: {source}")
        return
    manifest_path = os.path.join(plugin_dir, ".claude-plugin", "plugin.json")
    if not os.path.isfile(manifest_path):
        fail(f"{ctx}: .claude-plugin/plugin.json 없음 ({source})")
        return
    try:
        with open(manifest_path, encoding="utf-8") as f:
            m = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        fail(f"{ctx}: plugin.json 파싱 실패 — {e}")
        return

    for k in m:
        if k not in PLUGIN_KEYS:
            fail(f"{ctx}: plugin.json 에 알 수 없는 키 `{k}`")
    for k in PLUGIN_REQUIRED:
        if k not in m:
            fail(f"{ctx}: plugin.json 필수 키 누락 `{k}`")

    name = check_type(ctx, m, "name", str)
    if name and not NAME_RE.match(name):
        fail(f"{ctx}: name `{name}` 이 소문자 케밥케이스 아님")
    if name and name != entry_name:
        fail(f"{ctx}: marketplace name `{entry_name}` != plugin.json name `{name}`")

    version = check_type(ctx, m, "version", str)
    if version and not SEMVER_RE.match(version):
        fail(f"{ctx}: version `{version}` 이 semver 아님")

    check_type(ctx, m, "description", str)
    check_type(ctx, m, "license", str)
    check_type(ctx, m, "keywords", list)
    author = check_type(ctx, m, "author", dict)
    if author is not None:
        if "name" not in author:
            fail(f"{ctx}: author.name 누락")
        for k in author:
            if k not in OWNER_KEYS:
                fail(f"{ctx}: author 에 알 수 없는 키 `{k}`")

    validate_component_paths(ctx, plugin_dir, m)
    return version


def main():
    check_releases = "--check-releases" in sys.argv

    # 1. marketplace.json
    if not os.path.isfile(MARKETPLACE):
        print("ERROR: .claude-plugin/marketplace.json 없음", file=sys.stderr)
        return 1
    try:
        with open(MARKETPLACE, encoding="utf-8") as f:
            market = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: marketplace.json 파싱 실패 — {e}", file=sys.stderr)
        return 1

    for k in market:
        if k not in MARKETPLACE_TOP_KEYS:
            fail(f"marketplace.json: 알 수 없는 키 `{k}`")
    for k in MARKETPLACE_TOP_REQUIRED:
        if k not in market:
            fail(f"marketplace.json: 필수 키 누락 `{k}`")
    owner = market.get("owner")
    if isinstance(owner, dict):
        if "name" not in owner:
            fail("marketplace.json: owner.name 누락")
        for k in owner:
            if k not in OWNER_KEYS:
                fail(f"marketplace.json: owner 에 알 수 없는 키 `{k}`")

    entries = market.get("plugins", [])
    seen = set()
    versions = {}
    for e in entries:
        if not isinstance(e, dict):
            fail(f"marketplace.json: 엔트리가 객체가 아님: {e!r}")
            continue
        for k in e:
            if k not in ENTRY_KEYS:
                fail(f"marketplace entry `{e.get('name', '?')}`: 알 수 없는 키 `{k}`")
        missing = ENTRY_REQUIRED - e.keys()
        if missing:
            fail(f"marketplace entry {e!r}: 필수 키 누락 {sorted(missing)}")
            continue
        name = e["name"]
        if not NAME_RE.match(name):
            fail(f"marketplace entry `{name}`: 소문자 케밥케이스 아님")
        if name in seen:
            fail(f"marketplace entry `{name}`: 이름 중복")
        seen.add(name)
        versions[name] = validate_plugin_manifest(name, e["source"])

    # 6. tracked plugins/* 디렉토리 중 마켓 미등재 (gitignored 제외)
    plugins_root = os.path.join(ROOT, "plugins")
    if os.path.isdir(plugins_root):
        for d in sorted(os.listdir(plugins_root)):
            path = os.path.join(plugins_root, d)
            if not os.path.isdir(path) or d in seen:
                continue
            ignored = subprocess.run(
                ["git", "-C", ROOT, "check-ignore", "-q", f"plugins/{d}"],
                capture_output=True,
            ).returncode == 0
            if ignored:
                continue
            tracked = bool(git("ls-files", f"plugins/{d}").strip()) or \
                f"plugins/{d}" in git("ls-files", "-s", "plugins").split()
            if tracked:
                fail(f"plugins/{d}: tracked 인데 marketplace.json 미등재")
            else:
                warn(f"plugins/{d}: untracked WIP (마켓 미등재 — 참고)")

    # 7. .gitmodules path ↔ index gitlink 일치
    gitmodules = os.path.join(ROOT, ".gitmodules")
    if os.path.isfile(gitmodules):
        declared = set()
        with open(gitmodules, encoding="utf-8") as f:
            for line in f:
                mm = re.match(r"\s*path\s*=\s*(.+)", line)
                if mm:
                    declared.add(mm.group(1).strip())
        gitlinks = set()
        for line in git("ls-files", "-s").splitlines():
            parts = line.split()
            if parts and parts[0] == "160000":
                gitlinks.add(line.split("\t")[-1])
        for p in sorted(declared - gitlinks):
            fail(f".gitmodules: `{p}` 항목이 index gitlink 에 없음 (잔존 항목)")
        for p in sorted(gitlinks - declared):
            fail(f".gitmodules: gitlink `{p}` 가 .gitmodules 에 선언 안 됨")

    # 8. 릴리즈 태그 (옵트인)
    if check_releases:
        for name, version in sorted(versions.items()):
            if not version:
                continue
            sub = os.path.join(ROOT, "plugins", name)
            if not os.path.isdir(os.path.join(sub, ".git")) and not os.path.isfile(os.path.join(sub, ".git")):
                continue  # 서브모듈 아님 (in-tree WIP)
            out = subprocess.run(
                ["git", "-C", sub, "ls-remote", "--tags", "origin", f"refs/tags/v{version}"],
                capture_output=True, text=True, timeout=60,
            )
            if out.returncode != 0:
                warn(f"plugin `{name}`: ls-remote 실패 — 태그 확인 불가")
            elif not out.stdout.strip():
                fail(f"plugin `{name}`: origin 에 태그 v{version} 없음 "
                     f"(버전 bump 후 릴리즈 미발행 — CLAUDE.md Step 2)")

    for w in warnings:
        print(f"WARN: {w}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        print(f"\n검증 실패: {len(errors)}건", file=sys.stderr)
        return 1
    print(f"OK: 마켓 엔트리 {len(entries)}개 전부 정합 (경고 {len(warnings)}건)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
