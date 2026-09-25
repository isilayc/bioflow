from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.main import (
    StrategyRequest,
    WorkflowInspectRequest,
    catalog_coverage,
    health,
    sample_types,
    strategies,
    workflow_inspect,
)


def fail(message: str) -> None:
    print("FAIL:", message)
    raise SystemExit(1)


def main() -> None:
    if health().get("status") != "ok":
        fail("Health endpoint did not return ok.")

    samples = sample_types().get("sample_types", [])

    if "Metagenome" not in samples:
        fail("Metagenome sample type is missing.")

    strategy_payload = strategies(
        StrategyRequest(
            sample_type="Metagenome",
            data_state="raw_reads",
            sequencing="Illumina",
            read_type="Paired-end",
            goal="Functional profiling",
        )
    )

    rows = strategy_payload.get("strategies", [])

    if not rows:
        fail("No Metagenome functional profiling strategy was returned.")

    selected = rows[0]["id"]

    result = workflow_inspect(
        WorkflowInspectRequest(
            sample_type="Metagenome",
            data_state="raw_reads",
            sequencing="Illumina",
            read_type="Paired-end",
            goal="Functional profiling",
            workflow_id=selected,
            dataset_profile={},
            compute_profile={"enabled": False},
        )
    )

    required = (
        "workflow",
        "overview",
        "dependency",
        "constraint_fields",
        "workflow_constraint",
        "reference_guidance",
        "exports",
    )

    for key in required:
        if key not in result:
            fail(f"Missing inspect payload key: {key}")

    workflow = result["workflow"]

    if not workflow.get("steps"):
        fail("Inspected workflow has no steps.")

    first_tools = workflow["steps"][0].get("tools", [])

    if not first_tools:
        fail("First workflow step has no tools.")

    if "_assessment" not in first_tools[0]:
        fail("Tool assessment layer was not attached.")

    if not result["exports"]["markdown"].get("content"):
        fail("Markdown export content is empty.")

    if not result["exports"]["json"].get("content"):
        fail("JSON export content is empty.")

    coverage = catalog_coverage(False)

    if not coverage.get("families"):
        fail("Catalogue coverage returned no families.")

    print("=" * 72)
    print("OmicsRoute Web parity v1")
    print("=" * 72)
    print("API health: PASS")
    print("Workflow inspection: PASS")
    print("Dependency layer: PASS")
    print("Constraint layer: PASS")
    print("Operational layer: PASS")
    print("Export layer: PASS")
    print("Coverage layer: PASS")
    print("")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
