import unittest

from cyberfilm.domain import ProductionPlan, Shot
from cyberfilm.manipulation import ManipulationEngine, ManipulationResult


class ManipulationEngineTests(unittest.IsolatedAsyncioTestCase):
    def _plan(self):
        return ProductionPlan(
            "Treatment",
            (
                Shot("shot-01", "Wide", 5, "Establish", ()),
                Shot("shot-02", "Close-up", 3, "Emotion", ()),
                Shot("shot-03", "Drone", 4, "Scale", ()),
            ),
            100,
        )

    async def test_reorder(self):
        engine = ManipulationEngine()
        result = await engine.manipulate(
            self._plan(), "reorder", {"from_index": 0, "to_index": 2}
        )

        self.assertIsInstance(result, ManipulationResult)
        self.assertEqual("reorder", result.action)
        self.assertEqual("shot-02", result.plan.shots[0].shot_id)
        self.assertEqual("shot-01", result.plan.shots[2].shot_id)

    async def test_trim(self):
        engine = ManipulationEngine()
        result = await engine.manipulate(
            self._plan(), "trim", {"shot_id": "shot-01", "new_duration": 2}
        )

        self.assertEqual(2, result.plan.shots[0].duration_seconds)
        self.assertIn("Trimmed", result.explanation)

    async def test_remove(self):
        engine = ManipulationEngine()
        result = await engine.manipulate(
            self._plan(), "remove", {"shot_id": "shot-02"}
        )

        self.assertEqual(2, len(result.plan.shots))
        self.assertNotIn("shot-02", [s.shot_id for s in result.plan.shots])

    async def test_add(self):
        engine = ManipulationEngine()
        result = await engine.manipulate(
            self._plan(),
            "add",
            {
                "after_shot_id": "shot-01",
                "description": "Reaction",
                "duration_seconds": 2,
                "production_objective": "Show reaction",
            },
        )

        self.assertEqual(4, len(result.plan.shots))
        self.assertEqual("shot-04", result.plan.shots[1].shot_id)

    async def test_regenerate(self):
        engine = ManipulationEngine()
        result = await engine.manipulate(
            self._plan(),
            "regenerate",
            {"shot_id": "shot-01", "description": "New wide description"},
        )

        self.assertEqual("New wide description", result.plan.shots[0].description)

    async def test_unknown_action_raises(self):
        engine = ManipulationEngine()
        with self.assertRaisesRegex(ValueError, "Unknown manipulation action"):
            await engine.manipulate(self._plan(), "warp", {})


if __name__ == "__main__":
    unittest.main()
