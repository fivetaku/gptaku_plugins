#!/usr/bin/env python3
"""gptaku-core 라우터 회귀 테스트 — 마켓의 모든 routing.json을 모아 고정 사례와 대조한다.

cases_heldout.json은 키워드 작성 전에 고정한 검증 세트, cases_tuning.json은 튜닝 중
쓴 사례와 실제 대화에서 나온 오탐 사례다. 둘 다 전부 맞아야 통과한다.
"""
import glob, json, os, sys, unittest

sys.dont_write_bytecode = True  # 플러그인 폴더에 __pycache__를 남기지 않는다

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "plugins", "gptaku-core")
ALIAS = {"research": "insane-research:insane-research-main", "search": "insane-search:insane-search"}


class RoutesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dirs = [os.path.dirname(p) for p in glob.glob(os.path.join(ROOT, "plugins", "*", "routing.json"))]
        os.environ["GPTAKU_CORE_PLUGIN_DIRS"] = os.pathsep.join(dirs)
        os.environ["CLAUDE_CONFIG_DIR"] = "/nonexistent"  # 설치본이 아니라 레포 routing.json만 본다
        sys.path.insert(0, os.path.join(CORE, "hooks"))
        import routes
        cls.routes = routes
        cls.table = routes.load_routes()

    def _check(self, name):
        with open(os.path.join(CORE, "tests", name), encoding="utf-8") as f:
            cases = json.load(f)
        bad = []
        for cid, c in cases.items():
            m = self.routes.match(c["text"], self.table)
            got = m["skill"] if m else None
            want = None if c["expect"] == "none" else ALIAS.get(c["expect"], c["expect"])
            if got != want:
                bad.append(f"{cid}: want={want} got={got} | {c['text'][:50]}")
        self.assertEqual(bad, [], "\n".join(bad))

    def test_heldout(self): self._check("cases_heldout.json")
    def test_tuning(self): self._check("cases_tuning.json")

    def test_every_route_skill_exists(self):
        missing = []
        for r in self.table:
            plugin, _, name = r["skill"].partition(":")
            base = os.path.join(ROOT, "plugins", plugin)
            if not (os.path.exists(os.path.join(base, "skills", name, "SKILL.md"))
                    or os.path.exists(os.path.join(base, "commands", name + ".md"))):
                missing.append(r["skill"])
        self.assertEqual(missing, [])

    def test_off_switch(self):
        import subprocess
        env = dict(os.environ, GPTAKU_ROUTER="off")
        out = subprocess.run([sys.executable, "-B", os.path.join(CORE, "hooks", "router.py")], input='{"prompt":"레딧에서 글 찾아줘"}',
                             capture_output=True, text=True, env=env).stdout
        self.assertEqual(out.strip(), "")


if __name__ == "__main__":
    unittest.main(verbosity=1)
