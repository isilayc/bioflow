from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.dependencies import validate_workflow
from engine.recommender import (
    build_workflow,
    get_read_type_options,
    get_sequencing_options,
    get_workflow_strategies,
)


def fail(message):
    print("FAIL:", message)
    raise SystemExit(1)


def assert_option(sample_type, expected):
    values = get_sequencing_options(sample_type)
    if expected not in values:
        fail(f"{sample_type}: missing {expected}. Observed: {values}")


def validate_context(sample_type, sequencing, read_type, goal):
    strategies = get_workflow_strategies(
        sample_type,
        sequencing,
        read_type,
        goal,
        data_state="raw_reads",
    )
    if not strategies:
        fail(f"No strategy for {sample_type} / {sequencing} / {read_type} / {goal}")

    workflow = build_workflow(
        sample_type,
        sequencing,
        read_type,
        goal,
        workflow_id=strategies[0]["id"],
        data_state="raw_reads",
    )
    if not workflow:
        fail(f"Could not build {sample_type} / {sequencing} / {goal}")

    report = validate_workflow(workflow["id"], workflow_override=workflow)
    if not report.get("valid"):
        fail(f"Dependency validation failed for {sample_type} / {sequencing} / {goal}: {report}")


def main():
    assert_option("Metagenome", "Illumina + Oxford Nanopore")
    assert_option("Metagenome", "Illumina + PacBio")
    assert_option("Amplicon", "Oxford Nanopore")
    assert_option("Amplicon", "PacBio")
    assert_option("Bulk transcriptome", "Oxford Nanopore")
    assert_option("Bulk transcriptome", "PacBio")
    assert_option("Virome", "Oxford Nanopore")
    assert_option("Virome", "PacBio")
    assert_option("Metatranscriptome", "Oxford Nanopore")
    assert_option("Metatranscriptome", "PacBio")

    if "Paired-end + Long reads" not in get_read_type_options(
        "Metagenome",
        "Illumina + Oxford Nanopore",
    ):
        fail("Hybrid metagenome read layout missing.")

    validate_context("Metagenome", "Illumina + Oxford Nanopore", "Paired-end + Long reads", "MAG reconstruction")
    validate_context("Amplicon", "Oxford Nanopore", "Long reads", "16S rRNA analysis")
    validate_context("Amplicon", "PacBio", "Long reads", "16S rRNA analysis")
    validate_context("Bulk transcriptome", "Oxford Nanopore", "Long reads", "Differential expression")
    validate_context("Bulk transcriptome", "PacBio", "Long reads", "Transcript assembly")
    validate_context("Virome", "Oxford Nanopore", "Long reads", "Viral sequence detection")
    validate_context("Virome", "PacBio", "Long reads", "Viral abundance profiling")
    validate_context("Metatranscriptome", "Oxford Nanopore", "Long reads", "Taxonomic profiling")
    validate_context("Metatranscriptome", "PacBio", "Long reads", "Differential expression")

    print("=" * 78)
    print("OmicsRoute cross-platform coverage v2.1")
    print("=" * 78)
    print("Metagenome hybrid: PASS")
    print("Amplicon long-read platforms: PASS")
    print("Bulk transcriptome long-read platforms: PASS")
    print("Virome long-read platforms: PASS")
    print("Metatranscriptome long-read platforms: PASS")
    print("Representative dependency validation: PASS")
    print("")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
