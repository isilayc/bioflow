from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.context_intake import (
    AMPLICON_ASV_TABLE,
    AMPLICON_FEATURE_TABLE,
    AMPLICON_OTU_TABLE,
    AMPLICON_TAXONOMY_TABLE,
    get_data_state_options,
    get_goal_availability,
)
from engine.recommender import (
    build_workflow,
    get_goal_options,
    get_workflow_strategies,
)
from engine.dependencies import validate_workflow

EXPECTED = {
    "16S rRNA analysis",
    "18S rRNA analysis",
    "ITS analysis",
    "ASV inference",
    "Taxonomic assignment",
    "Alpha diversity",
    "Beta diversity",
    "Differential abundance",
}


def fail(message):
    print("FAIL:", message)
    raise SystemExit(1)


def main():
    states = {item["id"] for item in get_data_state_options("Amplicon")}
    required = {
        AMPLICON_ASV_TABLE,
        AMPLICON_OTU_TABLE,
        AMPLICON_FEATURE_TABLE,
        AMPLICON_TAXONOMY_TABLE,
    }

    if required - states:
        fail("Missing amplicon data states.")

    for state in required:
        goals = get_goal_options(
            "Amplicon",
            "Existing data",
            "Not applicable",
            data_state=state,
            reference_context={"status": "not_applicable", "usable_reference": False},
        )
        if EXPECTED - set(goals):
            fail(f"Missing goals for {state}: {sorted(EXPECTED - set(goals))}")

    for state in (
        AMPLICON_ASV_TABLE,
        AMPLICON_OTU_TABLE,
        AMPLICON_FEATURE_TABLE,
    ):
        for goal in ("Alpha diversity", "Beta diversity", "Differential abundance"):
            if not get_goal_availability("Amplicon", state, goal).get("selectable"):
                fail(f"Expected direct route: {state}/{goal}")

        strategies = get_workflow_strategies(
            "Amplicon",
            "Existing data",
            "Not applicable",
            "Alpha diversity",
            data_state=state,
            reference_context={"status": "not_applicable", "usable_reference": False},
        )

        if not strategies:
            fail(f"No alpha-diversity strategy for {state}")

        workflow = build_workflow(
            "Amplicon",
            "Existing data",
            "Not applicable",
            "Alpha diversity",
            workflow_id=strategies[0]["id"],
            data_state=state,
            reference_context={"status": "not_applicable", "usable_reference": False},
        )

        report = validate_workflow(workflow["id"], workflow_override=workflow)

        if not report.get("valid"):
            fail(f"Dependency-invalid route for {state}")

    if get_goal_availability(
        "Amplicon",
        AMPLICON_ASV_TABLE,
        "ASV inference",
    ).get("status") != "already_satisfied":
        fail("ASV inference should be already_satisfied for ASV-table input.")

    if get_goal_availability(
        "Amplicon",
        AMPLICON_TAXONOMY_TABLE,
        "Taxonomic assignment",
    ).get("status") != "already_satisfied":
        fail("Taxonomic assignment should be already_satisfied for taxonomy-table input.")

    print("=" * 72)
    print("OmicsRoute Amplicon Context v2.3")
    print("=" * 72)
    print("Amplicon data states: PASS")
    print("All 8 amplicon goals visible: PASS")
    print("ASV/OTU/feature-table downstream routes: PASS")
    print("")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
