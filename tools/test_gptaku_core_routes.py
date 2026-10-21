#!/usr/bin/env python3
"""gptaku-core 라우터 회귀 테스트 — 마켓의 모든 routing.json을 모아 고정 사례와 대조한다.

cases_heldout.json은 키워드 작성 전에 고정한 검증 세트, cases_tuning.json은 튜닝 중 쓴 사례와
실제 대화 오탐, cases_review.json은 외부 리뷰(2026-10-14)가 재현한 반례, cases_real.json은 실제 대화 오탐 유형을 익명화한 문장이다. 모두 전부 맞아야 통과한다.
"""
import glob, json, os, subprocess, sys, tempfile, unittest

sys.dont_write_bytecode = True  # 플러그인 폴더에 __pycache__를 남기지 않는다

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "plugins", "gptaku-core")
ALIAS = {"research": "insane-research:insane-research-main", "search": "insane-search:insane-search"}


def _env(**extra):
    dirs = [os.path.dirname(p) for p in glob.glob(os.path.join(ROOT, "plugins", "*", "routing.json"))]
    env = dict(os.environ, GPTAKU_CORE_PLUGIN_DIRS=os.pathsep.join(dirs), CLAUDE_CONFIG_DIR="/nonexistent",
               GPTAKU_USER_ROUTES="/nonexistent/routes.json")
    env.pop("GPTAKU_ROUTER", None)
    env.update(extra)
    return env


class RoutesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.update(_env())
        os.environ.pop("GPTAKU_ROUTER", None)
        sys.path.insert(0, os.path.join(CORE, "hooks"))
        import routes
        cls.routes = routes
        cls.table = routes.load_routes()

    def _check(self, name, table=None):
        with open(os.path.join(CORE, "tests", name), encoding="utf-8") as f:
            cases = json.load(f)
        bad = []
        for cid, c in cases.items():
            m = self.routes.match(c["text"], table or self.table)
            got = m["skill"] if m else None
            want = None if c["expect"] == "none" else ALIAS.get(c["expect"], c["expect"])
            if got != want:
                bad.append(f"{cid}: want={want} got={got} | {c['text'][:50]}")
        self.assertEqual(bad, [], "\n".join(bad))

    def test_heldout(self): self._check("cases_heldout.json")
    def test_tuning(self): self._check("cases_tuning.json")
    def test_review(self): self._check("cases_review.json")
    def test_real(self): self._check("cases_real.json")

    def test_route_order_does_not_change_result(self):
        for name in ("cases_heldout.json", "cases_tuning.json", "cases_review.json", "cases_real.json"):
            self._check(name, table=list(reversed(self.table)))

    def test_exact_tie_abstains(self):
        a = {"skill": "p:a", "when": "a", "priority": 1, "keywords": ["사과"]}
        b = {"skill": "p:b", "when": "b", "priority": 1, "keywords": ["배"]}
        self.assertIsNone(self.routes.match("사과 배 알려줘", [a, b]))

    def test_invalid_route_is_isolated(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "routing.json"), "w", encoding="utf-8") as f:
                json.dump({"routes": [{"skill": "bad:regex", "when": "x", "patterns": ["["]},
                                      {"skill": "bad:nowhen", "keywords": "문자열"},
                                      {"skill": "ok:route", "when": "y", "keywords": ["무지개"]}]}, f)
            old = os.environ["GPTAKU_CORE_PLUGIN_DIRS"]
            os.environ["GPTAKU_CORE_PLUGIN_DIRS"] = d
            try:
                table = self.routes.load_routes()
            finally:
                os.environ["GPTAKU_CORE_PLUGIN_DIRS"] = old
        self.assertEqual([r["skill"] for r in table], ["ok:route"])

    def test_unreadable_settings_loads_nothing_from_installs(self):
        with tempfile.TemporaryDirectory() as cfg:
            os.makedirs(os.path.join(cfg, "plugins"))
            with open(os.path.join(cfg, "settings.json"), "w") as f:
                f.write("{깨진 json")
            out = subprocess.run([sys.executable, "-B", "-c", "import routes;print(len(routes.plugin_dirs()))"],
                                 cwd=os.path.join(CORE, "hooks"), capture_output=True, text=True,
                                 env=_env(CLAUDE_CONFIG_DIR=cfg, GPTAKU_CORE_PLUGIN_DIRS=""))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), "0")

    def test_every_route_skill_exists(self):
        missing = []
        for r in self.table:
            plugin, _, name = r["skill"].partition(":")
            base = os.path.join(ROOT, "plugins", plugin)
            if not (os.path.exists(os.path.join(base, "skills", name, "SKILL.md"))
                    or os.path.exists(os.path.join(base, "commands", name + ".md"))):
                missing.append(r["skill"])
        self.assertEqual(missing, [])

    def _with_user_routes(self, routes):
        d = tempfile.mkdtemp()
        path = os.path.join(d, "routes.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"routes": routes}, f, ensure_ascii=False)
        old = self.routes.USER_ROUTES
        self.routes.USER_ROUTES = path
        try:
            return self.routes.load_routes()
        finally:
            self.routes.USER_ROUTES = old

    def test_user_routes_accept_personal_skill_names(self):
        table = self._with_user_routes([
            {"skill": "my-writer", "when": "윤문", "priority": 20, "keywords": ["윤문"]},
            {"skill": "other-market:deck", "when": "덱", "priority": 20, "keywords": ["발표 덱"]},
            {"skill": "bad name", "when": "x", "keywords": ["x"]},
        ])
        names = [r["skill"] for r in table]
        self.assertIn("my-writer", names)
        self.assertIn("other-market:deck", names)
        self.assertNotIn("bad name", names)
        self.assertEqual(self.routes.match("이 초안 윤문해줘", table)["skill"], "my-writer")
        self.assertEqual(self.routes.match("이거 /my-writer로 해줘", table)["skill"], "my-writer")

    def test_user_route_cannot_shadow_plugin_route(self):
        table = self._with_user_routes([{"skill": "nopal:nopal", "when": "가로채기", "priority": 99,
                                         "keywords": ["가로채기"]}])
        nopal = [r for r in table if r["skill"] == "nopal:nopal"]
        self.assertEqual(len(nopal), 1)
        self.assertNotEqual(nopal[0]["when"], "가로채기")

    def test_bad_user_file_does_not_stop_or_hijack(self):
        # 손편집 실수: routes가 null이어도 플러그인 라우트는 그대로 읽힌다
        self.assertEqual(len(self._with_user_routes(None)), len(self.table))
        # 빈 키워드·빈 문자열에 맞는 패턴은 모든 절에 걸려 다른 스킬을 가로채므로 라우트째 버린다
        table = self._with_user_routes([
            {"skill": "grab-all", "when": "x", "priority": 99, "keywords": [""]},
            {"skill": "grab-pat", "when": "x", "priority": 99, "patterns": ["(레딧)?"]},
        ])
        self.assertEqual([r["skill"] for r in table if r["skill"].startswith("grab-")], [])
        self.assertEqual(self.routes.match("레딧에서 글 찾아줘", table)["skill"], "insane-search:insane-search")

    def test_plugin_routes_still_require_plugin_skill_names(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "routing.json"), "w", encoding="utf-8") as f:
                json.dump({"routes": [{"skill": "bare", "when": "x", "keywords": ["무지개"]}]}, f)
            old = os.environ["GPTAKU_CORE_PLUGIN_DIRS"]
            os.environ["GPTAKU_CORE_PLUGIN_DIRS"] = d
            try:
                table = self.routes.load_routes()
            finally:
                os.environ["GPTAKU_CORE_PLUGIN_DIRS"] = old
        self.assertEqual(table, [])

    def test_request_shapes(self):
        r = {"skill": "p:w", "when": "w", "priority": 1, "keywords": ["윤문", "2.5로 그려", "슬라이드", "출첵"]}
        cases = {
            "이 문장 윤문해줘: '본 보고서는 다양한 측면에서 분석했습니다.'": "p:w",
            "2.5로 그려줘": "p:w",
            "슬라이드 만들어줘 IR용으로": "p:w",
            "출첵": "p:w",
            "슬라이드 만들어줘 했는데 안 되네": None,
            "슬라이드 만들어줘 라고 했잖아": None,
            "슬라이드 만들어줘 그랬잖아": None,
            "슬라이드 만들어줘 해도 안 됨": None,
            "슬라이드 만들어줘 이거 왜 안돼": None,
            "슬라이드 만들어줘 라고 했을 때": None,
            "슬라이드 만들어줘 최근 한 달": "p:w",
            "그 윤문은 어제 끝났어": None,
            "It's fine, 윤문 don't worry": None,
            "1. 윤문해줘": None,
            "1.윤문해줘": None,
            "출첵!": "p:w",
            "출첵. 이 파일 이름 바꿔줘": None,
            "수정할 곳:\n출첵\n이 컴포넌트 코드 위치 찾아줘": None,
        }
        got = {text: (m["skill"] if (m := self.routes.match(text, [r])) else None) for text in cases}
        self.assertEqual(got, cases)

    def test_setup_script_scan_write_check(self):
        script = os.path.join(CORE, "hooks", "user_routes.py")
        with tempfile.TemporaryDirectory() as cfg:
            skill = os.path.join(cfg, "skills", "my-writer")
            os.makedirs(skill)
            with open(os.path.join(skill, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write('---\nname: my-writer\ndescription: >-\n  한글 윤문. 트리거 — "이 초안 윤문해줘", "AI 티 없애줘".\n---\n')
            env = _env(CLAUDE_CONFIG_DIR=cfg, GPTAKU_USER_ROUTES=os.path.join(cfg, "gptaku-core", "routes.json"))
            run = lambda *a: subprocess.run([sys.executable, "-B", script, *a], capture_output=True, text=True, env=env)
            scan = json.loads(run("scan").stdout)
            row = next(s for s in scan["skills"] if s["skill"] == "my-writer")
            self.assertEqual((row["routed"], row["draft_keywords"]), (False, ["이 초안 윤문", "ai 티 없애"]))
            draft = os.path.join(cfg, "draft.json")
            with open(draft, "w", encoding="utf-8") as f:
                json.dump({"routes": [{"skill": "my-writer", "when": "윤문", "priority": 20, "keywords": ["윤문"]}]}, f)
            self.assertEqual(run("write", draft).returncode, 0)
            self.assertTrue(next(s for s in json.loads(run("scan").stdout)["skills"] if s["skill"] == "my-writer")["routed"])
            self.assertEqual(run("check", "이 초안 윤문해줘", "오늘 날씨 어때").stdout.splitlines(),
                             ["my-writer\t이 초안 윤문해줘", "-\t오늘 날씨 어때"])
            out = subprocess.run([sys.executable, "-B", os.path.join(CORE, "hooks", "router.py")],
                                 input='{"prompt":"이 초안 윤문해줘"}', capture_output=True, text=True, env=env)
            self.assertIn("`my-writer`", out.stdout)
            # 깨진 사용자 파일은 빈 목록으로 덮어쓰지 않는다(기존 라우트 보존)
            with open(env["GPTAKU_USER_ROUTES"], "w", encoding="utf-8") as f:
                f.write('{"routes": [{"skill": "keep-me",')
            for args in (("write", draft), ("remove", "keep-me"), ("list",)):
                self.assertEqual(run(*args).returncode, 1, args)
            with open(env["GPTAKU_USER_ROUTES"], encoding="utf-8") as f:
                self.assertEqual(f.read(), '{"routes": [{"skill": "keep-me",')

    def test_off_switch_both_hooks(self):
        for hook, stdin in (("router.py", '{"prompt":"레딧에서 글 찾아줘"}'), ("session_rule.py", "{}")):
            out = subprocess.run([sys.executable, "-B", os.path.join(CORE, "hooks", hook)], input=stdin,
                                 capture_output=True, text=True, env=_env(GPTAKU_ROUTER="off"))
            self.assertEqual((out.returncode, out.stdout.strip(), out.stderr.strip()), (0, "", ""), hook)

    def test_hooks_emit_valid_json_when_on(self):
        for hook, stdin, key in (("router.py", '{"prompt":"레딧에서 글 찾아줘"}', "UserPromptSubmit"),
                                 ("session_rule.py", "{}", "SessionStart")):
            out = subprocess.run([sys.executable, "-B", os.path.join(CORE, "hooks", hook)], input=stdin,
                                 capture_output=True, text=True, env=_env())
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(json.loads(out.stdout)["hookSpecificOutput"]["hookEventName"], key)


if __name__ == "__main__":
    unittest.main(verbosity=1)
