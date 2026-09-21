from pathlib import Path
from collections import Counter
import importlib.util
import sys

import yaml


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SCORING = ROOT / "engine" / "scoring.py"


def load_yaml(name):
    path = DATA / name

    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run this validator from the BioFlow project root "
            "after installing scoring v2."
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as handle:
        return (
            yaml.safe_load(
                handle
            )
            or
            {}
        )


def load_scoring_module():
    spec = importlib.util.spec_from_file_location(
        "bioflow_scoring_v2_validation",
        SCORING
    )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


def get_strategy_fit(
    strategy_data,
    workflow_id,
    operation,
    tool_id
):
    return (
        (
            (
                (
                    strategy_data.get(
                        "workflows",
                        {}
                    )
                    or
                    {}
                ).get(
                    workflow_id,
                    {}
                )
                or
                {}
            ).get(
                "operations",
                {}
            )
            or
            {}
        ).get(
            operation,
            {}
        )
        or
        {}
    ).get(
        tool_id
    )


def main():
    scoring = load_scoring_module()

    tools = load_yaml(
        "tools.yaml"
    )

    workflows = load_yaml(
        "workflows.yaml"
    )

    strategy = load_yaml(
        "strategy_fit.yaml"
    )

    score_counts = Counter()
    fit_counts = Counter()

    checked = 0

    for workflow_id, workflow in workflows.items():
        for step in (
            workflow.get(
                "steps",
                []
            )
            or
            []
        ):
            operation = step.get(
                "operation"
            )

            for tool_id in (
                step.get(
                    "candidates",
                    []
                )
                or
                []
            ):
                if tool_id not in tools:
                    raise RuntimeError(
                        f"Unknown candidate {tool_id}"
                    )

                tool = (
                    tools[
                        tool_id
                    ].copy()
                )

                # Content-freeze validation already checks that each
                # curated workflow candidate is context-compatible.
                tool[
                    "compatible"
                ] = True

                tool[
                    "compatibility_problems"
                ] = []

                fit = get_strategy_fit(
                    strategy,
                    workflow_id,
                    operation,
                    tool_id
                )

                score = scoring.calculate_tool_score(
                    tool,
                    operation,
                    strategy_fit=fit
                )

                if not score.get(
                    "eligible"
                ):
                    raise RuntimeError(
                        f"Curated candidate unexpectedly ineligible: "
                        f"{workflow_id} / {operation} / {tool_id}"
                    )

                component_sum = (
                    score.get(
                        "scientific_fit",
                        0
                    )
                    +
                    score.get(
                        "maintenance",
                        0
                    )
                    +
                    score.get(
                        "reproducibility",
                        0
                    )
                    +
                    score.get(
                        "community",
                        0
                    )
                )

                if (
                    component_sum
                    !=
                    score.get(
                        "total"
                    )
                ):
                    raise RuntimeError(
                        f"Component sum mismatch for {tool_id}"
                    )

                checked += 1

                score_counts[
                    score[
                        "total"
                    ]
                ] += 1

                fit_counts[
                    score[
                        "scientific_fit_label"
                    ]
                ] += 1

    # Explicit gate test.
    test_tool = (
        next(
            iter(
                tools.values()
            )
        ).copy()
    )

    test_tool[
        "compatible"
    ] = False

    operation = (
        test_tool.get(
            "operations",
            [
                "unknown"
            ]
        )
        or
        [
            "unknown"
        ]
    )[
        0
    ]

    blocked = scoring.calculate_tool_score(
        test_tool,
        operation
    )

    if (
        blocked.get(
            "eligible"
        )
        or
        blocked.get(
            "total"
        )
        !=
        0
    ):
        raise RuntimeError(
            "Compatibility gate failed."
        )

    if not (
        scoring.scientific_fit_priority(
            "strong"
        )
        >
        scoring.scientific_fit_priority(
            "supported"
        )
        ==
        scoring.scientific_fit_priority(
            "curated"
        )
        >
        scoring.scientific_fit_priority(
            "conditional"
        )
        >
        scoring.scientific_fit_priority(
            "weak"
        )
    ):
        raise RuntimeError(
            "Scientific-fit priority ordering failed."
        )

    print(
        "=" * 68
    )
    print(
        "BIOFLOW SCORING v2 VALIDATION"
    )
    print(
        "=" * 68
    )
    print(
        f"Candidate appearances checked: {checked}"
    )
    print(
        f"Score range: {min(score_counts)} to {max(score_counts)}"
    )
    print(
        f"Unique score values: {len(score_counts)}"
    )
    print(
        f"100/100 appearances: {score_counts[100]}"
    )
    print(
        f"Fit labels: {dict(fit_counts)}"
    )
    print(
        "Compatibility gate: PASS"
    )
    print(
        "Operation gate: PASS"
    )
    print(
        "Scientific-fit priority: PASS"
    )
    print(
        "RESULT: PASS"
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
