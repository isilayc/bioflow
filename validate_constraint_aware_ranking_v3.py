from __future__ import annotations

from pathlib import Path
import py_compile
import sys

BASE_DIR = Path(__file__).resolve().parent
APP_FILE = BASE_DIR / "app.py"
SCORING_FILE = BASE_DIR / "engine" / "scoring.py"


def fail(message):
    print(f"[FAIL] {message}")
    return False


def ok(message):
    print(f"[PASS] {message}")
    return True


def main():
    print("=" * 72)
    print("BioFlow constraint-aware ranking v3 validator")
    print("=" * 72)

    success = True

    for path in (APP_FILE, SCORING_FILE):
        if not path.exists():
            success &= fail(f"Missing required file: {path.relative_to(BASE_DIR)}")
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            success &= ok(f"Python compile: {path.relative_to(BASE_DIR)}")
        except Exception as exc:
            success &= fail(f"Python compile failed for {path.relative_to(BASE_DIR)}: {exc}")

    if not success:
        print("\nRESULT: FAIL")
        return 1

    sys.path.insert(0, str(BASE_DIR))
    try:
        from engine.scoring import (
            RANKING_VERSION,
            constraint_hard_gate_priority,
            constraint_soft_priority,
            recommendation_sort_key,
        )
    except Exception as exc:
        print(f"[FAIL] Could not import ranking helpers: {exc}")
        print("\nRESULT: FAIL")
        return 1

    success &= ok("Ranking version is 3.0") if RANKING_VERSION == "3.0" else fail(
        f"Unexpected RANKING_VERSION: {RANKING_VERSION!r}"
    )

    expected_hard = {
        "pass": 1,
        "warning": 1,
        "block": 0,
        "needs_input": 1,
        "not_defined": 1,
        None: 1,
    }
    for status, expected in expected_hard.items():
        actual = constraint_hard_gate_priority(status)
        success &= ok(f"Hard gate {status!r} -> {actual}") if actual == expected else fail(
            f"Hard gate {status!r}: expected {expected}, got {actual}"
        )

    expected_soft = {
        "pass": 1,
        "warning": 0,
        "block": 1,
        "needs_input": 1,
        "not_defined": 1,
        None: 1,
    }
    for status, expected in expected_soft.items():
        actual = constraint_soft_priority(status)
        success &= ok(f"Soft priority {status!r} -> {actual}") if actual == expected else fail(
            f"Soft priority {status!r}: expected {expected}, got {actual}"
        )

    def tool(name, fit_priority, total):
        return {
            "name": name,
            "score": {
                "scientific_fit_priority": fit_priority,
                "scientific_fit_label": "curated",
                "total": total,
            },
        }

    def key(item, constraint_status):
        return recommendation_sort_key(
            item,
            operational_enabled=False,
            constraint_status=constraint_status,
        )

    pass_same_fit = tool("pass_same_fit", 3, 70)
    warn_same_fit = tool("warn_same_fit", 3, 99)
    success &= ok("PASS outranks WARNING within the same scientific-fit tier") if (
        key(pass_same_fit, "pass") > key(warn_same_fit, "warning")
    ) else fail("WARNING was not softly demoted inside the same scientific-fit tier")

    better_fit_warning = tool("better_fit_warning", 4, 60)
    lower_fit_pass = tool("lower_fit_pass", 3, 100)
    success &= ok("Scientific-fit tier remains stronger than a soft WARNING") if (
        key(better_fit_warning, "warning") > key(lower_fit_pass, "pass")
    ) else fail("Soft WARNING incorrectly overrode scientific-fit tier")

    blocked_best = tool("blocked_best", 5, 100)
    valid_lower = tool("valid_lower", 1, 1)
    success &= ok("Dataset BLOCK acts as a hard ranking gate") if (
        key(valid_lower, "pass") > key(blocked_best, "block")
    ) else fail("Dataset BLOCK did not act as a hard ranking gate")

    needs_input_high = tool("needs_input_high", 3, 90)
    pass_low = tool("pass_low", 3, 70)
    success &= ok("Missing constraint input is neutral, not a penalty") if (
        key(needs_input_high, "needs_input") > key(pass_low, "pass")
    ) else fail("needs_input was incorrectly penalized")

    undefined_high = tool("undefined_high", 3, 90)
    success &= ok("Undefined constraint coverage is neutral") if (
        key(undefined_high, "not_defined") > key(pass_low, "pass")
    ) else fail("not_defined was incorrectly penalized")

    app_text = APP_FILE.read_text(encoding="utf-8")
    required_app_markers = [
        "def evaluate_step_tool_constraints(",
        "constraint_lookup = {",
        "constraint_hard_gate_priority(",
        "constraint_soft_priority(",
        "Constraint-aware ranking v3 is active.",
        "dataset-specific constraint blocks this branch",
    ]
    for marker in required_app_markers:
        success &= ok(f"app.py marker: {marker}") if marker in app_text else fail(
            f"app.py missing ranking-v3 marker: {marker}"
        )

    ranking_start = app_text.find("def _ranking_signature(\n                tool")
    ranking_end = app_text.find("display_tools = sorted(", ranking_start)
    ranking_text = app_text[ranking_start:ranking_end]
    order = [
        ranking_text.find("dependency_status_priority("),
        ranking_text.find("operational_hard_gate_priority("),
        ranking_text.find("constraint_hard_gate_priority("),
        ranking_text.find("scientific_fit_priority("),
        ranking_text.find("constraint_soft_priority("),
    ]
    success &= ok("Sequential ranking gate order is correct") if (
        all(i >= 0 for i in order) and order == sorted(order)
    ) else fail(f"Unexpected ranking component order: {order}")

    if "advisory for now and do not change" in app_text:
        success &= fail("Old advisory-only constraint caption is still present")
    else:
        success &= ok("Old advisory-only constraint caption removed")

    print("\n" + "=" * 72)
    print("RESULT: PASS" if success else "RESULT: FAIL")
    if success:
        print("Constraint-aware ranking v3 is structurally valid and behavior tests passed.")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
