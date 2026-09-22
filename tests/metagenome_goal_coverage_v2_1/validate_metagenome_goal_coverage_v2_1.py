from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.context_intake import (
    METAGENOME_CONTIGS,
    get_goal_availability,
)
from engine.recommender import (
    get_goal_options,
    get_workflow_strategies,
)


EXPECTED = {
    "Taxonomic profiling",
    "MAG reconstruction",
    "Functional profiling",
    "Pathway analysis",
    "Antibiotic resistance profiling",
    "Virulence profiling",
    "Viral analysis",
    "Plasmid analysis",
    "Strain-level phylogenomics",
    "Microdiversity profiling",
}


def fail(message):
    print("FAIL:", message)
    raise SystemExit(1)


def main():
    goals = get_goal_options(
        "Metagenome",
        "Existing data",
        "Not applicable",
        data_state=METAGENOME_CONTIGS,
        reference_context={
            "status": "not_applicable",
            "usable_reference": False,
        },
    )

    missing = EXPECTED - set(goals)

    if missing:
        fail(
            "Missing metagenome goals from contig intake: "
            + ", ".join(sorted(missing))
        )

    if len(set(goals) & EXPECTED) != 10:
        fail("Metagenome contig intake should expose all 10 catalogue goals.")

    for goal in (
        "Virulence profiling",
        "Viral analysis",
        "Plasmid analysis",
    ):
        status = get_goal_availability(
            "Metagenome",
            METAGENOME_CONTIGS,
            goal,
        )

        if not status.get("selectable"):
            fail(f"Direct contig goal is not selectable: {goal}")

        strategies = get_workflow_strategies(
            "Metagenome",
            "Existing data",
            "Not applicable",
            goal,
            data_state=METAGENOME_CONTIGS,
            reference_context={
                "status": "not_applicable",
                "usable_reference": False,
            },
        )

        if not strategies:
            fail(f"No direct contig strategy for: {goal}")

    mag = get_goal_availability(
        "Metagenome",
        METAGENOME_CONTIGS,
        "MAG reconstruction",
    )

    if mag.get("selectable"):
        fail(
            "MAG reconstruction should request original reads/coverage "
            "when starting only from contigs."
        )

    for goal in (
        "Taxonomic profiling",
        "Functional profiling",
        "Pathway analysis",
        "Antibiotic resistance profiling",
        "Strain-level phylogenomics",
        "Microdiversity profiling",
    ):
        status = get_goal_availability(
            "Metagenome",
            METAGENOME_CONTIGS,
            goal,
        )

        if status.get("status") != "needs_input":
            fail(f"Expected needs_input for: {goal}")

    print("=" * 72)
    print("OmicsRoute Metagenome Goal Coverage v2.1")
    print("=" * 72)
    print("All 10 metagenome goals visible: PASS")
    print("Direct contig routes remain selectable: PASS")
    print("Read-dependent routes are explained, not silently hidden: PASS")
    print("MAG coverage requirement is explicit: PASS")
    print("")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
