#!/usr/bin/env python3
"""gptaku_doctor.py — 마켓플레이스 배포 파이프라인 공용 진단기.

CLAUDE.md의 8단계 배포 체크리스트가 어긋났을 때 생기는 만성 증상
(캐시 버전 불일치, enabledPlugins 미등록, 닷파일 누락, installed_plugins.json
3중 불일치)을 플러그인 17종 전체에 대해 한 번에 대조한다.

상태값 4종:
  ok         — 축이 일치함
  warn       — 동작은 하지만 파이프라인 잔여물이 있음 (구버전 캐시 등)
  fail       — 구버전 로드/훅 미발화로 이어지는 실제 불일치
  unverified — 검증을 수행하지 않음 (네트워크 미사용, 프라이빗 플러그인 등).
               '없음'이 아니라 '확인 안 함'이다. fail로 반올림하지 않는다.

사용: python3 tools/gptaku_doctor.py [--all] [--json] [--network] [<plugin>...]
  --all      ok 축까지 전부 출력 (기본은 문제 축만)
  --json     기계 판독용 JSON 출력
  --network  gh CLI로 GitHub 릴리즈 태그까지 대조 (기본은 unverified)
"""

import argparse
import configparser
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
MARKET = "gptaku-plugins"
CACHE_ROOT = HOME / ".claude/plugins/cache" / MARKET
MARKET_ROOT = HOME / ".claude/plugins/marketplaces" / MARKET
INSTALLED_JSON = HOME / ".claude/plugins/installed_plugins.json"
SETTINGS_JSON = HOME / ".claude/settings.json"
# 개발 리포 위치. 테스트가 실제 plugins/를 읽지 않도록 env로 격리 가능
DEV_ROOT = Path(os.environ.get("GPTAKU_DEV_ROOT")
                or Path(__file__).resolve().parent.parent / "plugins")

C = {"ok": "\033[32m", "warn": "\033[33m", "fail": "\033[31m",
     "unverified": "\033[36m", "reset": "\033[0m", "bold": "\033[1m"}
SEVERITY = {"fail": 0, "warn": 1, "unverified": 2, "ok": 3}


def load_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def plugin_json_version(plugin_dir):
    data = load_json(plugin_dir / ".claude-plugin/plugin.json")
    return data.get("version") if isinstance(data, dict) else None


def git_submodule_shas():
    """마켓 클론 HEAD가 가리키는 서브모듈 SHA 맵. git 실패 시 None."""
    try:
        out = subprocess.run(
            ["git", "-C", str(MARKET_ROOT), "ls-tree", "HEAD", "plugins/"],
            capture_output=True, text=True, timeout=10, check=True).stdout
    except (subprocess.SubprocessError, OSError):
        return None
    shas = {}
    for line in out.splitlines():
        m = re.match(r"160000 commit ([0-9a-f]{40})\tplugins/(\S+)", line)
        if m:
            shas[m.group(2)] = m.group(1)
    return shas


def gitmodule_repos():
    """플러그인명 → 'owner/repo' 맵 (.gitmodules 기준)."""
    cp = configparser.ConfigParser()
    try:
        cp.read(MARKET_ROOT / ".gitmodules")
    except (OSError, configparser.Error):
        return {}
    repos = {}
    for section in cp.sections():
        path = cp[section].get("path", "")
        url = cp[section].get("url", "")
        m = re.search(r"github\.com[:/]([^/]+/[^/.]+)", url)
        if path.startswith("plugins/") and m:
            repos[path.split("/", 1)[1]] = m.group(1)
    return repos


def hook_script_paths(install_path):
    """hooks.json이 참조하는 ${CLAUDE_PLUGIN_ROOT} 상대 스크립트 경로들."""
    hooks_file = install_path / "hooks/hooks.json"
    if not hooks_file.exists():
        return None, []
    data = load_json(hooks_file)
    if data is None:
        return "unparsable", []
    # ${CLAUDE_PLUGIN_ROOT}/x 와 $CLAUDE_PLUGIN_ROOT/x 둘 다 포착
    paths = re.findall(r"\$\{?CLAUDE_PLUGIN_ROOT\}?([^\s\"'\\]+)", json.dumps(data))
    return "present", sorted(set(paths))


