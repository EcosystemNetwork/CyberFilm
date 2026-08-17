import unittest

from pydantic import ValidationError

from cyberfilm.agent import ProductionPlanOutput


class ProductionPlanOutputTests(unittest.TestCase):
    def test_accepts_bounded_plan(self) -> None:
        plan = ProductionPlanOutput.model_validate(
            {
                "treatment": "A tense control-room story grounded in observable production events.",
                "shots": [
                    {
                        "shot_id": "shot-01",
                        "description": "A wide shot reveals the production control room at dawn.",
                        "duration_seconds": 8,
                        "production_objective": "Establish the operating environment.",
                        "risk_notes": [],
                    }
                ],
                "estimated_cost_usd": 75,
                "assumptions": ["The location is available."],
            }
        )

        self.assertEqual("shot-01", plan.shots[0].shot_id)

    def test_rejects_unbounded_duration_and_cost(self) -> None:
        with self.assertRaises(ValidationError):
            ProductionPlanOutput.model_validate(
                {
                    "treatment": (
                        "A treatment long enough to satisfy the minimum schema requirement."
                    ),
                    "shots": [
                        {
                            "shot_id": "shot-01",
                            "description": (
                                "A deliberately invalid shot exceeds the duration boundary."
                            ),
                            "duration_seconds": 90,
                            "production_objective": "Exercise schema limits.",
                        }
                    ],
                    "estimated_cost_usd": 1_000_000,
                }
            )


if __name__ == "__main__":
    unittest.main()
