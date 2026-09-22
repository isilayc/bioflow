from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.context_intake import (
    GENOME_ASSEMBLY,
    PREDICTED_PROTEINS,
    RAW_READS,
    filter_goal_options,
    get_context_goal_options,
    get_data_state_options,
)
from engine.recommender import (
    build_workflow,
    get_goal_options,
    get_workflow_strategies,
)
from engine.dependencies import validate_workflow
from services.ncbi_reference import (
    parse_taxon_suggestions,
    parse_assembly_reports,
    reference_context_from_assembly,
)


def fail(message):
    print("FAIL:", message)
    raise SystemExit(1)


def main():
    euk_states = {
        item["id"]
        for item in get_data_state_options(
            "Eukaryotic genome"
        )
    }

    if {
        RAW_READS,
        GENOME_ASSEMBLY,
        PREDICTED_PROTEINS,
    } - euk_states:
        fail("Eukaryotic data-state options are incomplete.")

    no_ref = {
        "status": "no_reference",
        "usable_reference": False,
    }

    with_ref = {
        "status": "ncbi_reference",
        "usable_reference": True,
        "reference_accession": "GCF_000001405.40",
    }

    filtered = filter_goal_options(
        [
            "Genome assembly",
            "Variant analysis",
        ],
        "Eukaryotic genome",
        RAW_READS,
        no_ref,
    )

    if "Variant analysis" in filtered:
        fail("Variant analysis remained selectable without a reference.")

    filtered = filter_goal_options(
        [
            "Genome assembly",
            "Variant analysis",
        ],
        "Eukaryotic genome",
        RAW_READS,
        with_ref,
    )

    if "Variant analysis" not in filtered:
        fail("Variant analysis was not restored after selecting a reference.")

    assembly_goals = get_context_goal_options(
        "Eukaryotic genome",
        GENOME_ASSEMBLY,
    )

    for expected in (
        "Genome quality assessment",
        "Repeat annotation",
        "Gene prediction",
        "Comparative genomics",
    ):
        if expected not in assembly_goals:
            fail(f"Missing assembly-level goal: {expected}")

    protein_goals = get_context_goal_options(
        "Eukaryotic genome",
        PREDICTED_PROTEINS,
    )

    if protein_goals != [
        "Functional annotation"
    ]:
        fail("Predicted-protein intake did not resolve functional annotation.")

    strategies = get_workflow_strategies(
        "Eukaryotic genome",
        "Existing assembly",
        "Not applicable",
        "Genome quality assessment",
        data_state=GENOME_ASSEMBLY,
        reference_context=no_ref,
    )

    if not strategies:
        fail("No eukaryotic existing-assembly strategy was produced.")

    workflow = build_workflow(
        "Eukaryotic genome",
        "Existing assembly",
        "Not applicable",
        "Genome quality assessment",
        workflow_id=strategies[0]["id"],
        data_state=GENOME_ASSEMBLY,
        reference_context=no_ref,
    )

    if not workflow:
        fail("Existing-assembly workflow could not be materialized.")

    report = validate_workflow(
        workflow["id"],
        workflow_override=workflow,
    )

    if not report.get("valid"):
        fail("Existing-assembly eukaryotic route is not dependency-valid.")

    bacterial_strategies = get_workflow_strategies(
        "Bacterial isolate",
        "Existing assembly",
        "Not applicable",
        "Antimicrobial resistance detection",
        data_state=GENOME_ASSEMBLY,
        reference_context=no_ref,
    )

    if not bacterial_strategies:
        fail("No bacterial assembly-level AMR route was produced.")

    bacterial = build_workflow(
        "Bacterial isolate",
        "Existing assembly",
        "Not applicable",
        "Antimicrobial resistance detection",
        workflow_id=bacterial_strategies[0]["id"],
        data_state=GENOME_ASSEMBLY,
        reference_context=no_ref,
    )

    if bacterial.get("external_inputs") != ["genome_fasta"]:
        fail("Bacterial assembly route does not start from genome_fasta.")

    taxonomy_mock = {
        "sci_name_and_ids": [
            {
                "tax_id": 9606,
                "sci_name": "Homo sapiens",
                "common_name": "human",
                "rank": "species",
            }
        ]
    }

    taxa = parse_taxon_suggestions(
        taxonomy_mock
    )

    if taxa[0]["tax_id"] != 9606:
        fail("NCBI taxonomy parser failed.")

    assembly_mock = {
        "reports": [
            {
                "accession": "GCF_000001405.40",
                "current_accession": "GCF_000001405.40",
                "source_database": "SOURCE_DATABASE_REFSEQ",
                "organism": {
                    "tax_id": 9606,
                    "organism_name": "Homo sapiens",
                    "common_name": "human",
                },
                "assembly_info": {
                    "assembly_level": "Chromosome",
                    "assembly_status": "current",
                    "assembly_name": "GRCh38.p14",
                    "refseq_category": "reference genome",
                },
                "annotation_info": {
                    "status": "Full annotation",
                },
            }
        ]
    }

    assemblies = parse_assembly_reports(
        assembly_mock
    )

    if not assemblies or not assemblies[0]["is_reference"]:
        fail("NCBI assembly parser failed to recognize a reference genome.")

    ref_context = reference_context_from_assembly(
        assemblies[0],
        taxon=taxa[0],
    )

    if not ref_context.get("usable_reference"):
        fail("Reference context was not marked usable.")

    dynamic_goals = get_goal_options(
        "Eukaryotic genome",
        "Illumina",
        "Single-end",
        data_state=RAW_READS,
        reference_context=with_ref,
    )

    if "Variant analysis" not in dynamic_goals:
        fail("Reference-aware dynamic goal filtering failed.")

    print("=" * 72)
    print("OmicsRoute Context Intake + Reference Finder v1")
    print("=" * 72)
    print("Data-state intake: PASS")
    print("Reference-dependent goal gating: PASS")
    print("Existing-assembly route synthesis: PASS")
    print("NCBI taxonomy parser: PASS")
    print("NCBI assembly/reference parser: PASS")
    print("")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
