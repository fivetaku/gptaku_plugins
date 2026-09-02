#!/usr/bin/env python3
"""test_gptaku_doctor.py — gptaku_doctor.py 결함 주입 검증.

격리된 가짜 HOME에 마켓/캐시/매니페스트 픽스처를 세우고, 축별로 고장을 하나씩
주입해 doctor가 그 축을 정확한 status로 잡는지 대조한다. 실제 설치 상태는
건드리지 않는다 — HOME, 개발 리포(GPTAKU_DEV_ROOT), gh(PATH 선두의 가짜 실행파일)
셋 모두 픽스처로 바꿔 끼우므로 7축 전부가 네트워크 없이 검증된다.

clean 케이스가 전 축 ok여야 오탐 없음도 함께 보장된다.

사용: python3 tools/test_gptaku_doctor.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DOCTOR = Path(__file__).resolve().parent / "gptaku_doctor.py"
MARKET = "gptaku-plugins"
FAKE_SHA_A = "a" * 40
FAKE_SHA_B = "b" * 40

# (플러그인, 기대 축, 기대 status) — 주입한 고장이 이 축에서 이 status로 잡혀야 한다
EXPECTATIONS = [
    ("clean",           None,     None),        # 전 축 ok (오탐 없음)
    ("no-enable",       "enable", "fail"),
    ("stale-cache",     "캐시",   "warn"),
    ("no-cache",        "캐시",   "fail"),
    ("dotfile-trap",    "닷파일", "fail"),
    ("ver-mismatch",    "버전",   "fail"),
    ("market-drift",    "마켓",   "fail"),
    ("content-drift",   "SHA",    "fail"),
    ("sha-only",        "SHA",    "warn"),
    ("hook-missing",    "훅",     "fail"),
    ("hook-empty",      "훅",     "fail"),
    ("not-installed",   "등록",   "fail"),
    ("path-missing",    "경로",   "fail"),      # installPath가 캐시 밖을 가리킴
    ("dev-drift",       "개발리포", "warn"),    # 개발 리포 버전 앞섬 (env 격리된 DEV_ROOT)
    ("hook-unbraced",   "훅",     "fail"),      # $CLAUDE_PLUGIN_ROOT (중괄호 없음) 참조 미존재
    ("content-noise",   "SHA",    "warn"),      # __pycache__/.DS_Store만 다름 → 오탐 금지
    ("release-missing", "릴리즈", "fail"),      # 가짜 gh가 이 리포만 404
]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def make_plugin_tree(root, name, version, *, dotfile=True, hooks=None,
                     extra_file=None, braced=True):
    """플러그인 디렉토리 하나를 만든다. hooks=스크립트 상대경로 or None."""
    root.mkdir(parents=True, exist_ok=True)
    if dotfile:
        write_json(root / ".claude-plugin/plugin.json", {
            "name": name, "version": version, "description": f"{name} fixture",
            "author": {"name": "test"}, "license": "MIT",
        })
    (root / "README.md").write_text(f"# {name} {version}\n")
    if hooks is not None:
        write_json(root / "hooks/hooks.json", {"hooks": {"Stop": [{"hooks": [
            {"type": "command",
             "command": (f'bash "${{CLAUDE_PLUGIN_ROOT}}{hooks}" stop' if braced
                         else f'bash "$CLAUDE_PLUGIN_ROOT{hooks}" stop'),
             "timeout": 10}]}]}})
    if extra_file:
        (root / extra_file).write_text("drifted content\n")


def build_fixture(home):
    """가짜 HOME에 17개 케이스를 세운다. (installed, settings, market, cache)"""
    cache = home / ".claude/plugins/cache" / MARKET
    market = home / ".claude/plugins/marketplaces" / MARKET
    mplug = market / "plugins"
    installed, enabled, gitlinks = {}, {}, {}

    def register(name, version, *, sha=FAKE_SHA_A, enable=True, install=True,
                 install_path=None):
        if install:
            installed[f"{name}@{MARKET}"] = [{
                "scope": "user",
                "installPath": str(install_path or cache / name / version),
                "version": version,
                "installedAt": "2026-01-01T00:00:00.000Z",
                "lastUpdated": "2026-01-01T00:00:00.000Z",
                "gitCommitSha": sha,
            }]
        if enable is not None:
            enabled[f"{name}@{MARKET}"] = enable
        gitlinks[name] = FAKE_SHA_A

    # ── clean: 전 축 일치 ──
    for n in ("clean",):
        make_plugin_tree(mplug / n, n, "1.0.0", hooks="/hooks/scripts/go.sh")
        (mplug / n / "hooks/scripts").mkdir(parents=True, exist_ok=True)
        (mplug / n / "hooks/scripts/go.sh").write_text("#!/bin/bash\necho hi\n")
        shutil.copytree(mplug / n, cache / n / "1.0.0")
        register(n, "1.0.0")

    # ── no-enable: enabledPlugins에 키 자체가 없음 ──
    make_plugin_tree(mplug / "no-enable", "no-enable", "1.0.0")
    shutil.copytree(mplug / "no-enable", cache / "no-enable/1.0.0")
    register("no-enable", "1.0.0", enable=None)

    # ── stale-cache: 구버전 디렉토리 잔존 ──
    make_plugin_tree(mplug / "stale-cache", "stale-cache", "2.0.0")
    shutil.copytree(mplug / "stale-cache", cache / "stale-cache/2.0.0")
    make_plugin_tree(cache / "stale-cache/1.0.0", "stale-cache", "1.0.0")
    register("stale-cache", "2.0.0")

    # ── no-cache: 캐시 디렉토리 자체가 없음 ──
    make_plugin_tree(mplug / "no-cache", "no-cache", "1.0.0")
    register("no-cache", "1.0.0")

    # ── dotfile-trap: 캐시에 .claude-plugin 누락 (cp -R src/* 함정) ──
    make_plugin_tree(mplug / "dotfile-trap", "dotfile-trap", "1.0.0")
    make_plugin_tree(cache / "dotfile-trap/1.0.0", "dotfile-trap", "1.0.0",
                     dotfile=False)
    register("dotfile-trap", "1.0.0")

    # ── ver-mismatch: 캐시 plugin.json 버전 ≠ installed 버전 ──
    make_plugin_tree(mplug / "ver-mismatch", "ver-mismatch", "1.0.0")
    make_plugin_tree(cache / "ver-mismatch/1.0.0", "ver-mismatch", "0.5.0")
    register("ver-mismatch", "1.0.0")

    # ── market-drift: 마켓 클론 버전이 설치본보다 앞섬 (Step 4/5 누락) ──
    make_plugin_tree(mplug / "market-drift", "market-drift", "2.0.0")
    make_plugin_tree(cache / "market-drift/1.0.0", "market-drift", "1.0.0")
    register("market-drift", "1.0.0")

    # ── content-drift: 같은 버전인데 마켓에 내용이 더 있음 + SHA 불일치 ──
    make_plugin_tree(mplug / "content-drift", "content-drift", "1.0.0",
                     extra_file="new-fix.md")
    make_plugin_tree(cache / "content-drift/1.0.0", "content-drift", "1.0.0")
    register("content-drift", "1.0.0", sha=FAKE_SHA_B)

    # ── sha-only: SHA만 낡음, 내용은 동일 ──
    make_plugin_tree(mplug / "sha-only", "sha-only", "1.0.0")
    shutil.copytree(mplug / "sha-only", cache / "sha-only/1.0.0")
    register("sha-only", "1.0.0", sha=FAKE_SHA_B)

    # ── hook-missing: hooks.json이 없는 스크립트를 참조 ──
    make_plugin_tree(mplug / "hook-missing", "hook-missing", "1.0.0",
                     hooks="/hooks/scripts/gone.sh")
    shutil.copytree(mplug / "hook-missing", cache / "hook-missing/1.0.0")
    register("hook-missing", "1.0.0")

    # ── hook-empty: 스크립트가 0바이트 (broken) ──
    make_plugin_tree(mplug / "hook-empty", "hook-empty", "1.0.0",
                     hooks="/hooks/scripts/empty.sh")
    (mplug / "hook-empty/hooks/scripts").mkdir(parents=True, exist_ok=True)
    (mplug / "hook-empty/hooks/scripts/empty.sh").write_text("")
    shutil.copytree(mplug / "hook-empty", cache / "hook-empty/1.0.0")
    register("hook-empty", "1.0.0")

    # ── not-installed: 캐시에 있는데 installed_plugins.json에 없음 ──
    make_plugin_tree(mplug / "not-installed", "not-installed", "1.0.0")
    shutil.copytree(mplug / "not-installed", cache / "not-installed/1.0.0")
    register("not-installed", "1.0.0", install=False)

    # ── path-missing: 캐시엔 1.0.0이 있는데 installPath가 다른 곳을 가리킴 ──
    make_plugin_tree(mplug / "path-missing", "path-missing", "1.0.0")
    shutil.copytree(mplug / "path-missing", cache / "path-missing/1.0.0")
    register("path-missing", "1.0.0",
             install_path=cache / "path-missing/1.0.0-ghost")

    # ── dev-drift: 격리된 개발 리포(GPTAKU_DEV_ROOT)가 2.0.0, 배포본 1.0.0 ──
    make_plugin_tree(mplug / "dev-drift", "dev-drift", "1.0.0")
    shutil.copytree(mplug / "dev-drift", cache / "dev-drift/1.0.0")
    make_plugin_tree(home / "dev-plugins/dev-drift", "dev-drift", "2.0.0")
    register("dev-drift", "1.0.0")

    # ── hook-unbraced: $CLAUDE_PLUGIN_ROOT/… (중괄호 없음)로 없는 스크립트 참조 ──
    make_plugin_tree(mplug / "hook-unbraced", "hook-unbraced", "1.0.0",
                     hooks="/hooks/scripts/gone.sh", braced=False)
    shutil.copytree(mplug / "hook-unbraced", cache / "hook-unbraced/1.0.0")
    register("hook-unbraced", "1.0.0")

    # ── content-noise: SHA 불일치 + 캐시에 파이썬 캐시/.DS_Store만 추가 → warn ──
    make_plugin_tree(mplug / "content-noise", "content-noise", "1.0.0")
    shutil.copytree(mplug / "content-noise", cache / "content-noise/1.0.0")
    (cache / "content-noise/1.0.0/__pycache__").mkdir()
    (cache / "content-noise/1.0.0/__pycache__/x.cpython-312.pyc").write_bytes(b"\x00")
    (cache / "content-noise/1.0.0/.DS_Store").write_bytes(b"\x00")
    register("content-noise", "1.0.0", sha=FAKE_SHA_B)

    # ── release-missing: 가짜 gh가 test/release-missing 리포만 릴리즈 없음 처리 ──
    make_plugin_tree(mplug / "release-missing", "release-missing", "1.0.0")
    shutil.copytree(mplug / "release-missing", cache / "release-missing/1.0.0")
    register("release-missing", "1.0.0")

    # 가짜 gh — 네트워크 없이 릴리즈 축을 돌린다 (PATH 선두에 놓임)
    fake_bin = home / "bin"; fake_bin.mkdir()
    gh = fake_bin / "gh"
    gh.write_text("#!/bin/sh\ncase \"$*\" in *test/release-missing*) exit 1;; esac\n"
                  "echo '{\"tagName\":\"v1.0.0\"}'\n")
    gh.chmod(0o755)

    write_json(home / ".claude/plugins/installed_plugins.json",
               {"version": 1, "plugins": installed})
    write_json(home / ".claude/settings.json", {"enabledPlugins": enabled})

    # .gitmodules — 릴리즈 축이 리포 주소를 찾는 경로 (네트워크는 안 씀)
    (market / ".gitmodules").write_text("".join(
        f'[submodule "plugins/{n}"]\n\tpath = plugins/{n}\n'
        f"\turl = https://github.com/test/{n}.git\n" for n in gitlinks))

    # 마켓 클론을 git 리포로 만들고 서브모듈 gitlink를 심는다 (SHA 축 입력)
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    run = lambda *a: subprocess.run(["git", "-C", str(market), *a],
                                    capture_output=True, text=True, env=env,
                                    check=True)
    run("init", "-q")
    for n, sha in gitlinks.items():
        run("update-index", "--add", "--cacheinfo", f"160000,{sha},plugins/{n}")
    run("commit", "-q", "-m", "fixture")


def main():
    tmp = Path(tempfile.mkdtemp(prefix="doctor-verify-"))
    try:
        home = tmp / "home"
        build_fixture(home)
        r = subprocess.run(
            [sys.executable, str(DOCTOR), "--json", "--network"],
            capture_output=True, text=True,
            env={**os.environ, "HOME": str(home),
                 "GPTAKU_DEV_ROOT": str(home / "dev-plugins"),
                 "PATH": f"{home / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"})
        if not r.stdout.strip():
            sys.exit(f"doctor가 출력 없이 종료 (rc={r.returncode})\n{r.stderr}")
        report = json.loads(r.stdout)

        failures, checked = [], 0
        for name, axis, status in EXPECTATIONS:
            checks = report.get(name)
            if checks is None:
                failures.append(f"{name}: 리포트에 플러그인이 없음")
                continue
            got = {c["axis"]: c["status"] for c in checks}
            if axis is None:
                bad = {a: s for a, s in got.items() if s != "ok"}
                if bad:
                    failures.append(f"{name}: 전 축 ok여야 하는데 {bad} (오탐)")
                else:
                    checked += 1
                continue
            if got.get(axis) != status:
                failures.append(
                    f"{name}: {axis} 축이 {status}여야 하는데 "
                    f"{got.get(axis, '축 없음')} — 전체 {got}")
            else:
                checked += 1
                fix = next((c["fix"] for c in checks if c["axis"] == axis), None)
                if not fix:
                    failures.append(f"{name}: {axis} {status}인데 처방 문자열 없음")

        # fail이 있으면 exit 1 (CI 게이트로 쓸 수 있어야 한다)
        if r.returncode != 1:
            failures.append(f"fail 케이스가 있는데 종료코드가 {r.returncode} (1이어야 함)")

        for f in failures:
            print(f"  \033[31m✗\033[0m {f}")
        print(f"\n{len(EXPECTATIONS) - len(failures)}/{len(EXPECTATIONS)} 케이스 통과"
              f" (축 대조 {checked}건)")
        if failures:
            sys.exit(1)
        print("\033[32m전 케이스 통과 — 각 축이 주입된 고장을 정확한 status로 잡음\033[0m")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
