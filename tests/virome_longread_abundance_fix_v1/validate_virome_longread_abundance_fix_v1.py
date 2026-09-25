from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.dependencies import validate_workflow
from engine.recommender import build_workflow, get_workflow_strategies


def fail(message):
    print("FAIL:", message)
    raise SystemExit(1)


def check(platform):
    strategies = get_workflow_strategies(
        "Virome",
        platform,
        "Long reads",
        "Viral abundance profiling",
        data_state="raw_reads",
    )

    if len(strategies) < 2:
        fail(
            f"{platform}: expected both contig/genome and vOTU abundance "
            f"strategies, found {len(strategies)}."
        )

    for strategy in strategies:
        workflow = build_workflow(
            "Virome",
            platform,
            "Long reads",
            "Viral abundance profiling",
            workflow_id=strategy["id"],
            data_state="raw_reads",
        )

        if not workflow:
            fail(f"{platform}: could not build {strategy['id']}")

        dep = validate_workflow(
            workflow["id"],
            workflow_override=workflow,
        )

        if not dep.get("valid"):
            fail(
                f"{platform}: dependency validation failed for "
                f"{strategy['id']}: {dep}"
            )

        abundance_steps = [
            step
            for step in workflow.get("steps", [])
            if step.get("operation") == "viral_abundance_profiling"
        ]

        if not abundance_steps:
            fail(
                f"{platform}: no viral_abundance_profiling step in "
                f"{strategy['id']}"
            )

        for step in abundance_steps:
            tools = step.get("tools", []) or []

            if not tools:
                fail(
                    f"{platform}: abundance step has no prepared tools in "
                    f"{strategy['id']}"
                )

            compatible = [
                tool
                for tool in tools
                if tool.get("compatible")
            ]

            if not compatible:
                details = [
                    {
                        "id": tool.get("id"),
                        "problems": tool.get("compatibility_problems"),
                    }
                    for tool in tools
                ]
                fail(
                    f"{platform}: no compatible abundance tool in "
                    f"{strategy['id']}: {details}"
                )


def main():
    check("Oxford Nanopore")
    check("PacBio")

    print("=" * 76)
    print("Virome long-read abundance compatibility fix v1")
    print("=" * 76)
    print("Oxford Nanopore contig/vOTU abundance: PASS")
    print("PacBio contig/vOTU abundance: PASS")
    print("Dependency validation: PASS")
    print("")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
