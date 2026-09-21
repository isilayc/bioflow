from __future__ import annotations

from pathlib import Path
import csv
import json
import subprocess
import sys
from datetime import datetime

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Activate the BioFlow virtual environment first.")
    raise SystemExit(2)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CASES_FILE = SCRIPT_DIR / "benchmark_cases.yaml"
RESULTS_DIR = SCRIPT_DIR / "results"


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


def step_candidates(step: dict) -> list[str]:
    candidates = step.get("candidates")
    if candidates:
        return [str(x) for x in candidates if x]
    out = []
    preferred = step.get("preferred")
    if preferred:
        out.append(str(preferred))
    out.extend(str(x) for x in (step.get("alternatives") or []) if x)
    # preserve order
    return list(dict.fromkeys(out))


def context_value_matches(actual, expected) -> bool:
    if isinstance(actual, list):
        return expected in actual
    return actual == expected


def workflow_context_matches(workflow: dict, expected: dict) -> bool:
    actual = workflow.get("context") or {}
    return all(context_value_matches(actual.get(k), v) for k, v in expected.items())


def matching_workflow_ids(workflows: dict, expected_context: dict) -> list[str]:
    return [wid for wid, wf in workflows.items() if workflow_context_matches(wf, expected_context)]


def result(check_id, case_id, status, message, severity="hard"):
    return {
        "case_id": case_id,
        "check_id": check_id,
        "status": status,
        "severity": severity,
        "message": message,
    }


def validate_case(case: dict, workflows: dict, tools: dict):
    out = []
    cid = case["id"]
    wid = case["workflow_id"]
    wf = workflows.get(wid)
    if wf is None:
        out.append(result("workflow_exists", cid, "FAIL", f"Workflow {wid!r} is missing."))
        return out
    out.append(result("workflow_exists", cid, "PASS", f"Workflow {wid!r} exists."))

    expected_context = case.get("context") or {}
    if workflow_context_matches(wf, expected_context):
        out.append(result("context_match", cid, "PASS", "Workflow context matches the benchmark scenario."))
    else:
        out.append(result("context_match", cid, "FAIL", f"Workflow context does not match expected context: {expected_context!r}."))

    matching = matching_workflow_ids(workflows, expected_context)
    if wid in matching:
        out.append(result("context_resolves_target", cid, "PASS", f"Selected context resolves to benchmark workflow {wid}."))
    else:
        out.append(result("context_resolves_target", cid, "FAIL", f"Selected context does not resolve to {wid}."))

    minimum_strategies = int(case.get("context_strategy_minimum", 1) or 1)
    if len(matching) >= minimum_strategies:
        out.append(result("strategy_coverage", cid, "PASS", f"Context exposes {len(matching)} workflow strategy/strategies (minimum {minimum_strategies}).", severity="soft"))
    else:
        out.append(result("strategy_coverage", cid, "WARN", f"Context exposes only {len(matching)} workflow strategy/strategies; benchmark expects at least {minimum_strategies}.", severity="soft"))

    steps = wf.get("steps") or []
    operations = [step.get("operation") for step in steps]

    for op in case.get("required_operations") or []:
        if op in operations:
            out.append(result(f"required_operation:{op}", cid, "PASS", f"Required stage {op!r} is present."))
        else:
            out.append(result(f"required_operation:{op}", cid, "FAIL", f"Required stage {op!r} is missing."))

    for op in case.get("forbidden_operations") or []:
        if op not in operations:
            out.append(result(f"forbidden_operation:{op}", cid, "PASS", f"Unrelated stage {op!r} is absent."))
        else:
            out.append(result(f"forbidden_operation:{op}", cid, "FAIL", f"Unrelated stage {op!r} leaked into the workflow."))

    by_op = {}
    for step in steps:
        op = step.get("operation")
        if op and op not in by_op:
            by_op[op] = step

    for op, rule in (case.get("key_steps") or {}).items():
        step = by_op.get(op)
        if step is None:
            out.append(result(f"key_step:{op}", cid, "FAIL", f"Key stage {op!r} is missing."))
            continue
        candidates = step_candidates(step)
        accepted = set(rule.get("accepted_any") or [])
        overlap = [x for x in candidates if x in accepted]
        if overlap:
            out.append(result(f"accepted_tool:{op}", cid, "PASS", f"Stage {op!r} contains accepted candidate(s): {', '.join(overlap)}."))
        else:
            out.append(result(f"accepted_tool:{op}", cid, "FAIL", f"Stage {op!r} has no accepted candidate. Candidates: {candidates}."))

        min_candidates = int(rule.get("min_candidates", 1) or 1)
        if len(candidates) >= min_candidates:
            out.append(result(f"candidate_redundancy:{op}", cid, "PASS", f"Stage {op!r} has {len(candidates)} candidate(s), meeting minimum {min_candidates}."))
        else:
            out.append(result(f"candidate_redundancy:{op}", cid, "FAIL", f"Stage {op!r} has only {len(candidates)} candidate(s); minimum is {min_candidates}."))

        required_any_fallback = set(rule.get("required_any_fallback") or [])
        if required_any_fallback:
            fallback = [x for x in candidates if x in required_any_fallback]
            if fallback:
                out.append(result(f"fallback:{op}", cid, "PASS", f"Stage {op!r} has fallback candidate(s): {', '.join(fallback)}."))
            else:
                out.append(result(f"fallback:{op}", cid, "FAIL", f"Stage {op!r} lacks required fallback candidates from {sorted(required_any_fallback)}."))

        expected_mode = rule.get("mode")
        if expected_mode:
            actual_mode = str(step.get("mode", "sequential") or "sequential").strip().lower()
            if actual_mode == expected_mode:
                out.append(result(f"step_mode:{op}", cid, "PASS", f"Stage {op!r} uses expected mode {expected_mode!r}."))
            else:
                out.append(result(f"step_mode:{op}", cid, "FAIL", f"Stage {op!r} mode is {actual_mode!r}; expected {expected_mode!r}."))

        for tid in candidates:
            tool = tools.get(tid)
            if tool is None:
                out.append(result(f"tool_exists:{op}:{tid}", cid, "FAIL", f"Candidate tool {tid!r} is missing from tools.yaml."))
            elif op not in (tool.get("operations") or []):
                out.append(result(f"tool_operation:{op}:{tid}", cid, "FAIL", f"Tool {tid!r} does not declare operation {op!r}."))

    return out


