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
    env = dict(os.environ, GPTAKU_CORE_PLUGIN_DIRS=os.pathsep.join(dirs), CLAUDE_CONFIG_DIR="/nonexistent")
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
