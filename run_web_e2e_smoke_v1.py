from __future__ import annotations

import csv
import json
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


ROOT = Path.cwd()
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_DIR = ROOT / "audit" / "web_e2e_smoke_v1" / STAMP
OUT_DIR.mkdir(parents=True, exist_ok=True)

API_BASE = "http://127.0.0.1:8000"
FRONTEND_BASE = "http://localhost:3000"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "OmicsRoute-Web-E2E-Smoke-v1"})

REFERENCE_CONTEXT = {
    "status": "selected",
    "usable_reference": True,
    "reference_accession": "GCF_000005845.2",
    "reference_name": "Audit placeholder reference",
    "reference_source": "audit",
    "organism_name": "Escherichia coli",
    "tax_id": "562",
}

LOW_COMPUTE_PROFILE = {
    "enabled": True,
    "os": "Windows",
    "ram_gb": 8,
    "cpu_cores": 4,
    "disk_gb": 50,
    "gpu": False,
    "wsl": False,
    "container": False,
    "hpc": False,
    "internet": True,
    "large_databases": False,
    "dataset_scale": "small",
}


def write_csv(path: Path, rows: list[dict[str, Any]]):
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fields = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)

    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def request_json(method: str, url: str, **kwargs):
    response = SESSION.request(method, url, timeout=30, **kwargs)
    content_type = response.headers.get("content-type", "")
    payload = None

    if "application/json" in content_type:
        try:
            payload = response.json()
        except Exception:
            payload = None

    return response, payload


def get_first_list(payload: Any, preferred_keys=()):
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in preferred_keys:
            value = payload.get(key)
            if isinstance(value, list):
                return value

        list_values = [
            value
            for value in payload.values()
            if isinstance(value, list)
        ]
        if len(list_values) == 1:
            return list_values[0]

    return []


def item_value(item):
    if isinstance(item, str):
        return item

    if isinstance(item, dict):
        for key in (
            "id",
            "value",
            "name",
            "label",
            "sample_type",
            "sequencing",
            "read_type",
            "goal",
        ):
            value = item.get(key)
            if isinstance(value, str) and value:
                return value

    return str(item)


def extract_workflow(inspect_payload):
    if not isinstance(inspect_payload, dict):
        return None

    workflow = inspect_payload.get("workflow")
    if isinstance(workflow, dict):
        return workflow

    # Older API variants may directly return the built workflow.
    if isinstance(inspect_payload.get("steps"), list):
        return inspect_payload

    return None


def flatten_tool_assessments(value):
    found = []

    def walk(obj, path="root"):
        if isinstance(obj, dict):
            if "operational_fit" in obj and isinstance(obj.get("operational_fit"), dict):
                found.append(
                    {
                        "path": path,
                        "status": obj["operational_fit"].get("status"),
                    }
                )
            assessment = obj.get("_assessment")
            if isinstance(assessment, dict):
                operational = assessment.get("operational")
                if isinstance(operational, dict):
                    found.append(
                        {
                            "path": path + "._assessment",
                            "status": operational.get("status"),
                        }
                    )

            for key, child in obj.items():
                walk(child, f"{path}.{key}")

        elif isinstance(obj, list):
            for index, child in enumerate(obj):
                walk(child, f"{path}[{index}]")

    walk(value)
    return found


