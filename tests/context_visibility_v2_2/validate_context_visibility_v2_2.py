from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.context_intake import (
    GENE_COUNT_MATRIX,
    METATRANSCRIPTOME_COUNT_MATRIX,
    RANKED_GENE_LIST,
    SIGNIFICANT_GENE_LIST,
    VIRAL_FASTA,
    get_goal_availability,
)
from engine.recommender import (
    build_workflow,
    get_goal_options,
    get_workflow_strategies,
)
from engine.dependencies import validate_workflow


def fail(message):
    print("FAIL:", message)
    raise SystemExit(1)


def assert_visible(sample, state, expected):
    goals = get_goal_options(
        sample,
        "Existing data",
        "Not applicable",
        data_state=state,
        reference_context={
            "status": "not_applicable",
            "usable_reference": False,
        },
    )
    missing = set(expected) - set(goals)
    if missing:
        fail(
            f"{sample}/{state} missing goals: "
            + ", ".join(sorted(missing))
        )


def assert_direct_route(sample, state, goal):
    status = get_goal_availability(sample, state, goal)
    if not status.get("selectable"):
        fail(f"Expected selectable route: {sample}/{state}/{goal}")

    strategies = get_workflow_strategies(
        sample,
        "Existing data",
        "Not applicable",
        goal,
        data_state=state,
        reference_context={
            "status": "not_applicable",
            "usable_reference": False,
        },
    )

    if not strategies:
        fail(f"No strategy for direct route: {sample}/{state}/{goal}")

    workflow = build_workflow(
        sample,
        "Existing data",
        "Not applicable",
        goal,
        workflow_id=strategies[0]["id"],
        data_state=state,
        reference_context={
            "status": "not_applicable",
            "usable_reference": False,
        },
    )

    report = validate_workflow(
        workflow["id"],
        workflow_override=workflow,
    )

    if not report.get("valid"):
        fail(f"Dependency invalid: {sample}/{state}/{goal}")


def main():
    virome_goals = {
        "Viral sequence detection",
        "Viral genome quality assessment",
        "Viral taxonomy",
        "Viral abundance profiling",
        "Viral host prediction",
        "Viral clustering / vOTU analysis",
        "Viral functional annotation",
        "Auxiliary metabolic gene analysis",
    }

    assert_visible("Virome", VIRAL_FASTA, virome_goals)

    for goal in (
        "Viral genome quality assessment",
        "Viral taxonomy",
        "Viral host prediction",
        "Viral clustering / vOTU analysis",
        "Viral functional annotation",
    ):
        assert_direct_route("Virome", VIRAL_FASTA, goal)

    if get_goal_availability(
        "Virome",
        VIRAL_FASTA,
        "Viral sequence detection",
    ).get("status") != "already_satisfied":
        fail("Viral detection should be already_satisfied for viral FASTA.")

    bulk_goals = {
        "Differential expression",
        "Alignment-based RNA-seq",
        "Pseudoalignment / lightweight quantification",
        "Transcript assembly",
        "Functional enrichment",
        "Pathway analysis",
        "Alternative splicing",
    }

    for state in (
        GENE_COUNT_MATRIX,
        SIGNIFICANT_GENE_LIST,
        RANKED_GENE_LIST,
    ):
        assert_visible("Bulk transcriptome", state, bulk_goals)

    assert_direct_route(
        "Bulk transcriptome",
        GENE_COUNT_MATRIX,
        "Differential expression",
    )
    assert_direct_route(
        "Bulk transcriptome",
        SIGNIFICANT_GENE_LIST,
        "Functional enrichment",
    )
    assert_direct_route(
        "Bulk transcriptome",
        RANKED_GENE_LIST,
        "Pathway analysis",
    )

    metatranscriptome_goals = {
        "Host read removal",
        "rRNA depletion assessment",
        "Taxonomic profiling",
        "Functional profiling",
        "Pathway analysis",
        "Differential expression",
    }

    assert_visible(
        "Metatranscriptome",
        METATRANSCRIPTOME_COUNT_MATRIX,
        metatranscriptome_goals,
    )

    assert_direct_route(
        "Metatranscriptome",
        METATRANSCRIPTOME_COUNT_MATRIX,
        "Differential expression",
    )

    print("=" * 72)
    print("OmicsRoute Context Visibility v2.2")
    print("=" * 72)
    print("Virome visibility: PASS")
    print("Bulk transcriptome visibility: PASS")
    print("Metatranscriptome count-matrix intake: PASS")
    print("")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
