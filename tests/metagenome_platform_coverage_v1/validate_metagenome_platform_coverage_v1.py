from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.dependencies import validate_workflow
from engine.recommender import (
    build_workflow,
    get_goal_options,
    get_read_type_options,
    get_sequencing_options,
    get_workflow_strategies,
)


def fail(message):
    print("FAIL:", message)
    raise SystemExit(1)


def validate_route(sequencing, read_type, goal):
    strategies = get_workflow_strategies(
        "Metagenome",
        sequencing,
        read_type,
        goal,
        data_state="raw_reads",
    )

    if not strategies:
        fail(f"No strategy for {sequencing} / {read_type} / {goal}")

    workflow = build_workflow(
        "Metagenome",
        sequencing,
        read_type,
        goal,
        workflow_id=strategies[0]["id"],
        data_state="raw_reads",
    )

    if not workflow:
        fail(f"Could not materialize {sequencing} / {goal}")

    report = validate_workflow(
        workflow["id"],
        workflow_override=workflow,
    )

    if not report.get("valid"):
        fail(
            f"Dependency validation failed for {sequencing} / {goal}: "
            f"{report}"
        )


def main():
    sequencing = get_sequencing_options("Metagenome")

    for expected in ("Illumina", "Oxford Nanopore", "PacBio"):
        if expected not in sequencing:
            fail(f"Missing sequencing option: {expected}")

    if "Single-end" not in get_read_type_options("Metagenome", "Illumina"):
        fail("Illumina Single-end was not exposed.")

    for platform in ("Oxford Nanopore", "PacBio"):
        if "Long reads" not in get_read_type_options("Metagenome", platform):
            fail(f"{platform} Long reads was not exposed.")

        goals = get_goal_options(
            "Metagenome",
            platform,
            "Long reads",
            data_state="raw_reads",
        )

        for expected_goal in (
            "Taxonomic profiling",
            "MAG reconstruction",
            "Antibiotic resistance profiling",
            "Virulence profiling",
            "Viral analysis",
            "Plasmid analysis",
        ):
            if expected_goal not in goals:
                fail(f"{platform}: missing goal {expected_goal}")

    validate_route(
        "Illumina",
        "Single-end",
        "Taxonomic profiling",
    )
    validate_route(
        "Illumina",
        "Single-end",
        "MAG reconstruction",
    )
    validate_route(
        "Oxford Nanopore",
        "Long reads",
        "MAG reconstruction",
    )
    validate_route(
        "PacBio",
        "Long reads",
        "Viral analysis",
    )

    print("=" * 76)
    print("Metagenome platform coverage v1")
    print("=" * 76)
    print("Illumina paired-end: retained")
    print("Illumina single-end: PASS")
    print("Oxford Nanopore long reads: PASS")
    print("PacBio long reads: PASS")
    print("Representative dependency routes: PASS")
    print("")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
