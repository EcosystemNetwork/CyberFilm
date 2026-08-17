from dataclasses import dataclass
from typing import Any

from cyberfilm.domain import ProductionPlan, Shot


@dataclass(frozen=True, slots=True)
class ManipulationResult:
    plan: ProductionPlan
    action: str
    explanation: str


class ManipulationEngine:
    async def manipulate(
        self,
        plan: ProductionPlan,
        action: str,
        params: dict[str, Any],
    ) -> ManipulationResult:
        shots = list(plan.shots)

        if action == "reorder":
            from_index = int(params.get("from_index", 0))
            to_index = int(params.get("to_index", 0))
            shot = shots.pop(from_index)
            shots.insert(to_index, shot)
            explanation = f"Reordered {shot.shot_id} from position {from_index} to {to_index}."

        elif action == "trim":
            shot_id = str(params.get("shot_id", ""))
            new_duration = int(params.get("new_duration", 1))
            for i, shot in enumerate(shots):
                if shot.shot_id == shot_id:
                    shots[i] = Shot(
                        shot_id=shot.shot_id,
                        description=shot.description,
                        duration_seconds=new_duration,
                        production_objective=shot.production_objective,
                        risk_notes=shot.risk_notes,
                    )
                    explanation = f"Trimmed {shot_id} to {new_duration} seconds."
                    break
            else:
                raise ValueError(f"Shot {shot_id} not found")

        elif action == "remove":
            shot_id = str(params.get("shot_id", ""))
            shots = [s for s in shots if s.shot_id != shot_id]
            explanation = f"Removed shot {shot_id}."

        elif action == "add":
            next_id = max((int(s.shot_id.split("-")[-1]) for s in shots), default=0) + 1
            new_shot = Shot(
                shot_id=f"shot-{next_id:02d}",
                description=str(params.get("description", "")),
                duration_seconds=int(params.get("duration_seconds", 5)),
                production_objective=str(params.get("production_objective", "")),
                risk_notes=tuple(params.get("risk_notes", [])),
            )
            after = params.get("after_shot_id")
            if after:
                index = next(
                    (i for i, s in enumerate(shots) if s.shot_id == after), len(shots)
                )
                shots.insert(index + 1, new_shot)
            else:
                shots.append(new_shot)
            explanation = f"Added shot {new_shot.shot_id}."

        elif action == "regenerate":
            shot_id = str(params.get("shot_id", ""))
            new_description = str(params.get("description", ""))
            for i, shot in enumerate(shots):
                if shot.shot_id == shot_id:
                    shots[i] = Shot(
                        shot_id=shot.shot_id,
                        description=new_description,
                        duration_seconds=shot.duration_seconds,
                        production_objective=shot.production_objective,
                        risk_notes=shot.risk_notes,
                    )
                    explanation = f"Regenerated description for {shot_id}."
                    break
            else:
                raise ValueError(f"Shot {shot_id} not found")

        else:
            raise ValueError(f"Unknown manipulation action: {action}")

        return ManipulationResult(
            plan=ProductionPlan(
                treatment=plan.treatment,
                shots=tuple(shots),
                estimated_cost_usd=plan.estimated_cost_usd,
            ),
            action=action,
            explanation=explanation,
        )
