from __future__ import annotations

import csv
import json
import sys
import traceback
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path.cwd()

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from engine.context_intake import (
        RAW_READS,
        get_data_state_options,
        get_goal_availability,
    )
    from engine.dependencies import validate_workflow
    from engine.recommender import (
        build_workflow,
        get_goal_options,
        get_read_type_options,
        get_sample_types,
        get_sequencing_options,
        get_workflow_strategies,
    )
except Exception as exc:
    print("Could not import the OmicsRoute engine.")
    print("Run this script from the project root:")
    print(r"C:\Users\Işılay\Documents\bioflow")
    print("")
    raise


STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_DIR = ROOT / "audit" / "coverage_consistency_v1" / STAMP
OUT_DIR.mkdir(parents=True, exist_ok=True)


REFERENCE_CONTEXT = {
    "status": "selected",
    "usable_reference": True,
    "reference_accession": "AUDIT_REFERENCE",
    "reference_name": "Audit placeholder reference",
    "reference_source": "audit",
}


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None):
    if not rows:
        if fieldnames:
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
        else:
            path.write_text("", encoding="utf-8")
        return

    if fieldnames is None:
        keys = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    keys.append(key)
        fieldnames = keys

    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def compact_dependency_issue(report: dict) -> str:
    if not isinstance(report, dict):
        return "Dependency validator returned a non-dict result."

    if report.get("valid"):
        return ""

    useful_keys = (
        "missing_inputs",
        "missing_artifacts",
        "missing_requirements",
        "errors",
        "issues",
        "blocked_steps",
        "unresolved",
    )

    chunks = []
    for key in useful_keys:
        value = report.get(key)
        if value:
            try:
                rendered = json.dumps(value, ensure_ascii=False)
            except Exception:
                rendered = str(value)
            chunks.append(f"{key}={rendered}")

    if chunks:
        return " | ".join(chunks)[:3000]

    try:
        return json.dumps(report, ensure_ascii=False)[:3000]
    except Exception:
        return str(report)[:3000]


def classify_route_kind(workflow: dict, strategy: dict) -> str:
    if workflow.get("dynamic_route") or strategy.get("dynamic"):
        return "dynamic"
    if workflow.get("data_state") and workflow.get("data_state") != RAW_READS:
        return "context"
    route_class = workflow.get("route_class") or strategy.get("route_class")
    if route_class:
        return str(route_class)
    return "curated_static"


def step_compatibility_summary(workflow: dict):
    zero_compatible_steps = []
    insufficient_parallel_steps = []
    incompatible_tools = []
    total_tools = 0
    compatible_tools = 0
    steps_with_no_tools = []

    for index, step in enumerate(workflow.get("steps", []) or [], start=1):
        tools = step.get("tools", []) or []
        mode = str(step.get("mode", "sequential") or "sequential").lower()
        step_name = step.get("name") or step.get("operation") or f"Step {index}"

        if not tools:
            steps_with_no_tools.append(step_name)
            zero_compatible_steps.append(step_name)
            continue

        total_tools += len(tools)
        compatible_count = 0

        for tool in tools:
            if tool.get("compatible", False):
                compatible_count += 1
                compatible_tools += 1
            else:
                tool_name = tool.get("name") or tool.get("id") or "unknown"
                problems = tool.get("compatibility_problems") or []
                incompatible_tools.append(
                    f"{step_name}: {tool_name}"
                    + (f" ({'; '.join(map(str, problems))})" if problems else "")
                )

        if mode == "parallel":
            required = step.get("min_successful_candidates", 1) or 1
            try:
                required = int(required)
            except Exception:
                required = 1

            if compatible_count < required:
                insufficient_parallel_steps.append(
                    f"{step_name}: {compatible_count}/{required} compatible branches"
                )
        else:
            if compatible_count == 0:
                zero_compatible_steps.append(step_name)

    return {
        "total_tools": total_tools,
        "compatible_tools": compatible_tools,
        "incompatible_tools_count": len(incompatible_tools),
        "incompatible_tools": " | ".join(incompatible_tools),
        "zero_compatible_steps_count": len(zero_compatible_steps),
        "zero_compatible_steps": " | ".join(zero_compatible_steps),
        "insufficient_parallel_steps_count": len(insufficient_parallel_steps),
        "insufficient_parallel_steps": " | ".join(insufficient_parallel_steps),
        "steps_with_no_tools_count": len(steps_with_no_tools),
        "steps_with_no_tools": " | ".join(steps_with_no_tools),
    }


def safe_list(callable_obj, *args, **kwargs):
    try:
        value = callable_obj(*args, **kwargs)
        return list(value or []), None
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"