def global_audit(workflows: dict, tools: dict, tool_io: dict):
    out = []
    missing_tools = []
    mismatched_ops = []
    missing_io = []
    duplicates = []
    total_candidates = 0
    for wid, wf in workflows.items():
        for step_index, step in enumerate(wf.get("steps") or [], start=1):
            op = step.get("operation")
            candidates = step_candidates(step)
            total_candidates += len(candidates)
            if len(candidates) != len(set(candidates)):
                duplicates.append((wid, step_index, op, candidates))
            for tid in candidates:
                tool = tools.get(tid)
                if tool is None:
                    missing_tools.append((wid, step_index, op, tid))
                    continue
                if op not in (tool.get("operations") or []):
                    mismatched_ops.append((wid, step_index, op, tid))
                if tid not in tool_io:
                    missing_io.append((wid, step_index, op, tid))
    checks = [
        ("global:tool_registry", missing_tools, "workflow candidate(s) missing from tools.yaml"),
        ("global:operation_contract", mismatched_ops, "workflow candidate(s) do not declare their workflow operation"),
        ("global:tool_io", missing_io, "workflow candidate(s) missing from tool_io.yaml"),
        ("global:duplicate_candidates", duplicates, "workflow step(s) contain duplicate candidate IDs"),
    ]
    for check_id, problems, label in checks:
        if problems:
            preview = "; ".join(map(str, problems[:5]))
            out.append(result(check_id, "GLOBAL", "FAIL", f"{len(problems)} {label}. First items: {preview}"))
        else:
            out.append(result(check_id, "GLOBAL", "PASS", f"No {label}. Audited {total_candidates} workflow candidate references."))
    return out


def run_regression_validators():
    known = [
        "validate_scoring_v2.py",
        "validate_constraints.py",
        "validate_constraint_coverage_v1.py",
        "validate_constraint_aware_ranking_v3.py",
        "validate_mag_taxonomy_fallback_v1.py",
    ]
    results = []
    for name in known:
        path = PROJECT_ROOT / name
        if not path.exists():
            results.append({"name": name, "status": "SKIP", "returncode": None, "tail": "Validator not present in project root."})
            continue
        try:
            proc = subprocess.run([sys.executable, str(path)], cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=60)
            combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
            tail = "\n".join(combined.strip().splitlines()[-8:])
            results.append({"name": name, "status": "PASS" if proc.returncode == 0 else "FAIL", "returncode": proc.returncode, "tail": tail})
        except Exception as exc:
            results.append({"name": name, "status": "FAIL", "returncode": None, "tail": f"{type(exc).__name__}: {exc}"})
    return results


