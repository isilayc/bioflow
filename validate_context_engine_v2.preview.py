from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.context_intake import (
    GENE_COUNT_MATRIX,
    METAGENOME_CONTIGS,
    RANKED_GENE_LIST,
    SIGNIFICANT_GENE_LIST,
    VIRAL_FASTA,
    get_context_goal_options,
    get_data_state_options,
)
from engine.recommender import (
    build_workflow,
    get_goal_options,
    get_read_type_options,
    get_workflow_strategies,
)
from engine.dependencies import validate_workflow


def fail(message):
    print("FAIL:", message)
    raise SystemExit(1)


def build_context_route(
    sample,
    state,
    goal,
):
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
        fail(
            f"No context strategy: {sample} / {state} / {goal}"
        )

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

    if not workflow:
        fail(
            f"Could not materialize: {sample} / {state} / {goal}"
        )

    report = validate_workflow(
        workflow["id"],
        workflow_override=workflow,
    )

    if not report.get("valid"):
        fail(
            f"Dependency invalid: {sample} / {state} / {goal}: {report}"
        )

    return workflow


def main():
    bacterial_reads = get_read_type_options(
        "Bacterial isolate",
        "Illumina",
    )

    if "Single-end" not in bacterial_reads:
        fail(
            "Bacterial Illumina Single-end option is missing."
        )

    no_reference = {
        "status": "no_reference",
        "usable_reference": False,
    }

    with_reference = {
        "status": "ncbi_reference",
        "usable_reference": True,
        "reference_accession": "GCF_TEST.1",
    }

    bacterial_goals_no_ref = get_goal_options(
        "Bacterial isolate",
        "Illumina",
        "Single-end",
        reference_context=no_reference,
    )

    if "Whole genome characterization" not in bacterial_goals_no_ref:
        fail(
            "Bacterial Single-end WGS goal is missing."
        )

    if "Variant analysis" in bacterial_goals_no_ref:
        fail(
            "Bacterial variant analysis is visible without a reference."
        )

    bacterial_goals_with_ref = get_goal_options(
        "Bacterial isolate",
        "Illumina",
        "Single-end",
        reference_context=with_reference,
    )

    if "Variant analysis" not in bacterial_goals_with_ref:
        fail(
            "Bacterial variant analysis did not appear with a reference."
        )

    strategies = get_workflow_strategies(
        "Bacterial isolate",
        "Illumina",
        "Single-end",
        "Whole genome characterization",
    )

    if not strategies:
        fail(
            "No bacterial Single-end WGS strategy was produced."
        )

    bacterial_wgs = build_workflow(
        "Bacterial isolate",
        "Illumina",
        "Single-end",
        "Whole genome characterization",
        workflow_id=strategies[0]["id"],
    )

    bacterial_report = validate_workflow(
        bacterial_wgs["id"],
        workflow_override=bacterial_wgs,
    )

    if not bacterial_report.get("valid"):
        fail(
            "Bacterial Single-end WGS is not dependency-valid."
        )

    metagenome_states = {
        item["id"]
        for item in get_data_state_options(
            "Metagenome"
        )
    }

    if METAGENOME_CONTIGS not in metagenome_states:
        fail(
            "Metagenome contig data state is missing."
        )

    for expected in (
        "Virulence profiling",
        "Viral analysis",
        "Plasmid analysis",
    ):
        if expected not in get_context_goal_options(
            "Metagenome",
            METAGENOME_CONTIGS,
        ):
            fail(
                f"Missing metagenome-contig goal: {expected}"
            )

    build_context_route(
        "Metagenome",
        METAGENOME_CONTIGS,
        "Viral analysis",
    )

    virome_states = {
        item["id"]
        for item in get_data_state_options(
            "Virome"
        )
    }

    if VIRAL_FASTA not in virome_states:
        fail(
            "Virome viral-FASTA data state is missing."
        )

    build_context_route(
        "Virome",
        VIRAL_FASTA,
        "Viral genome quality assessment",
    )

    transcriptome_states = {
        item["id"]
        for item in get_data_state_options(
            "Bulk transcriptome"
        )
    }

    for required in (
        GENE_COUNT_MATRIX,
        SIGNIFICANT_GENE_LIST,
        RANKED_GENE_LIST,
    ):
        if required not in transcriptome_states:
            fail(
                f"Missing transcriptome data state: {required}"
            )

    build_context_route(
        "Bulk transcriptome",
        GENE_COUNT_MATRIX,
        "Differential expression",
    )

    build_context_route(
        "Bulk transcriptome",
        SIGNIFICANT_GENE_LIST,
        "Functional enrichment",
    )

    build_context_route(
        "Bulk transcriptome",
        RANKED_GENE_LIST,
        "Pathway analysis",
    )

    print("=" * 72)
    print("OmicsRoute Context Engine v2")
    print("=" * 72)
    print("Bacterial Illumina Single-end: PASS")
    print("Reference-aware bacterial variant gating: PASS")
    print("Metagenome contig intake: PASS")
    print("Virome viral-FASTA intake: PASS")
    print("Bulk transcriptome downstream intake: PASS")
    print("")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