def main():
    route_rows = []
    coverage_rows = []
    context_state_rows = []
    issue_rows = []

    sample_types, sample_error = safe_list(get_sample_types)
    if sample_error:
        raise RuntimeError(sample_error)

    total_contexts = 0
    total_goals = 0
    total_strategies = 0
    built_strategies = 0

    print("=" * 88)
    print("OmicsRoute — Coverage & Consistency Audit v1")
    print("=" * 88)
    print("Output:", OUT_DIR)
    print("")

    # ------------------------------------------------------------------
    # RAW-READ PLATFORM / READ-LAYOUT / GOAL / ROUTE AUDIT
    # ------------------------------------------------------------------
    for sample_type in sample_types:
        sequencing_options, seq_error = safe_list(
            get_sequencing_options,
            sample_type,
        )

        if seq_error:
            issue_rows.append(
                {
                    "severity": "CRITICAL",
                    "category": "sequencing_options_error",
                    "sample_type": sample_type,
                    "sequencing": "",
                    "read_type": "",
                    "goal": "",
                    "strategy_id": "",
                    "detail": seq_error,
                }
            )
            continue

        if not sequencing_options:
            issue_rows.append(
                {
                    "severity": "CRITICAL",
                    "category": "no_sequencing_options",
                    "sample_type": sample_type,
                    "sequencing": "",
                    "read_type": "",
                    "goal": "",
                    "strategy_id": "",
                    "detail": "Sample type is visible but exposes no sequencing platform.",
                }
            )

        for sequencing in sequencing_options:
            read_types, read_error = safe_list(
                get_read_type_options,
                sample_type,
                sequencing,
            )

            if read_error:
                issue_rows.append(
                    {
                        "severity": "CRITICAL",
                        "category": "read_type_options_error",
                        "sample_type": sample_type,
                        "sequencing": sequencing,
                        "read_type": "",
                        "goal": "",
                        "strategy_id": "",
                        "detail": read_error,
                    }
                )
                continue

            if not read_types:
                issue_rows.append(
                    {
                        "severity": "CRITICAL",
                        "category": "orphan_platform",
                        "sample_type": sample_type,
                        "sequencing": sequencing,
                        "read_type": "",
                        "goal": "",
                        "strategy_id": "",
                        "detail": "Sequencing platform is visible but has no read-layout option.",
                    }
                )

            for read_type in read_types:
                total_contexts += 1

                goals_no_ref, goals_error = safe_list(
                    get_goal_options,
                    sample_type,
                    sequencing,
                    read_type,
                    data_state=RAW_READS,
                    reference_context=None,
                )

                goals_with_ref, goals_ref_error = safe_list(
                    get_goal_options,
                    sample_type,
                    sequencing,
                    read_type,
                    data_state=RAW_READS,
                    reference_context=REFERENCE_CONTEXT,
                )

                if goals_error or goals_ref_error:
                    issue_rows.append(
                        {
                            "severity": "CRITICAL",
                            "category": "goal_options_error",
                            "sample_type": sample_type,
                            "sequencing": sequencing,
                            "read_type": read_type,
                            "goal": "",
                            "strategy_id": "",
                            "detail": goals_error or goals_ref_error,
                        }
                    )
                    continue

                # Full route potential includes reference-gated goals.
                goals = []
                seen_goals = set()
                for goal in goals_no_ref + goals_with_ref:
                    if goal not in seen_goals:
                        seen_goals.add(goal)
                        goals.append(goal)

                if not goals:
                    issue_rows.append(
                        {
                            "severity": "CRITICAL",
                            "category": "orphan_read_layout",
                            "sample_type": sample_type,
                            "sequencing": sequencing,
                            "read_type": read_type,
                            "goal": "",
                            "strategy_id": "",
                            "detail": "Read layout is visible but exposes no biological goal.",
                        }
                    )

                goal_strategy_count = 0
                context_broken_goals = 0
                context_dependency_failures = 0
                context_compatibility_failures = 0

                for goal in goals:
                    total_goals += 1
                    ref_required_in_ui = goal not in goals_no_ref and goal in goals_with_ref
                    reference_context = REFERENCE_CONTEXT if ref_required_in_ui else None

                    strategies, strategy_error = safe_list(
                        get_workflow_strategies,
                        sample_type,
                        sequencing,
                        read_type,
                        goal,
                        data_state=RAW_READS,
                        reference_context=reference_context,
                    )

                    if strategy_error:
                        context_broken_goals += 1
                        issue_rows.append(
                            {
                                "severity": "CRITICAL",
                                "category": "strategy_lookup_error",
                                "sample_type": sample_type,
                                "sequencing": sequencing,
                                "read_type": read_type,
                                "goal": goal,
                                "strategy_id": "",
                                "detail": strategy_error,
                            }
                        )
                        continue

                    if not strategies:
                        context_broken_goals += 1
                        issue_rows.append(
                            {
                                "severity": "CRITICAL",
                                "category": "goal_without_strategy",
                                "sample_type": sample_type,
                                "sequencing": sequencing,
                                "read_type": read_type,
                                "goal": goal,
                                "strategy_id": "",
                                "detail": (
                                    "Goal is exposed by the backend but no workflow strategy "
                                    "is available for it."
                                ),
                            }
                        )
                        continue

                    goal_strategy_count += len(strategies)
                    total_strategies += len(strategies)

                    for strategy in strategies:
                        strategy_id = strategy.get("id") or ""
                        workflow_name = strategy.get("name") or strategy_id

                        try:
                            workflow = build_workflow(
                                sample_type,
                                sequencing,
                                read_type,
                                goal,
                                workflow_id=strategy_id,
                                data_state=RAW_READS,
                                reference_context=reference_context,
                            )
                        except Exception as exc:
                            workflow = None
                            build_error = f"{type(exc).__name__}: {exc}"
                        else:
                            build_error = ""

                        if not workflow:
                            context_broken_goals += 1
                            issue_rows.append(
                                {
                                    "severity": "CRITICAL",
                                    "category": "workflow_build_failure",
                                    "sample_type": sample_type,
                                    "sequencing": sequencing,
                                    "read_type": read_type,
                                    "goal": goal,
                                    "strategy_id": strategy_id,
                                    "detail": build_error or "build_workflow returned None.",
                                }
                            )

                            route_rows.append(
                                {
                                    "sample_type": sample_type,
                                    "sequencing": sequencing,
                                    "read_type": read_type,
                                    "goal": goal,
                                    "reference_gated": ref_required_in_ui,
                                    "strategy_id": strategy_id,
                                    "workflow_name": workflow_name,
                                    "route_kind": strategy.get("route_class") or "",
                                    "build_ok": False,
                                    "dependency_valid": False,
                                    "step_count": 0,
                                    "tool_candidates": 0,
                                    "compatible_tools": 0,
                                    "incompatible_tools": 0,
                                    "zero_compatible_steps": 0,
                                    "insufficient_parallel_steps": 0,
                                    "status": "CRITICAL",
                                    "detail": build_error or "Workflow build returned None.",
                                }
                            )
                            continue

                        built_strategies += 1

                        try:
                            dep_report = validate_workflow(
                                workflow["id"],
                                workflow_override=workflow,
                            )
                            dependency_valid = bool(dep_report.get("valid"))
                            dep_detail = compact_dependency_issue(dep_report)
                        except Exception as exc:
                            dependency_valid = False
                            dep_detail = f"{type(exc).__name__}: {exc}"
                            dep_report = {}

                        comp = step_compatibility_summary(workflow)

                        if not dependency_valid:
                            context_dependency_failures += 1
                            issue_rows.append(
                                {
                                    "severity": "HIGH",
                                    "category": "dependency_failure",
                                    "sample_type": sample_type,
                                    "sequencing": sequencing,
                                    "read_type": read_type,
                                    "goal": goal,
                                    "strategy_id": strategy_id,
                                    "detail": dep_detail,
                                }
                            )

                        if (
                            comp["zero_compatible_steps_count"] > 0
                            or comp["insufficient_parallel_steps_count"] > 0
                        ):
                            context_compatibility_failures += 1
                            issue_rows.append(
                                {
                                    "severity": "HIGH",
                                    "category": "tool_compatibility_failure",
                                    "sample_type": sample_type,
                                    "sequencing": sequencing,
                                    "read_type": read_type,
                                    "goal": goal,
                                    "strategy_id": strategy_id,
                                    "detail": (
                                        f"zero_compatible_steps={comp['zero_compatible_steps']} | "
                                        f"insufficient_parallel={comp['insufficient_parallel_steps']}"
                                    ),
                                }
                            )

                        if comp["steps_with_no_tools_count"] > 0:
                            issue_rows.append(
                                {
                                    "severity": "HIGH",
                                    "category": "step_without_candidate_tools",
                                    "sample_type": sample_type,
                                    "sequencing": sequencing,
                                    "read_type": read_type,
                                    "goal": goal,
                                    "strategy_id": strategy_id,
                                    "detail": comp["steps_with_no_tools"],
                                }
                            )

                        status = "PASS"
                        if not dependency_valid:
                            status = "DEPENDENCY_FAIL"
                        if (
                            comp["zero_compatible_steps_count"] > 0
                            or comp["insufficient_parallel_steps_count"] > 0
                        ):
                            status = (
                                "DEPENDENCY_AND_COMPATIBILITY_FAIL"
                                if not dependency_valid
                                else "COMPATIBILITY_FAIL"
                            )

                        route_rows.append(
                            {
                                "sample_type": sample_type,
                                "sequencing": sequencing,
                                "read_type": read_type,
                                "goal": goal,
                                "reference_gated": ref_required_in_ui,
                                "strategy_id": strategy_id,
                                "workflow_name": workflow.get("name") or workflow_name,
                                "route_kind": classify_route_kind(workflow, strategy),
                                "build_ok": True,
                                "dependency_valid": dependency_valid,
                                "step_count": len(workflow.get("steps", []) or []),
                                "tool_candidates": comp["total_tools"],
                                "compatible_tools": comp["compatible_tools"],
                                "incompatible_tools": comp["incompatible_tools_count"],
                                "zero_compatible_steps": comp["zero_compatible_steps_count"],
                                "insufficient_parallel_steps": comp["insufficient_parallel_steps_count"],
                                "status": status,
                                "detail": (
                                    dep_detail
                                    or comp["zero_compatible_steps"]
                                    or comp["insufficient_parallel_steps"]
                                    or ""
                                ),
                            }
                        )

                coverage_rows.append(
                    {
                        "sample_type": sample_type,
                        "sequencing": sequencing,
                        "read_type": read_type,
                        "goals_visible_without_reference": len(goals_no_ref),
                        "goals_with_reference_context": len(goals),
                        "reference_gated_goals": max(0, len(goals) - len(goals_no_ref)),
                        "strategies": goal_strategy_count,
                        "goals_without_strategy_or_build": context_broken_goals,
                        "dependency_failures": context_dependency_failures,
                        "compatibility_failures": context_compatibility_failures,
                        "goals": " | ".join(goals),
                    }
                )

    # ------------------------------------------------------------------
    # NON-RAW DATA-STATE VISIBILITY AUDIT
    # ------------------------------------------------------------------
    for sample_type in sample_types:
        try:
            states = list(get_data_state_options(sample_type) or [])
        except Exception as exc:
            issue_rows.append(
                {
                    "severity": "HIGH",
                    "category": "data_state_error",
                    "sample_type": sample_type,
                    "sequencing": "",
                    "read_type": "",
                    "goal": "",
                    "strategy_id": "",
                    "detail": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        for state in states:
            state_id = state.get("id")
            state_label = state.get("label") or state_id

            if state_id == RAW_READS:
                continue

            try:
                # Non-raw context routes are platform-independent in the
                # current intake architecture.
                goals = get_goal_options(
                    sample_type,
                    "Existing data",
                    "Not applicable",
                    data_state=state_id,
                    reference_context=REFERENCE_CONTEXT,
                )
            except Exception:
                # Some engine versions expose context goals directly but do
                # not accept synthetic sequencing/read labels. Fall back to
                # context availability by asking known goal options through
                # the intake module indirectly.
                try:
                    from engine.context_intake import get_context_goal_options
                    goals = get_context_goal_options(sample_type, state_id)
                except Exception as exc:
                    issue_rows.append(
                        {
                            "severity": "HIGH",
                            "category": "context_goal_error",
                            "sample_type": sample_type,
                            "sequencing": "Existing data",
                            "read_type": "Not applicable",
                            "goal": "",
                            "strategy_id": "",
                            "detail": f"{state_id}: {type(exc).__name__}: {exc}",
                        }
                    )
                    continue

            for goal in goals or []:
                try:
                    availability = get_goal_availability(
                        sample_type,
                        state_id,
                        goal,
                    )
                except Exception as exc:
                    availability = {
                        "status": "error",
                        "selectable": False,
                        "note": f"{type(exc).__name__}: {exc}",
                    }

                context_state_rows.append(
                    {
                        "sample_type": sample_type,
                        "data_state": state_id,
                        "data_state_label": state_label,
                        "goal": goal,
                        "availability_status": availability.get("status", ""),
                        "selectable": availability.get("selectable", ""),
                        "note": availability.get("note", ""),
                    }
                )

    # ------------------------------------------------------------------
    # WRITE OUTPUTS
    # ------------------------------------------------------------------
    write_csv(OUT_DIR / "raw_route_audit.csv", route_rows)
    write_csv(OUT_DIR / "raw_coverage_matrix.csv", coverage_rows)
    write_csv(OUT_DIR / "nonraw_context_state_audit.csv", context_state_rows)
    write_csv(OUT_DIR / "issues.csv", issue_rows)

    issue_counter = Counter(row.get("category", "unknown") for row in issue_rows)
    severity_counter = Counter(row.get("severity", "unknown") for row in issue_rows)

    sample_summary = defaultdict(
        lambda: {
            "contexts": 0,
            "goals": 0,
            "strategies": 0,
            "dependency_failures": 0,
            "compatibility_failures": 0,
        }
    )

    for row in coverage_rows:
        item = sample_summary[row["sample_type"]]
        item["contexts"] += 1
        item["goals"] += int(row["goals_with_reference_context"])
        item["strategies"] += int(row["strategies"])
        item["dependency_failures"] += int(row["dependency_failures"])
        item["compatibility_failures"] += int(row["compatibility_failures"])

    report_lines = [
        "# OmicsRoute Coverage & Consistency Audit v1",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Executive summary",
        "",
        f"- Sample types: **{len(sample_types)}**",
        f"- Raw sequencing/read-layout contexts: **{total_contexts}**",
        f"- Biological goal exposures audited: **{total_goals}**",
        f"- Workflow strategies discovered: **{total_strategies}**",
        f"- Workflow strategies built successfully: **{built_strategies}**",
        f"- Issues recorded: **{len(issue_rows)}**",
        f"- Critical issues: **{severity_counter.get('CRITICAL', 0)}**",
        f"- High issues: **{severity_counter.get('HIGH', 0)}**",
        "",
        "## Sample-type coverage",
        "",
        "| Sample type | Platform/read contexts | Goal exposures | Strategies | Dependency failures | Compatibility failures |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for sample_type in sample_types:
        item = sample_summary[sample_type]
        report_lines.append(
            f"| {sample_type} | {item['contexts']} | {item['goals']} | "
            f"{item['strategies']} | {item['dependency_failures']} | "
            f"{item['compatibility_failures']} |"
        )

    report_lines.extend(
        [
            "",
            "## Issue categories",
            "",
        ]
    )

    if issue_counter:
        for category, count in issue_counter.most_common():
            report_lines.append(f"- **{category}**: {count}")
    else:
        report_lines.append("- No issues detected.")

    report_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A visible sequencing platform/read-layout/goal is treated as a UI promise. "
            "The audit flags a critical issue when that promise has no strategy or cannot "
            "be built. Dependency failures and steps with no compatible candidate tools are "
            "reported separately so catalogue breadth is not confused with executable coverage.",
            "",
            "Reference-gated genome goals are audited twice: first as the UI appears without "
            "a selected reference, then with a placeholder usable-reference context. This avoids "
            "incorrectly treating a deliberately hidden reference-dependent goal as missing.",
            "",
            "Non-raw data states are reported separately because they are artifact-driven rather "
            "than sequencing-platform-driven.",
            "",
            "## Files",
            "",
            "- `raw_coverage_matrix.csv` — platform/read-layout/goal coverage by sample type",
            "- `raw_route_audit.csv` — every discovered strategy with dependency/tool-compatibility result",
            "- `issues.csv` — actionable gaps and failures",
            "- `nonraw_context_state_audit.csv` — assembly/table/FASTA downstream-state visibility",
            "- `summary.json` — machine-readable audit totals",
        ]
    )

    (OUT_DIR / "REPORT.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sample_types": len(sample_types),
        "raw_contexts": total_contexts,
        "goal_exposures": total_goals,
        "strategies": total_strategies,
        "built_strategies": built_strategies,
        "issues": len(issue_rows),
        "severity_counts": dict(severity_counter),
        "issue_category_counts": dict(issue_counter),
        "output_directory": str(OUT_DIR),
    }

    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Sample types:", len(sample_types))
    print("Raw contexts:", total_contexts)
    print("Goal exposures:", total_goals)
    print("Strategies:", total_strategies)
    print("Built strategies:", built_strategies)
    print("Issues:", len(issue_rows))
    print("  CRITICAL:", severity_counter.get("CRITICAL", 0))
    print("  HIGH:", severity_counter.get("HIGH", 0))
    print("")
    print("Report:", OUT_DIR / "REPORT.md")
    print("Issues:", OUT_DIR / "issues.csv")
    print("")
    print("=" * 88)
    print("AUDIT COMPLETED")
    if issue_rows:
        print("RESULT: ISSUES FOUND — review REPORT.md and issues.csv")
    else:
        print("RESULT: CLEAN")
    print("=" * 88)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("")
        print("=" * 88)
        print("AUDIT CRASHED")
        print("=" * 88)
        traceback.print_exc()
        raise
