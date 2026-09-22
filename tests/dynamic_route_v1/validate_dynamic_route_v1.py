from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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

def main():
    read_types = get_read_type_options("Eukaryotic genome", "Illumina")
    for expected in ("Paired-end", "Single-end"):
        if expected not in read_types:
            fail(f"Missing read type: {expected}")

    goals = get_goal_options(
        "Eukaryotic genome",
        "Illumina",
        "Single-end",
        reference_context={
            "status": "ncbi_reference",
            "usable_reference": True,
            "reference_accession": "GCF_TEST.1",
        },
    )
    expected_goals = {
        "Variant analysis",
        "Genome quality assessment",
        "Repeat annotation",
        "Gene prediction",
        "Functional annotation",
        "Comparative genomics",
    }
    missing = expected_goals - set(goals)
    if missing:
        fail(f"Missing Single-end goals: {sorted(missing)}")

    variant_strategies = get_workflow_strategies(
        "Eukaryotic genome",
        "Illumina",
        "Single-end",
        "Variant analysis",
    )
    if not variant_strategies:
        fail("No Single-end variant strategy.")

    variant = build_workflow(
        "Eukaryotic genome",
        "Illumina",
        "Single-end",
        "Variant analysis",
        workflow_id=variant_strategies[0]["id"],
    )
    if not variant or not variant.get("dynamic_route"):
        fail("Dynamic variant workflow not materialized.")

    required = set(variant.get("external_inputs", []))
    if "raw_single_fastq" not in required:
        fail("raw_single_fastq missing.")
    if "reference_genome_fasta" not in required:
        fail("reference_genome_fasta missing.")
    if "raw_paired_fastq" in required:
        fail("Single-end route still requires paired reads.")

    report = validate_workflow(
        variant["id"],
        workflow_override=variant,
    )
    if not report.get("valid"):
        fail("Single-end dynamic variant route is not dependency-valid.")

    quality_strategies = get_workflow_strategies(
        "Eukaryotic genome",
        "Illumina",
        "Single-end",
        "Genome quality assessment",
    )
    if not quality_strategies:
        fail("Quality route missing.")

    quality = build_workflow(
        "Eukaryotic genome",
        "Illumina",
        "Single-end",
        "Genome quality assessment",
        workflow_id=quality_strategies[0]["id"],
    )
    if quality.get("infer_read_inputs", True):
        fail("Prerequisite route incorrectly infers raw reads.")

    qreport = validate_workflow(
        quality["id"],
        workflow_override=quality,
    )
    if not qreport.get("valid"):
        fail("Quality prerequisite route is not dependency-valid.")

    gene_strategies = get_workflow_strategies(
        "Eukaryotic genome",
        "Illumina",
        "Single-end",
        "Gene prediction",
    )
    if len(gene_strategies) < 2:
        fail("BRAKER4 + AUGUSTUS routes were not exposed.")

    paired = get_workflow_strategies(
        "Eukaryotic genome",
        "Illumina",
        "Paired-end",
        "Variant analysis",
    )
    if not paired:
        fail("Existing paired-end variant route disappeared.")

    print("=" * 72)
    print("OmicsRoute Dynamic Route Engine v1")
    print("=" * 72)
    print("Paired-end option: PASS")
    print("Single-end option: PASS")
    print("Dynamic Single-end variant route: PASS")
    print("Assembly-level prerequisite routes: PASS")
    print("Multiple gene-prediction routes: PASS")
    print("Existing paired-end route preserved: PASS")
    print("")
    print("RESULT: PASS")

if __name__ == "__main__":
    main()
