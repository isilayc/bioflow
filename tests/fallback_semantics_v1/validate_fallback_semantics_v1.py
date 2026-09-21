from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.fallbacks import get_recovery_rule, find_alternative_strategies

DATA = ROOT / "data"


def load_yaml(name):
    with (DATA / name).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def candidates(step):
    vals = step.get("candidates")
    if isinstance(vals, list) and vals:
        return vals
    out = []
    if step.get("preferred"):
        out.append(step["preferred"])
    out.extend(step.get("alternatives", []) or [])
    return out


def main():
    ok = True
    failures = []
    workflows = load_yaml("workflows.yaml")
    fallbacks = load_yaml("fallbacks.yaml")

    if not isinstance(fallbacks.get("rules"), list):
        failures.append("fallbacks.yaml rules must be a list")

    viral_detection_steps = 0
    for workflow_id, workflow in workflows.items():
        if not isinstance(workflow, dict):
            continue
        for step in workflow.get("steps", []) or []:
            if not isinstance(step, dict):
                continue
            if step.get("operation") != "viral_sequence_detection":
                continue
            c = candidates(step)
            if "genomad" in c:
                viral_detection_steps += 1
                if "virsorter2" not in c:
                    failures.append(
                        f"{workflow_id}: geNomad viral detection has no VirSorter2 fallback"
                    )

    expected_pairs = [
        ("checkv", "viral_quality"),
        ("checkv", "viral_genome_quality"),
        ("genomad", "viral_taxonomy"),
        ("genomad", "plasmid_detection"),
        ("genomad", "viral_sequence_detection"),
        ("dada2", "asv_inference"),
        ("iphop", "viral_host_prediction"),
        ("virsorter2", "dramv_preparation"),
        ("busco", "genome_quality_assessment"),
        ("gtdbtk", "species_identification"),
        ("gtdbtk", "mag_taxonomy"),
    ]

    for tool_id, operation in expected_pairs:
        if get_recovery_rule(tool_id, operation) is None:
            failures.append(f"Missing recovery rule for {tool_id}/{operation}")

    # These alternatives already exist in the BioFlow workflow catalog.
    known_cases = [
        (
            "bacterial_illumina_species_identification_gtdbtk",
            ["gtdbtk"],
            "bacterial_illumina_species_identification_fastani",
        ),
        (
            "bacterial_illumina_plasmid_genomad",
            ["genomad"],
            "bacterial_illumina_plasmid_mobsuite",
        ),
        (
            "metagenome_illumina_plasmid_genomad",
            ["genomad"],
            "metagenome_illumina_plasmid_plasx",
        ),
    ]

    # Amplicon strategy names can evolve, so require at least one same-context
    # route that avoids DADA2 rather than hard-coding one package name.
    amp = workflows.get("amplicon_illumina_16s", {})
    if isinstance(amp, dict):
        wf = dict(amp)
        wf["id"] = "amplicon_illumina_16s"
        alternatives = find_alternative_strategies(wf, ["dada2"], limit=50)
        if not alternatives:
            failures.append("No alternative 16S workflow strategy was found when DADA2 is blocked")

    for workflow_id, blocked, expected_id in known_cases:
        source = workflows.get(workflow_id)
        if not isinstance(source, dict):
            failures.append(f"Expected workflow not found: {workflow_id}")
            continue
        wf = dict(source)
        wf["id"] = workflow_id
        found = {x["id"] for x in find_alternative_strategies(wf, blocked, limit=50)}
        if expected_id not in found:
            failures.append(
                f"{workflow_id}: expected alternative strategy {expected_id} was not discovered"
            )

    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    for marker in [
        "from engine.fallbacks import",
        "def show_step_recovery_guidance(",
        "show_step_recovery_guidance(",
        "No ready candidate remains for this step",
    ]:
        if marker not in app_text:
            failures.append(f"app.py integration marker missing: {marker}")

    print("=" * 72)
    print("BioFlow Fallback Semantics v1")
    print("=" * 72)
    print(f"geNomad viral-detection steps checked: {viral_detection_steps}")
    print(f"Explicit recovery rule pairs checked: {len(expected_pairs)}")

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        print("\nRESULT: FAIL")
        return 1

    print("\nRESULT: PASS")
    print("Fallback semantics v1 is structurally valid and recovery routes resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
