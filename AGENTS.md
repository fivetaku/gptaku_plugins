# gptaku-plugins 마켓플레이스

## OmO host mapping

- In OmO, `/Users/chulrolee/gptaku_plugins/CLAUDE.md` is the canonical project policy; the Codex-specific instructions below remain for Codex and are not an OmO installation procedure. Follow the canonical release/tag, enabledPlugins, doctor verification and project-local `.pumasi/pumasi.config.yaml` rules. Its later cache-copy rule takes precedence over the earlier wildcard example: preserve dotfiles with `cp -R "$SRC/." "$DST/"`.
- Use native `read`, `bash`, `write`, `edit` and `apply_patch` tools. When delegation is needed, use the available native task tool and await its terminal result; a role description or spawn receipt is not completed work. This root declares no constrained roles.
- Use the discovered `.agents/skills/coupang-search/SKILL.md` and `.agents/skills/powerup-kr/SKILL.md` adapters. Read original `.claude/commands/<name>.md` resources explicitly when requested, preserving their arguments; reading a command does not register a slash command or authorize its side effects.
- Claude plugin installation, cache paths, UI shortcuts and MCP references are not native OmO capabilities. Do not translate `~/.claude` or `~/.Codex` paths into invented `~/.omo` equivalents. Use only tools actually available; ask questions in conversation if no native question tool is exposed.
- `.omo/settings.json` imports the shared adapter; `.omo/workspace-runtime.json` loads the canonical instructions and binds native `bash` calls to the exact active `.claude/settings.json` commit validator. This is a read-only validation gate, not permission to commit.
- Sync, commits, pushes, releases, cache replacement, installation and restarts require the user's applicable authorization. Workspace setup does not run them, inspect private progress or migrate state.

## 프로젝트 구조

```
gptaku_plugins/           # 마켓플레이스 (parent repo)
  plugins/                # 모든 플러그인은 git submodule
    dd/
    docs-guide/
    git-teacher/
    goaljaby/
    insane-design/
    insane-research/
    insane-review/
    insane-search/
    insane-slide/         # 미출시 (marketplace.json 미등록, v0.1.0)
    kkirikkiri/
    nopal/
    pumasi/
    show-me-the-prd/
    skillers-suda/
    vibe-sunsang/
```

## 플러그인 버전 업데이트 체크리스트

플러그인 코드를 수정하고 버전을 올릴 때 반드시 아래 순서를 따른다.
**하나라도 빠지면 캐시 불일치로 구버전이 로드된다.**

### Step 1: 서브모듈 내에서 작업

```bash
cd plugins/<plugin-name>
# 코드 수정 완료 후
# 1) plugin.json 버전 업데이트
# 2) git add + commit + push
```

### Step 2: 부모 저장소에서 서브모듈 포인터 업데이트

```bash
cd /Users/chulrolee/gptaku_plugins
git add plugins/<plugin-name>
git commit -m "chore: update <plugin-name> submodule to v<new-version>"
git push
```

### Step 3: 마켓플레이스 클론 동기화

```bash
cd ~/.Codex/plugins/marketplaces/gptaku-plugins
git pull
git submodule update --init plugins/<plugin-name>
```

### Step 4: 캐시 교체

```bash
# 1) 이전 버전 캐시 삭제
trash ~/.Codex/plugins/cache/gptaku-plugins/<plugin-name>/<old-version>

# 2) 새 버전 캐시 생성 (마켓플레이스에서 복사)
cp -R ~/.Codex/plugins/marketplaces/gptaku-plugins/plugins/<plugin-name> \
      /tmp/<plugin-name>-staging
mkdir -p ~/.Codex/plugins/cache/gptaku-plugins/<plugin-name>/<new-version>
cp -R /tmp/<plugin-name>-staging/* \
      ~/.Codex/plugins/cache/gptaku-plugins/<plugin-name>/<new-version>/
trash /tmp/<plugin-name>-staging
```

### Step 5: installed_plugins.json 업데이트

```python
# ~/.Codex/plugins/installed_plugins.json 에서 해당 플러그인 항목 수정:
# - installPath: 새 버전 경로로 변경
# - version: 새 버전으로 변경
# - gitCommitSha: 서브모듈 최신 커밋 SHA로 변경
# - lastUpdated: 현재 시간으로 변경
```

### Step 6: 검증

```bash
# 캐시에 새 버전만 존재하는지 확인
ls ~/.Codex/plugins/cache/gptaku-plugins/<plugin-name>/
# → <new-version> 만 표시되어야 함

# installed_plugins.json에서 버전 확인
cat ~/.Codex/plugins/installed_plugins.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(json.dumps(data['plugins']['<plugin-name>@gptaku-plugins'], indent=2))
"
```

### Step 7: Codex 재시작

캐시를 교체해도 **현재 세션**은 이미 로드된 구 버전을 사용한다.
반드시 Codex를 재시작해야 새 버전이 반영된다.

## 핵심 원칙

- **버전을 올릴 때는 반드시 동작 확인 후** 올린다. 미확인 상태에서 버전만 반복 업데이트하지 않는다.
- **캐시는 단일 버전만 유지**한다. 구 버전 디렉토리는 즉시 삭제한다.
- **installed_plugins.json의 installPath, version, gitCommitSha**가 모두 일치해야 한다.
- **커맨드 파일이 실행 지시서**다. Read로 읽은 스킬 파일은 참고 자료일 뿐 도구 호출을 트리거하지 않는다.

## 플러그인별 주요 파일

### show-me-the-prd

| 파일 | 역할 |
|------|------|
| `commands/show-me-the-prd.md` | **실행 지시서** — AskUserQuestion 인라인 호출 포함 |
| `skills/show-me-the-prd/SKILL.md` | 참고 문서 (Read로 읽히면 참고 자료 취급) |
| `.Codex-plugin/plugin.json` | 버전 정보 |
| `references/` | 인터뷰 가이드, 문서 템플릿, 리서치 전략 |