def check_plugin(name, entry, enabled_map, sub_shas, repos, network):
    """플러그인 1개의 축별 진단. [(axis, status, message, prescription)] 반환."""
    checks = []
    key = f"{name}@{MARKET}"
    cache_dir = CACHE_ROOT / name

    # ── 축 1: 등록 (installed_plugins.json + enabledPlugins) ──
    if entry is None:
        checks.append(("등록", "fail", "installed_plugins.json에 항목 없음",
                       f"/plugin install {name}@{MARKET} 또는 수동 설치 시 항목 추가"))
        return checks
    enabled = enabled_map.get(key)
    if enabled is True:
        checks.append(("enable", "ok", "enabledPlugins 등록됨", None))
    elif enabled is False:
        checks.append(("enable", "warn", "enabledPlugins=false (의도적 비활성이면 정상)",
                       None))
    else:
        checks.append(("enable", "fail",
                       "enabledPlugins에 항목 자체가 없음 — 훅·스킬이 로드되지 않음"
                       " (2026-08-24 ddiring 실사례)",
                       f"~/.claude/settings.json enabledPlugins에 "
                       f'"{key}": true 추가'))

    ver = entry.get("version")
    install_path = Path(entry.get("installPath", ""))

    # ── 축 2: 캐시 단일 버전 ──
    if not cache_dir.is_dir():
        checks.append(("캐시", "fail", "캐시 디렉토리 없음",
                       "CLAUDE.md Step 5 캐시 생성 수행"))
        return checks
    versions = sorted(p.name for p in cache_dir.iterdir() if p.is_dir())
    if versions == [ver]:
        checks.append(("캐시", "ok", f"단일 버전 {ver}", None))
    elif ver in versions:
        stale = [v for v in versions if v != ver]
        checks.append(("캐시", "warn",
                       f"구버전 캐시 잔존: {', '.join(stale)} (현행 {ver})",
                       " && ".join(f"trash {cache_dir}/{v}" for v in stale)))
    else:
        checks.append(("캐시", "fail",
                       f"installed 버전 {ver}이 캐시에 없음 (캐시: {versions})",
                       "CLAUDE.md Step 5~6 재수행 (캐시 생성 + installed_plugins.json 정정)"))

    # ── 축 3: installPath 실체 + 닷파일 함정 + plugin.json 버전 ──
    if not install_path.is_dir():
        checks.append(("경로", "fail", f"installPath 부재: {install_path}",
                       "CLAUDE.md Step 5 캐시 생성 후 Step 6 경로 정정"))
    elif not (install_path / ".claude-plugin/plugin.json").exists():
        checks.append(("닷파일", "fail",
                       ".claude-plugin/plugin.json 누락 — cp -R staging/* 닷파일 함정",
                       f'cp -R "{MARKET_ROOT}/plugins/{name}/." "{install_path}/" '
                       f'&& trash "{install_path}/.git"'))
    else:
        pv = plugin_json_version(install_path)
        if pv == ver:
            checks.append(("버전", "ok", f"plugin.json == installed == {ver}", None))
        else:
            checks.append(("버전", "fail",
                           f"plugin.json {pv} ≠ installed_plugins.json {ver}",
                           "CLAUDE.md Step 5~6 재수행 (둘 중 스테일한 쪽 정정)"))

    # ── 축 4: 마켓 클론 동기화 ──
    market_dir = MARKET_ROOT / "plugins" / name
    if not market_dir.is_dir() or not any(market_dir.iterdir()):
        checks.append(("마켓", "unverified",
                       "마켓 클론에 없음 (프라이빗/로컬 플러그인이면 정상)", None))
    else:
        mv = plugin_json_version(market_dir)
        if mv != ver:
            checks.append(("마켓", "fail",
                           f"마켓 클론 {mv} ≠ 설치본 {ver} — Step 4(git pull/"
                           f"submodule update) 또는 Step 5(캐시 교체) 누락",
                           f"cd {MARKET_ROOT} && git pull && "
                           f"git submodule update --init plugins/{name}"))
        else:
            checks.append(("마켓", "ok", f"마켓 클론 버전 일치 {mv}", None))
        sha = entry.get("gitCommitSha", "")
        if sub_shas is None:
            checks.append(("SHA", "unverified", "git ls-tree 실패 — 대조 안 함", None))
        elif name not in sub_shas:
            checks.append(("SHA", "unverified", "서브모듈 아님 (in-tree)", None))
        elif sha == sub_shas[name]:
            checks.append(("SHA", "ok", f"gitCommitSha 일치 {sha[:8]}", None))
        else:
            # 버전이 같아도 bump 없이 배포된 fix가 캐시에 빠졌을 수 있다 — 내용 대조
            try:
                r = subprocess.run(
                    ["diff", "-rq", str(market_dir), str(install_path),
                     "--exclude=.git", "--exclude=.in_use",
                     "--exclude=__pycache__", "--exclude=*.pyc",
                     "--exclude=.DS_Store"],
                    capture_output=True, text=True, timeout=30)
                content_differs = r.returncode != 0
            except (subprocess.SubprocessError, OSError):
                content_differs = None
            if content_differs:
                checks.append(("SHA", "fail",
                               f"캐시 내용이 마켓과 다름 (동일 버전 {ver}, "
                               f"bump 없이 배포된 fix 미반영 — SHA "
                               f"{sha[:8]}≠{sub_shas[name][:8]})",
                               f'cp -R "{market_dir}/." "{install_path}/" && '
                               f'trash "{install_path}/.git" 후 '
                               f"gitCommitSha를 {sub_shas[name][:8]}로 정정"))
            else:
                note = ("내용은 일치" if content_differs is False else "내용 대조 실패")
                checks.append(("SHA", "warn",
                               f"gitCommitSha {sha[:8]} ≠ 마켓 서브모듈 "
                               f"{sub_shas[name][:8]} ({note})",
                               "installed_plugins.json gitCommitSha를 마켓 서브모듈 SHA로 정정"))

    # ── 축 5: 개발 리포 드리프트 ──
    dev_dir = DEV_ROOT / name
    if dev_dir.is_dir() and any(dev_dir.iterdir()):
        dv = plugin_json_version(dev_dir)
        if dv and dv != ver:
            checks.append(("개발리포", "warn",
                           f"개발 리포 {dv} ≠ 배포본 {ver} — 미배포 변경 있음",
                           f"배포하려면 CLAUDE.md Step 1~8, 아니면 무시"))
        elif dv:
            checks.append(("개발리포", "ok", f"개발 리포 버전 일치 {dv}", None))

    # ── 축 6: 훅 probe (missing / broken / disabled 3분류) ──
    if install_path.is_dir():
        state, paths = hook_script_paths(install_path)
        if state == "unparsable":
            checks.append(("훅", "fail", "hooks/hooks.json 파싱 불가",
                           f"{install_path}/hooks/hooks.json 문법 확인"))
        elif state == "present":
            missing = [p for p in paths if not (install_path / p.lstrip("/")).exists()]
            empty = [p for p in paths if (install_path / p.lstrip("/")).exists()
                     and (install_path / p.lstrip("/")).stat().st_size == 0]
            if missing:
                checks.append(("훅", "fail",
                               f"훅 스크립트 missing: {', '.join(missing)}",
                               "캐시 재복사 (닷파일 함정 처방과 동일)"))
            elif empty:
                checks.append(("훅", "fail",
                               f"훅 스크립트 broken(0바이트): {', '.join(empty)}",
                               "캐시 재복사"))
            elif enabled is not True:
                checks.append(("훅", "warn",
                               f"훅 {len(paths)}개 정상이나 플러그인이 disabled 상태",
                               None))
            else:
                checks.append(("훅", "ok", f"훅 스크립트 {len(paths)}개 실체 확인", None))

    # ── 축 7: GitHub 릴리즈 태그 ──
    repo = repos.get(name)
    if not network:
        checks.append(("릴리즈", "unverified",
                       "네트워크 검증 안 함 (--network로 확인)", None))
    elif not repo:
        checks.append(("릴리즈", "unverified", "리포 주소 미확인 (.gitmodules에 없음)", None))
    else:
        try:
            r = subprocess.run(["gh", "release", "view", f"v{ver}", "-R", repo,
                                "--json", "tagName"],
                               capture_output=True, text=True, timeout=15)
            if r.returncode == 0:
                checks.append(("릴리즈", "ok", f"v{ver} 릴리즈 존재 ({repo})", None))
            else:
                checks.append(("릴리즈", "fail",
                               f"{repo}에 v{ver} 릴리즈 없음 — Step 2 누락",
                               f"cd plugins/{name} && gh release create v{ver} "
                               f"--title 'v{ver} — <요약>' --notes '<변경>' --target main"))
        except (subprocess.SubprocessError, OSError) as e:
            checks.append(("릴리즈", "unverified", f"gh 실행 실패: {e}", None))
    return checks


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("plugins", nargs="*", help="특정 플러그인만 진단 (기본: 전체)")
    ap.add_argument("--all", action="store_true", help="ok 축까지 전부 출력")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--network", action="store_true", help="GitHub 릴리즈 태그 대조")
    args = ap.parse_args()

    installed = load_json(INSTALLED_JSON) or {}
    settings = load_json(SETTINGS_JSON) or {}
    enabled_map = settings.get("enabledPlugins", {})
    plugin_entries = installed.get("plugins", {})
    sub_shas = git_submodule_shas()
    repos = gitmodule_repos()

    names = set()
    for k in plugin_entries:
        if k.endswith(f"@{MARKET}"):
            names.add(k.rsplit("@", 1)[0])
    if CACHE_ROOT.is_dir():
        names.update(p.name for p in CACHE_ROOT.iterdir() if p.is_dir())
    for k in enabled_map:
        if k.endswith(f"@{MARKET}"):
            names.add(k.rsplit("@", 1)[0])
    if args.plugins:
        unknown = set(args.plugins) - names
        if unknown:
            sys.exit(f"미설치 플러그인: {', '.join(sorted(unknown))}")
        names = set(args.plugins)

    report = {}
    for name in sorted(names):
        raw = plugin_entries.get(f"{name}@{MARKET}")
        entry = raw[0] if isinstance(raw, list) and raw else (
            raw if isinstance(raw, dict) else None)
        report[name] = check_plugin(name, entry, enabled_map, sub_shas, repos,
                                    args.network)

    counts = {"ok": 0, "warn": 0, "fail": 0, "unverified": 0}
    for checks in report.values():
        for _, status, _, _ in checks:
            counts[status] += 1

    # 종료코드는 두 출력 모드에서 동일해야 한다 — --json도 CI 게이트로 쓰인다
    if args.as_json:
        print(json.dumps({n: [dict(zip(("axis", "status", "message", "fix"), c))
                              for c in cs] for n, cs in report.items()},
                         ensure_ascii=False, indent=2))
        sys.exit(1 if counts["fail"] else 0)

    for name, checks in report.items():
        worst = min((c[1] for c in checks), key=SEVERITY.get)
        shown = checks if args.all else [c for c in checks if c[1] != "ok"]
        if not shown and not args.all:
            continue
        print(f"{C['bold']}{name}{C['reset']}  "
              f"[{C[worst]}{worst}{C['reset']}]")
        for axis, status, msg, fix in shown:
            print(f"  {C[status]}{status:10}{C['reset']} {axis}: {msg}")
            if fix:
                print(f"             └ 처방: {fix}")
    total = sum(counts.values())
    print(f"\n{C['bold']}합계{C['reset']} 축 {total}개 — "
          + ", ".join(f"{C[s]}{s} {n}{C['reset']}" for s, n in counts.items()))
    if not args.network:
        print("(릴리즈 태그는 unverified — 미검증이지 실패가 아님. --network로 대조 가능)")
    sys.exit(1 if counts["fail"] else 0)


if __name__ == "__main__":
    main()
