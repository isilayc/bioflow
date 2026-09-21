from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from validate_constraints import validate_constraints
from engine.constraints import (
    evaluate_tool_constraints,
    evaluate_workflow_constraints,
    get_tool_constraint_definition,
)


PASS = "pass"
WARNING = "warning"
BLOCK = "block"
NEEDS_INPUT = "needs_input"


def assert_status(name, actual, expected, failures):
    if actual != expected:
        failures.append(f"{name}: expected {expected!r}, got {actual!r}")
    else:
        print(f"[PASS] {name}: {actual}")


def tool_status(tool_id, profile):
    return evaluate_tool_constraints(tool_id, profile).get("status")


def workflow_status(workflow_id, profile):
    return evaluate_workflow_constraints(workflow_id, profile).get("status")


def main():
    failures = []

    print("=" * 72)
    print("BioFlow Constraint Coverage v1 validation")
    print("=" * 72)

    structural_errors, _warnings = validate_constraints(verbose=False)
    if structural_errors:
        print("[FAIL] Structural validation")
        for error in structural_errors:
            print("   -", error)
        failures.extend(structural_errors)
    else:
        print("[PASS] Structural validation")

    required_tools = {
        "dada2", "checkv", "genomad", "virsorter2", "iphop", "gtdbtk", "metabat2"
    }
    for tool_id in sorted(required_tools):
        if get_tool_constraint_definition(tool_id) is None:
            failures.append(f"Missing constraint definition for {tool_id}")
            print(f"[FAIL] definition exists: {tool_id}")
        else:
            print(f"[PASS] definition exists: {tool_id}")

    # CheckV
    assert_status("CheckV standard", tool_status("checkv", {
        "min_viral_contig_length": 1000,
        "checkv_database_available": True,
    }), PASS, failures)
    assert_status("CheckV short contigs", tool_status("checkv", {
        "min_viral_contig_length": 500,
        "checkv_database_available": True,
    }), WARNING, failures)
    assert_status("CheckV database missing", tool_status("checkv", {
        "min_viral_contig_length": 1000,
        "checkv_database_available": False,
    }), BLOCK, failures)

    # geNomad
    assert_status("geNomad standard", tool_status("genomad", {
        "genomad_database_available": True,
        "genomad_min_sequence_length": 2500,
    }), PASS, failures)
    assert_status("geNomad short-sequence advisory", tool_status("genomad", {
        "genomad_database_available": True,
        "genomad_min_sequence_length": 1000,
    }), WARNING, failures)
    assert_status("geNomad database missing", tool_status("genomad", {
        "genomad_database_available": False,
        "genomad_min_sequence_length": 2500,
    }), BLOCK, failures)

    # VirSorter2
    assert_status("VirSorter2 standard", tool_status("virsorter2", {
        "virsorter2_database_available": True,
        "virsorter2_min_length": 1500,
    }), PASS, failures)
    assert_status("VirSorter2 short threshold", tool_status("virsorter2", {
        "virsorter2_database_available": True,
        "virsorter2_min_length": 500,
    }), WARNING, failures)
    assert_status("VirSorter2 database missing", tool_status("virsorter2", {
        "virsorter2_database_available": False,
        "virsorter2_min_length": 1500,
    }), BLOCK, failures)

    # iPHoP
    iphop_pass = {
        "iphop_database_available": True,
        "iphop_input_is_prokaryotic_virus": True,
        "iphop_viral_sequences_quality_assessed": True,
    }
    assert_status("iPHoP standard", tool_status("iphop", iphop_pass), PASS, failures)
    iphop_warn = dict(iphop_pass)
    iphop_warn["iphop_viral_sequences_quality_assessed"] = False
    assert_status("iPHoP uncurated viral input", tool_status("iphop", iphop_warn), WARNING, failures)
    iphop_block = dict(iphop_pass)
    iphop_block["iphop_input_is_prokaryotic_virus"] = False
    assert_status("iPHoP outside viral scope", tool_status("iphop", iphop_block), BLOCK, failures)

    # GTDB-Tk
    gtdb_pass = {
        "gtdbtk_database_compatible": True,
        "gtdbtk_input_is_bacteria_archaea": True,
        "gtdbtk_genomes_quality_screened": True,
    }
    assert_status("GTDB-Tk standard", tool_status("gtdbtk", gtdb_pass), PASS, failures)
    gtdb_warn = dict(gtdb_pass)
    gtdb_warn["gtdbtk_genomes_quality_screened"] = False
    assert_status("GTDB-Tk unscreened genomes", tool_status("gtdbtk", gtdb_warn), WARNING, failures)
    gtdb_block = dict(gtdb_pass)
    gtdb_block["gtdbtk_database_compatible"] = False
    assert_status("GTDB-Tk database mismatch", tool_status("gtdbtk", gtdb_block), BLOCK, failures)

    # MetaBAT2
    assert_status("MetaBAT2 standard", tool_status("metabat2", {
        "metabat2_min_contig_length": 1500,
        "metabat2_depth_available": True,
    }), PASS, failures)
    assert_status("MetaBAT2 short contigs", tool_status("metabat2", {
        "metabat2_min_contig_length": 1000,
        "metabat2_depth_available": True,
    }), WARNING, failures)
    assert_status("MetaBAT2 no depth", tool_status("metabat2", {
        "metabat2_min_contig_length": 1500,
        "metabat2_depth_available": False,
    }), WARNING, failures)

    # DADA2 existing paired-end overlap rule.
    assert_status("DADA2 overlap pass", tool_status("dada2", {
        "read_type": "Paired-end",
        "forward_retained_length": 250,
        "reverse_retained_length": 250,
        "expected_amplicon_length": 460,
    }), PASS, failures)
    assert_status("DADA2 overlap warning", tool_status("dada2", {
        "read_type": "Paired-end",
        "forward_retained_length": 220,
        "reverse_retained_length": 220,
        "expected_amplicon_length": 430,
    }), WARNING, failures)
    assert_status("DADA2 missing overlap inputs", tool_status("dada2", {
        "read_type": "Paired-end",
    }), NEEDS_INPUT, failures)

    # Regression test for an existing workflow-level constraint.
    assert_status("Pangenome workflow 2 genomes", workflow_status(
        "bacterial_illumina_pangenome", {"genome_count": 2}
    ), PASS, failures)
    assert_status("Pangenome workflow 1 genome", workflow_status(
        "bacterial_illumina_pangenome", {"genome_count": 1}
    ), BLOCK, failures)

    print("\n" + "=" * 72)
    if failures:
        print(f"RESULT: FAIL ({len(failures)} issue(s))")
        for failure in failures:
            print("  -", failure)
        return 1
    print("RESULT: PASS")
    print("Constraint coverage v1 is structurally valid and functional tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