def main():
    checks = []
    failures = []
    route_rows = []

    print("=" * 92)
    print("OmicsRoute — Web End-to-End Smoke Test v1")
    print("=" * 92)
    print("API:", API_BASE)
    print("Frontend:", FRONTEND_BASE)
    print("Output:", OUT_DIR)
    print("")

    # ------------------------------------------------------------------
    # Basic connectivity
    # ------------------------------------------------------------------
    try:
        front = SESSION.get(FRONTEND_BASE, timeout=20)
        frontend_ok = front.status_code == 200
        checks.append(
            {
                "check": "frontend_http",
                "status": "PASS" if frontend_ok else "FAIL",
                "detail": f"HTTP {front.status_code}",
            }
        )

        if not frontend_ok:
            failures.append(
                {
                    "severity": "CRITICAL",
                    "category": "frontend_unreachable",
                    "detail": f"{FRONTEND_BASE} returned HTTP {front.status_code}",
                }
            )
    except Exception as exc:
        front = None
        frontend_ok = False
        checks.append(
            {
                "check": "frontend_http",
                "status": "FAIL",
                "detail": str(exc),
            }
        )
        failures.append(
            {
                "severity": "CRITICAL",
                "category": "frontend_unreachable",
                "detail": str(exc),
            }
        )

    try:
        health_response, health_payload = request_json(
            "GET",
            f"{API_BASE}/health",
        )
        api_ok = health_response.status_code == 200
        checks.append(
            {
                "check": "api_health",
                "status": "PASS" if api_ok else "FAIL",
                "detail": (
                    json.dumps(health_payload, ensure_ascii=False)
                    if health_payload is not None
                    else f"HTTP {health_response.status_code}"
                ),
            }
        )

        if not api_ok:
            failures.append(
                {
                    "severity": "CRITICAL",
                    "category": "api_unreachable",
                    "detail": f"/health returned HTTP {health_response.status_code}",
                }
            )
    except Exception as exc:
        api_ok = False
        checks.append(
            {
                "check": "api_health",
                "status": "FAIL",
                "detail": str(exc),
            }
        )
        failures.append(
            {
                "severity": "CRITICAL",
                "category": "api_unreachable",
                "detail": str(exc),
            }
        )

    if not api_ok:
        write_csv(OUT_DIR / "checks.csv", checks)
        write_csv(OUT_DIR / "failures.csv", failures)
        print("API is not available. Start FastAPI first, then rerun this test.")
        print("RESULT: FAIL")
        raise SystemExit(1)

    # ------------------------------------------------------------------
    # OpenAPI contract
    # ------------------------------------------------------------------
    openapi_response, openapi = request_json(
        "GET",
        f"{API_BASE}/openapi.json",
    )

    paths = (
        openapi.get("paths", {})
        if isinstance(openapi, dict)
        else {}
    )

    required_endpoints = [
        "/health",
        "/v1/sample-types",
        "/v1/data-states",
        "/v1/sequencing-options",
        "/v1/read-types",
        "/v1/goals",
        "/v1/strategies",
        "/v1/workflow",
        "/v1/workflow/inspect",
        "/v1/reference-guidance",
        "/v1/catalog/coverage",
    ]

    optional_external_endpoints = [
        "/v1/reference/taxa",
        "/v1/reference/assemblies",
        "/v1/tool-evidence",
        "/v1/biotools",
        "/v1/discovery",
    ]

    for endpoint in required_endpoints:
        present = endpoint in paths
        checks.append(
            {
                "check": f"openapi:{endpoint}",
                "status": "PASS" if present else "FAIL",
                "detail": "present" if present else "missing",
            }
        )
        if not present:
            failures.append(
                {
                    "severity": "CRITICAL",
                    "category": "missing_api_endpoint",
                    "detail": endpoint,
                }
            )

    for endpoint in optional_external_endpoints:
        checks.append(
            {
                "check": f"openapi_optional:{endpoint}",
                "status": "PASS" if endpoint in paths else "WARN",
                "detail": "present" if endpoint in paths else "not exposed",
            }
        )

    # ------------------------------------------------------------------
    # Frontend static markers
    # ------------------------------------------------------------------
    if front is not None and front.status_code == 200:
        html = front.text
        marker_groups = {
            "brand": ["OmicsRoute"],
            "analysis_intake": [
                "Describe your analysis",
                "Sample type",
            ],
            "compute_profile": [
                "Computer / compute environment",
                "Compute environment",
            ],
        }

        for name, alternatives in marker_groups.items():
            found = any(marker in html for marker in alternatives)
            checks.append(
                {
                    "check": f"frontend_marker:{name}",
                    "status": "PASS" if found else "WARN",
                    "detail": (
                        " | ".join(alternatives)
                        if not found
                        else "visible in initial HTML"
                    ),
                }
            )

    # ------------------------------------------------------------------
    # Local coverage endpoint
    # ------------------------------------------------------------------
    try:
        coverage_response, coverage_payload = request_json(
            "GET",
            f"{API_BASE}/v1/catalog/coverage",
            params={"validate_dependencies": "false"},
        )
        coverage_ok = coverage_response.status_code == 200
    except Exception as exc:
        coverage_ok = False
        coverage_payload = None
        coverage_response = None
        failures.append(
            {
                "severity": "HIGH",
                "category": "coverage_endpoint_error",
                "detail": str(exc),
            }
        )

    checks.append(
        {
            "check": "catalog_coverage",
            "status": "PASS" if coverage_ok else "FAIL",
            "detail": (
                f"HTTP {coverage_response.status_code}"
                if coverage_response is not None
                else "request error"
            ),
        }
    )

    # ------------------------------------------------------------------
    # Sample-type → platform → read layout → goals → strategies → inspect
    # ------------------------------------------------------------------
    sample_response, sample_payload = request_json(
        "GET",
        f"{API_BASE}/v1/sample-types",
    )

    sample_items = get_first_list(
        sample_payload,
        ("sample_types", "items", "values"),
    )
    sample_types = [item_value(item) for item in sample_items]

    if sample_response.status_code != 200 or not sample_types:
        failures.append(
            {
                "severity": "CRITICAL",
                "category": "sample_type_contract",
                "detail": (
                    f"HTTP {sample_response.status_code}; "
                    f"payload={sample_payload}"
                ),
            }
        )

    total_contexts = 0
    total_goals = 0
    total_strategies = 0
    inspected = 0

    for sample_type in sample_types:
        ds_response, ds_payload = request_json(
            "GET",
            f"{API_BASE}/v1/data-states",
            params={"sample_type": sample_type},
        )

        data_states = get_first_list(
            ds_payload,
            ("data_states", "states", "items", "values"),
        )
        raw_state = "raw_reads"

        # If the API returns explicit state IDs, prefer its raw state.
        for item in data_states:
            if isinstance(item, dict):
                candidate = item.get("id")
                if candidate == "raw_reads":
                    raw_state = candidate
                    break

        seq_response, seq_payload = request_json(
            "GET",
            f"{API_BASE}/v1/sequencing-options",
            params={"sample_type": sample_type},
        )

        sequencing_items = get_first_list(
            seq_payload,
            ("sequencing_options", "sequencing", "items", "values"),
        )
        sequencing_options = [
            item_value(item)
            for item in sequencing_items
        ]

        if seq_response.status_code != 200 or not sequencing_options:
            failures.append(
                {
                    "severity": "CRITICAL",
                    "category": "sequencing_options_contract",
                    "sample_type": sample_type,
                    "detail": (
                        f"HTTP {seq_response.status_code}; payload={seq_payload}"
                    ),
                }
            )
            continue

        for sequencing in sequencing_options:
            read_response, read_payload = request_json(
                "GET",
                f"{API_BASE}/v1/read-types",
                params={
                    "sample_type": sample_type,
                    "sequencing": sequencing,
                },
            )

            read_items = get_first_list(
                read_payload,
                ("read_types", "items", "values"),
            )
            read_types = [
                item_value(item)
                for item in read_items
            ]

            if read_response.status_code != 200 or not read_types:
                failures.append(
                    {
                        "severity": "CRITICAL",
                        "category": "read_types_contract",
                        "sample_type": sample_type,
                        "sequencing": sequencing,
                        "detail": (
                            f"HTTP {read_response.status_code}; "
                            f"payload={read_payload}"
                        ),
                    }
                )
                continue

            for read_type in read_types:
                total_contexts += 1

                base_payload = {
                    "sample_type": sample_type,
                    "sequencing": sequencing,
                    "read_type": read_type,
                    "data_state": raw_state,
                    "reference_context": REFERENCE_CONTEXT,
                }

                goals_response, goals_payload = request_json(
                    "POST",
                    f"{API_BASE}/v1/goals",
                    json=base_payload,
                )

                goal_items = get_first_list(
                    goals_payload,
                    ("goals", "items", "values"),
                )

                goals = []
                for item in goal_items:
                    if isinstance(item, dict):
                        value = (
                            item.get("goal")
                            or item.get("name")
                            or item.get("id")
                            or item.get("value")
                        )
                        selectable = item.get("selectable")
                        if selectable is False:
                            continue
                    else:
                        value = item

                    if value:
                        goals.append(str(value))

                if goals_response.status_code != 200:
                    failures.append(
                        {
                            "severity": "CRITICAL",
                            "category": "goals_contract",
                            "sample_type": sample_type,
                            "sequencing": sequencing,
                            "read_type": read_type,
                            "detail": (
                                f"HTTP {goals_response.status_code}; "
                                f"payload={goals_payload}"
                            ),
                        }
                    )
                    continue

                for goal in goals:
                    total_goals += 1
                    strategy_request = {
                        **base_payload,
                        "goal": goal,
                    }

                    strategies_response, strategies_payload = request_json(
                        "POST",
                        f"{API_BASE}/v1/strategies",
                        json=strategy_request,
                    )

                    strategies = get_first_list(
                        strategies_payload,
                        ("strategies", "items", "values"),
                    )

                    if strategies_response.status_code != 200 or not strategies:
                        failures.append(
                            {
                                "severity": "CRITICAL",
                                "category": "strategies_contract",
                                "sample_type": sample_type,
                                "sequencing": sequencing,
                                "read_type": read_type,
                                "goal": goal,
                                "detail": (
                                    f"HTTP {strategies_response.status_code}; "
                                    f"payload={strategies_payload}"
                                ),
                            }
                        )
                        continue

                    total_strategies += len(strategies)

                    for strategy in strategies:
                        if not isinstance(strategy, dict):
                            strategy_id = str(strategy)
                            strategy_name = strategy_id
                        else:
                            strategy_id = (
                                strategy.get("id")
                                or strategy.get("workflow_id")
                                or ""
                            )
                            strategy_name = (
                                strategy.get("name")
                                or strategy_id
                            )

                        inspect_request = {
                            **strategy_request,
                            "workflow_id": strategy_id,
                        }

                        inspect_response, inspect_payload = request_json(
                            "POST",
                            f"{API_BASE}/v1/workflow/inspect",
                            json=inspect_request,
                        )

                        workflow = extract_workflow(inspect_payload)
                        inspect_ok = (
                            inspect_response.status_code == 200
                            and isinstance(inspect_payload, dict)
                            and isinstance(workflow, dict)
                        )

                        exports_ok = False
                        dependency_present = False
                        tool_assessment_present = False

                        if isinstance(inspect_payload, dict):
                            exports = inspect_payload.get("exports")
                            exports_ok = isinstance(exports, dict) and bool(exports)

                            dependency = inspect_payload.get("dependency")
                            dependency_present = isinstance(dependency, dict)

                            assessments = flatten_tool_assessments(inspect_payload)
                            tool_assessment_present = bool(assessments)

                        status = "PASS"
                        detail = ""

                        if not inspect_ok:
                            status = "FAIL"
                            detail = (
                                f"HTTP {inspect_response.status_code}; "
                                f"payload={inspect_payload}"
                            )
                            failures.append(
                                {
                                    "severity": "CRITICAL",
                                    "category": "workflow_inspect_failure",
                                    "sample_type": sample_type,
                                    "sequencing": sequencing,
                                    "read_type": read_type,
                                    "goal": goal,
                                    "strategy_id": strategy_id,
                                    "detail": detail[:4000],
                                }
                            )
                        else:
                            inspected += 1

                            if not exports_ok:
                                failures.append(
                                    {
                                        "severity": "HIGH",
                                        "category": "missing_exports",
                                        "sample_type": sample_type,
                                        "sequencing": sequencing,
                                        "read_type": read_type,
                                        "goal": goal,
                                        "strategy_id": strategy_id,
                                        "detail": "workflow/inspect response has no populated exports object.",
                                    }
                                )

                            if not dependency_present:
                                failures.append(
                                    {
                                        "severity": "HIGH",
                                        "category": "missing_dependency_report",
                                        "sample_type": sample_type,
                                        "sequencing": sequencing,
                                        "read_type": read_type,
                                        "goal": goal,
                                        "strategy_id": strategy_id,
                                        "detail": "workflow/inspect response has no dependency object.",
                                    }
                                )

                            if not tool_assessment_present:
                                failures.append(
                                    {
                                        "severity": "HIGH",
                                        "category": "missing_tool_assessment",
                                        "sample_type": sample_type,
                                        "sequencing": sequencing,
                                        "read_type": read_type,
                                        "goal": goal,
                                        "strategy_id": strategy_id,
                                        "detail": "No operational/tool assessment found in workflow/inspect response.",
                                    }
                                )

                        route_rows.append(
                            {
                                "sample_type": sample_type,
                                "sequencing": sequencing,
                                "read_type": read_type,
                                "goal": goal,
                                "strategy_id": strategy_id,
                                "strategy_name": strategy_name,
                                "inspect_http": inspect_response.status_code,
                                "inspect_ok": inspect_ok,
                                "exports_present": exports_ok,
                                "dependency_present": dependency_present,
                                "tool_assessment_present": tool_assessment_present,
                                "status": status,
                            }
                        )

    # ------------------------------------------------------------------
    # Compute-profile integration smoke
    # ------------------------------------------------------------------
    compute_tested = False
    compute_profile_accepted = False
    operational_assessment_count = 0

    representative = next(
        (
            row
            for row in route_rows
            if row.get("inspect_ok")
        ),
        None,
    )

    if representative:
        compute_tested = True
        payload = {
            "sample_type": representative["sample_type"],
            "sequencing": representative["sequencing"],
            "read_type": representative["read_type"],
            "goal": representative["goal"],
            "data_state": "raw_reads",
            "reference_context": REFERENCE_CONTEXT,
            "workflow_id": representative["strategy_id"],
            "compute_profile": LOW_COMPUTE_PROFILE,
        }

        cp_response, cp_payload = request_json(
            "POST",
            f"{API_BASE}/v1/workflow/inspect",
            json=payload,
        )

        if cp_response.status_code == 200:
            compute_profile_accepted = True
            operational_assessment_count = len(
                flatten_tool_assessments(cp_payload)
            )
            checks.append(
                {
                    "check": "compute_profile_inspect",
                    "status": (
                        "PASS"
                        if operational_assessment_count > 0
                        else "WARN"
                    ),
                    "detail": (
                        f"HTTP 200; operational assessments="
                        f"{operational_assessment_count}"
                    ),
                }
            )
        else:
            checks.append(
                {
                    "check": "compute_profile_inspect",
                    "status": "FAIL",
                    "detail": (
                        f"HTTP {cp_response.status_code}; "
                        f"payload={cp_payload}"
                    ),
                }
            )
            failures.append(
                {
                    "severity": "HIGH",
                    "category": "compute_profile_contract",
                    "detail": (
                        f"Compute-profile workflow inspection returned "
                        f"HTTP {cp_response.status_code}: {cp_payload}"
                    ),
                }
            )

    # ------------------------------------------------------------------
    # Local reference-guidance endpoint
    # ------------------------------------------------------------------
    try:
        ref_response, ref_payload = request_json(
            "GET",
            f"{API_BASE}/v1/reference-guidance",
        )
        ref_ok = ref_response.status_code == 200
    except Exception as exc:
        ref_ok = False
        ref_payload = None
        failures.append(
            {
                "severity": "HIGH",
                "category": "reference_guidance_error",
                "detail": str(exc),
            }
        )

    checks.append(
        {
            "check": "reference_guidance",
            "status": "PASS" if ref_ok else "FAIL",
            "detail": "local endpoint only; no external NCBI request required",
        }
    )

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------
    write_csv(OUT_DIR / "checks.csv", checks)
    write_csv(OUT_DIR / "route_e2e.csv", route_rows)
    write_csv(OUT_DIR / "failures.csv", failures)

    severity_counts = Counter(
        row.get("severity", "UNKNOWN")
        for row in failures
    )
    category_counts = Counter(
        row.get("category", "unknown")
        for row in failures
    )

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "frontend_ok": frontend_ok,
        "api_ok": api_ok,
        "sample_types": len(sample_types),
        "raw_contexts": total_contexts,
        "goals": total_goals,
        "strategies": total_strategies,
        "workflow_inspections_passed": inspected,
        "failures": len(failures),
        "critical": severity_counts.get("CRITICAL", 0),
        "high": severity_counts.get("HIGH", 0),
        "compute_profile_tested": compute_tested,
        "compute_profile_accepted": compute_profile_accepted,
        "operational_assessment_count": operational_assessment_count,
        "output_directory": str(OUT_DIR),
    }

    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    report = [
        "# OmicsRoute Web End-to-End Smoke Test v1",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Executive summary",
        "",
        f"- Frontend reachable: **{frontend_ok}**",
        f"- API reachable: **{api_ok}**",
        f"- Sample types: **{len(sample_types)}**",
        f"- Raw contexts exercised: **{total_contexts}**",
        f"- Goals exercised: **{total_goals}**",
        f"- Strategies exercised: **{total_strategies}**",
        f"- Successful workflow/inspect calls: **{inspected}**",
        f"- Failures recorded: **{len(failures)}**",
        f"- Critical: **{severity_counts.get('CRITICAL', 0)}**",
        f"- High: **{severity_counts.get('HIGH', 0)}**",
        "",
        "## Compute profile",
        "",
        f"- Test attempted: **{compute_tested}**",
        f"- Payload accepted: **{compute_profile_accepted}**",
        f"- Operational assessments found: **{operational_assessment_count}**",
        "",
        "## Failure categories",
        "",
    ]

    if category_counts:
        for category, count in category_counts.most_common():
            report.append(f"- **{category}**: {count}")
    else:
        report.append("- None")

    report.extend(
        [
            "",
            "## Notes",
            "",
            "This is an integration smoke test, not a browser visual-regression test. "
            "It verifies that the frontend is reachable and then exercises the same API "
            "chain used by the web UI: sample type → sequencing → read layout → goals → "
            "strategies → workflow inspection.",
            "",
            "External live services such as NCBI, OpenAlex, PubMed and bio.tools are not "
            "treated as release blockers here because temporary network/API outages should "
            "not make the local OmicsRoute application fail release validation.",
            "",
            "## Files",
            "",
            "- `route_e2e.csv` — every strategy exercised through `/v1/workflow/inspect`",
            "- `failures.csv` — actionable API/frontend integration failures",
            "- `checks.csv` — endpoint and frontend checks",
            "- `summary.json` — machine-readable totals",
        ]
    )

    (OUT_DIR / "REPORT.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    print("Frontend:", "PASS" if frontend_ok else "FAIL")
    print("API:", "PASS" if api_ok else "FAIL")
    print("Sample types:", len(sample_types))
    print("Raw contexts:", total_contexts)
    print("Goals:", total_goals)
    print("Strategies:", total_strategies)
    print("Workflow inspections passed:", inspected)
    print("Failures:", len(failures))
    print("  CRITICAL:", severity_counts.get("CRITICAL", 0))
    print("  HIGH:", severity_counts.get("HIGH", 0))
    print("Compute profile accepted:", compute_profile_accepted)
    print("Operational assessments:", operational_assessment_count)
    print("")
    print("Report:", OUT_DIR / "REPORT.md")
    print("Failures:", OUT_DIR / "failures.csv")
    print("")
    print("=" * 92)

    if severity_counts.get("CRITICAL", 0) == 0 and severity_counts.get("HIGH", 0) == 0:
        print("RESULT: CLEAN")
    else:
        print("RESULT: ISSUES FOUND")

    print("=" * 92)


if __name__ == "__main__":
    main()
