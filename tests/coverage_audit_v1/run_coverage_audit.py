from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import yaml
except Exception as exc:
    print("ERROR: PyYAML is required. Activate the BioFlow virtual environment first.")
    print(exc)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

WORKFLOWS = DATA / "workflows.yaml"
TOOLS = DATA / "tools.yaml"
TOOL_IO = DATA / "tool_io.yaml"
CONSTRAINTS = DATA / "constraints.yaml"

def load_yaml(path: Path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)

def norm_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]

def get_candidates(step):
    candidates = norm_list(step.get("candidates"))
    if candidates:
        return [x for x in candidates if x]
    out = []
    preferred = step.get("preferred")
    if preferred:
        out.append(preferred)
    out.extend(norm_list(step.get("alternatives")))
    seen = set()
    dedup = []
    for x in out:
        if x and x not in seen:
            seen.add(x)
            dedup.append(x)
    return dedup

def has_io_route(tool_io, tool_id):
    rec = (tool_io or {}).get(tool_id)
    if not isinstance(rec, dict):
        return False
    routes = rec.get("routes")
    return isinstance(routes, list) and len(routes) > 0

def constraint_tools(constraints):
    if not isinstance(constraints, dict):
        return set()
    tools = constraints.get("tools", {})
    if not isinstance(tools, dict):
        return set()
    return set(tools.keys())