def main():
    required = [DATA_DIR/"workflows.yaml", DATA_DIR/"tools.yaml", DATA_DIR/"tool_io.yaml", CASES_FILE]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("RESULT: FAIL")
        print("Missing required files:")
        for item in missing:
            print(" -", item)
        return 1

    workflows = load_yaml(DATA_DIR/"workflows.yaml")
    tools = load_yaml(DATA_DIR/"tools.yaml")
    tool_io = load_yaml(DATA_DIR/"tool_io.yaml")
    spec = load_yaml(CASES_FILE)

    rows = []
    for case in spec.get("cases") or []:
        rows.extend(validate_case(case, workflows, tools))
    rows.extend(global_audit(workflows, tools, tool_io))

    hard_fails = [r for r in rows if r["status"] == "FAIL" and r["severity"] == "hard"]
    warnings = [r for r in rows if r["status"] == "WARN"]
    passes = [r for r in rows if r["status"] == "PASS"]
    hard_total = sum(1 for r in rows if r["severity"] == "hard")
    hard_passes = sum(1 for r in rows if r["severity"] == "hard" and r["status"] == "PASS")
    score = 100.0 * hard_passes / hard_total if hard_total else 0.0

    regression = run_regression_validators()
    regression_fails = [x for x in regression if x["status"] == "FAIL"]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    summary = {
        "benchmark": spec.get("benchmark_name"),
        "timestamp": timestamp,
        "cases": len(spec.get("cases") or []),
        "hard_checks": hard_total,
        "hard_passes": hard_passes,
        "hard_failures": len(hard_fails),
        "warnings": len(warnings),
        "score_percent": round(score, 2),
        "regression_validator_failures": len(regression_fails),
        "overall_status": "PASS" if not hard_fails and not regression_fails else "FAIL",
    }

    with (RESULTS_DIR/"BENCHMARK_V1_RESULTS.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["case_id","check_id","status","severity","message"])
        writer.writeheader(); writer.writerows(rows)

    with (RESULTS_DIR/"BENCHMARK_V1_RESULTS.json").open("w", encoding="utf-8") as handle:
        json.dump({"summary": summary, "checks": rows, "regression_validators": regression}, handle, indent=2, ensure_ascii=False)

    lines = [
        "# BioFlow Scientific Recommendation Benchmark v1",
        "",
        f"Generated: {timestamp}",
        "",
        "## Summary",
        "",
        f"- Overall status: **{summary['overall_status']}**",
        f"- Curated scenarios: **{summary['cases']}**",
        f"- Hard benchmark score: **{summary['score_percent']:.2f}%** ({hard_passes}/{hard_total})",
        f"- Hard failures: **{len(hard_fails)}**",
        f"- Soft warnings: **{len(warnings)}**",
        f"- Regression validator failures: **{len(regression_fails)}**",
        "",
        "This v1 benchmark is a curated internal scientific-content validation panel. It is useful for regression testing and manuscript methods development, but it is not yet an independent external expert benchmark.",
        "",
        "## Scenario results",
        "",
    ]
    for case in spec.get("cases") or []:
        cid = case["id"]
        case_rows = [r for r in rows if r["case_id"] == cid]
        bad = [r for r in case_rows if r["status"] == "FAIL"]
        warn = [r for r in case_rows if r["status"] == "WARN"]
        status = "PASS" if not bad else "FAIL"
        lines += [f"### {case.get('title', cid)} — {status}", "", f"Workflow: `{case['workflow_id']}`", ""]
        for r in bad + warn:
            lines.append(f"- **{r['status']}** `{r['check_id']}` — {r['message']}")
        if not bad and not warn:
            lines.append("- All benchmark checks passed.")
        lines.append("")

    lines += ["## Global registry/contract audit", ""]
    for r in [x for x in rows if x["case_id"] == "GLOBAL"]:
        lines.append(f"- **{r['status']}** `{r['check_id']}` — {r['message']}")
    lines += ["", "## Existing regression validators", ""]
    for item in regression:
        lines.append(f"### {item['name']} — {item['status']}")
        lines.append("")
        if item["tail"]:
            lines.append("```text")
            lines.append(item["tail"])
            lines.append("```")
        lines.append("")
    (RESULTS_DIR/"BENCHMARK_V1_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    print("="*72)
    print("BioFlow Scientific Recommendation Benchmark v1")
    print("="*72)
    print(f"Scenarios: {summary['cases']}")
    print(f"Hard benchmark score: {summary['score_percent']:.2f}% ({hard_passes}/{hard_total})")
    print(f"Hard failures: {len(hard_fails)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Regression validator failures: {len(regression_fails)}")
    print(f"Report: {RESULTS_DIR/'BENCHMARK_V1_REPORT.md'}")
    print()
    if hard_fails:
        print("Hard failures:")
        for r in hard_fails[:20]:
            print(f" - [{r['case_id']}] {r['check_id']}: {r['message']}")
        if len(hard_fails) > 20:
            print(f" ... and {len(hard_fails)-20} more")
        print()
    if regression_fails:
        print("Regression validator failures:")
        for item in regression_fails:
            print(f" - {item['name']}")
        print()
    print(f"RESULT: {summary['overall_status']}")
    if summary["overall_status"] == "PASS":
        print("Scientific recommendation benchmark v1 passed.")
    else:
        print("Review tests/benchmark_v1/results/BENCHMARK_V1_REPORT.md for details.")
    return 0 if summary["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
