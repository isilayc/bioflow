from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.main import PlanningContext, StrategyRequest, health, sample_types, data_states, goals, strategies


def fail(message):
    print("FAIL:", message)
    raise SystemExit(1)


def main():
    if health().get("status") != "ok":
        fail("Health failed.")

    samples = sample_types().get("sample_types", [])
    if not samples:
        fail("No sample types.")

    chosen = "Metagenome" if "Metagenome" in samples else samples[0]
    if not data_states(chosen).get("data_states"):
        fail("No data states.")

    ctx = PlanningContext(
        sample_type=chosen,
        data_state="raw_reads",
        sequencing="Illumina",
        read_type="Paired-end",
    )

    goal_rows = goals(ctx).get("goals", [])
    if not goal_rows:
        fail("No goals.")

    goal = goal_rows[0]["id"]

    rows = strategies(
        StrategyRequest(
            sample_type=chosen,
            data_state="raw_reads",
            sequencing="Illumina",
            read_type="Paired-end",
            goal=goal,
        )
    ).get("strategies", [])

    if not rows:
        fail("No strategies.")

    print("RESULT: PASS")


if __name__ == "__main__":
    main()