def main():
    workflows = load_yaml(WORKFLOWS)
    tools = load_yaml(TOOLS)
    tool_io = load_yaml(TOOL_IO)
    constraints = load_yaml(CONSTRAINTS)

    missing = [str(p) for p, d in [(WORKFLOWS, workflows), (TOOLS, tools), (TOOL_IO, tool_io)] if d is None]
    if missing:
        print("RESULT: FAIL")
        print("Missing required files:")
        for p in missing:
            print(" -", p)
        return 2

    if not isinstance(workflows, dict) or not isinstance(tools, dict) or not isinstance(tool_io, dict):
        print("RESULT: FAIL")
        print("workflows.yaml, tools.yaml, and tool_io.yaml must parse to mappings.")
        return 2

    ctools = constraint_tools(constraints)
    rows = []
    unknown_candidates = []
    missing_io = []
    single_candidate_steps = []
    constrained_singletons = []
    operation_candidates = defaultdict(set)

    total_steps = 0
    total_candidate_refs = 0

    for workflow_id, workflow in workflows.items():
        if not isinstance(workflow, dict):
            continue
        steps = workflow.get("steps", [])
        if not isinstance(steps, list):
            continue
        for idx, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                continue
            total_steps += 1
            operation = step.get("operation", "")
            step_name = step.get("name", "")
            candidates = get_candidates(step)
            total_candidate_refs += len(candidates)

            for tool_id in candidates:
                operation_candidates[operation].add(tool_id)

            if len(candidates) == 1:
                single_candidate_steps.append((workflow_id, idx, operation, step_name, candidates[0]))
                if candidates[0] in ctools:
                    constrained_singletons.append((workflow_id, idx, operation, step_name, candidates[0]))

            for rank, tool_id in enumerate(candidates, start=1):
                tool_known = tool_id in tools
                io_known = has_io_route(tool_io, tool_id)
                has_constraint = tool_id in ctools

                if not tool_known:
                    unknown_candidates.append((workflow_id, idx, operation, tool_id))
                if not io_known:
                    missing_io.append((workflow_id, idx, operation, tool_id))

                rows.append({
                    "workflow_id": workflow_id,
                    "step_number": idx,
                    "step_name": step_name,
                    "operation": operation,
                    "candidate_rank_in_yaml": rank,
                    "tool_id": tool_id,
                    "tool_defined": tool_known,
                    "io_route_defined": io_known,
                    "constraint_defined": has_constraint,
                    "candidate_count_for_step": len(candidates),
                    "fallback_available": len(candidates) >= 2,
                    "risk_if_blocked": "HIGH" if (len(candidates) == 1 and has_constraint) else ("MEDIUM" if len(candidates) == 1 else "LOW"),
                })

    operation_summary = []
    for operation, tids in sorted(operation_candidates.items()):
        operation_summary.append({
            "operation": operation,
            "unique_candidate_tools": len(tids),
            "tool_ids": ", ".join(sorted(tids)),
            "alternative_depth": "LOW" if len(tids) <= 1 else ("MODERATE" if len(tids) == 2 else "GOOD"),
        })

    candidate_tools = {r["tool_id"] for r in rows}
    constrained_candidates = candidate_tools & ctools
    constraint_coverage_pct = (100.0 * len(constrained_candidates) / len(candidate_tools)) if candidate_tools else 0.0
    fallback_step_pct = (100.0 * sum(1 for r in { (x["workflow_id"], x["step_number"]): x for x in rows }.values() if r["candidate_count_for_step"] >= 2) / total_steps) if total_steps else 0.0
    singleton_pct = (100.0 * len(single_candidate_steps) / total_steps) if total_steps else 0.0

    csv_path = OUT / "COVERAGE_AUDIT_V1_STEP_CANDIDATES.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else [
            "workflow_id","step_number","step_name","operation","candidate_rank_in_yaml",
            "tool_id","tool_defined","io_route_defined","constraint_defined",
            "candidate_count_for_step","fallback_available","risk_if_blocked"
        ])
        writer.writeheader()
        writer.writerows(rows)

    op_csv = OUT / "COVERAGE_AUDIT_V1_OPERATIONS.csv"
    with op_csv.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=["operation","unique_candidate_tools","tool_ids","alternative_depth"])
        writer.writeheader()
        writer.writerows(operation_summary)

    summary = {
        "total_workflows": len([w for w in workflows.values() if isinstance(w, dict)]),
        "total_steps": total_steps,
        "total_candidate_references": total_candidate_refs,
        "unique_candidate_tools": len(candidate_tools),
        "constraint_covered_candidate_tools": len(constrained_candidates),
        "constraint_coverage_pct": round(constraint_coverage_pct, 2),
        "single_candidate_steps": len(single_candidate_steps),
        "single_candidate_steps_pct": round(singleton_pct, 2),
        "single_candidate_steps_with_constraints": len(constrained_singletons),
        "steps_with_fallback_pct": round(100.0 - singleton_pct, 2),
        "unknown_candidate_refs": len(unknown_candidates),
        "candidate_refs_missing_io_route": len(missing_io),
        "operations_with_only_one_unique_tool": sum(1 for x in operation_summary if x["unique_candidate_tools"] <= 1),
    }

    json_path = OUT / "COVERAGE_AUDIT_V1_SUMMARY.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    report = []
    report.append("# BioFlow Coverage Audit v1")
    report.append("")
    report.append("This is an internal product-coverage audit. It is not an external scientific validation.")
    report.append("")
    report.append("## Executive summary")
    report.append("")
    report.append(f"- Workflows: **{summary['total_workflows']}**")
    report.append(f"- Workflow steps: **{summary['total_steps']}**")
    report.append(f"- Unique candidate tools used by workflows: **{summary['unique_candidate_tools']}**")
    report.append(f"- Candidate tools with dataset constraints: **{summary['constraint_covered_candidate_tools']} / {summary['unique_candidate_tools']} ({summary['constraint_coverage_pct']:.2f}%)**")
    report.append(f"- Steps with only one candidate tool: **{summary['single_candidate_steps']} ({summary['single_candidate_steps_pct']:.2f}%)**")
    report.append(f"- Singleton steps whose only tool has a constraint and could therefore BLOCK with no fallback: **{summary['single_candidate_steps_with_constraints']}**")
    report.append(f"- Unknown candidate references: **{summary['unknown_candidate_refs']}**")
    report.append(f"- Candidate references without tool_io route: **{summary['candidate_refs_missing_io_route']}**")
    report.append(f"- Operations represented by only one unique tool across all workflows: **{summary['operations_with_only_one_unique_tool']}**")
    report.append("")

    report.append("## Highest-priority fallback gaps")
    report.append("")
    if constrained_singletons:
        report.append("| Workflow | Step | Operation | Tool | Why it matters |")
        report.append("|---|---:|---|---|---|")
        for wf, idx, op, name, tool in constrained_singletons:
            report.append(f"| `{wf}` | {idx} | `{op}` | `{tool}` | Constraint can BLOCK the only candidate; no automatic fallback exists. |")
    else:
        report.append("No constrained single-candidate steps were found.")
    report.append("")

    report.append("## All single-candidate steps")
    report.append("")
    if single_candidate_steps:
        report.append("| Workflow | Step | Operation | Tool |")
        report.append("|---|---:|---|---|")
        for wf, idx, op, name, tool in single_candidate_steps:
            report.append(f"| `{wf}` | {idx} | `{op}` | `{tool}` |")
    else:
        report.append("No single-candidate steps were found.")
    report.append("")

    report.append("## Operations with shallow alternative coverage")
    report.append("")
    shallow = [x for x in operation_summary if x["unique_candidate_tools"] <= 2]
    if shallow:
        report.append("| Operation | Unique tools | Tool IDs |")
        report.append("|---|---:|---|")
        for x in shallow:
            report.append(f"| `{x['operation']}` | {x['unique_candidate_tools']} | {x['tool_ids']} |")
    else:
        report.append("All represented operations have at least three unique candidate tools.")
    report.append("")

    report.append("## Structural problems")
    report.append("")
    if not unknown_candidates and not missing_io:
        report.append("No unknown workflow candidates or missing tool I/O routes were detected.")
    else:
        if unknown_candidates:
            report.append("### Unknown workflow candidate IDs")
            for item in unknown_candidates:
                report.append(f"- `{item[0]}` step {item[1]} `{item[2]}` -> `{item[3]}`")
        if missing_io:
            report.append("")
            report.append("### Candidate tools without a tool_io route")
            for item in missing_io:
                report.append(f"- `{item[0]}` step {item[1]} `{item[2]}` -> `{item[3]}`")
    report.append("")
    report.append("## Interpretation")
    report.append("")
    report.append(
        "The most important number for product robustness is not raw tool count but the number of constrained "
        "single-candidate steps. Those are the places where BioFlow can correctly identify that a tool is unsuitable "
        "yet still fail to offer a usable alternative. These should be filled before cosmetic UI work."
    )

    report_path = OUT / "COVERAGE_AUDIT_V1_REPORT.md"
    report_path.write_text("\n".join(report), encoding="utf-8")

    print("=" * 72)
    print("BioFlow Coverage Audit v1")
    print("=" * 72)
    print(f"Workflows: {summary['total_workflows']}")
    print(f"Steps: {summary['total_steps']}")
    print(f"Unique candidate tools: {summary['unique_candidate_tools']}")
    print(f"Constraint coverage: {summary['constraint_coverage_pct']:.2f}%")
    print(f"Single-candidate steps: {summary['single_candidate_steps']} ({summary['single_candidate_steps_pct']:.2f}%)")
    print(f"Constrained singleton fallback risks: {summary['single_candidate_steps_with_constraints']}")
    print(f"Unknown candidate refs: {summary['unknown_candidate_refs']}")
    print(f"Missing tool_io refs: {summary['candidate_refs_missing_io_route']}")
    print(f"Report: {report_path}")

    if unknown_candidates or missing_io:
        print("")
        print("RESULT: FAIL")
        print("Structural coverage errors were detected.")
        return 1

    print("")
    print("RESULT: PASS")
    if constrained_singletons:
        print("Structural integrity passed, but fallback gaps remain. Review the report.")
    else:
        print("Structural integrity passed and no constrained singleton fallback gaps were found.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
