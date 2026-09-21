from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app.py"


def fail(message):
    print("FAIL:", message)
    return False


def main():
    ok = True
    text = APP.read_text(encoding="utf-8")
    tree = ast.parse(text)
    funcs = {
        n.name: n
        for n in tree.body
        if isinstance(n, ast.FunctionDef)
    }

    for name in [
        "get_workflow_required_inputs",
        "show_workflow_overview_and_export",
        "show_workflow_input_requirements",
        "show_workflow_dependency_validation",
    ]:
        if name not in funcs:
            ok = fail(f"Missing function: {name}") and ok

    overview = funcs.get("show_workflow_overview_and_export")
    if overview:
        args = [a.arg for a in overview.args.args]
        if args != ["workflow", "dependency_validation"]:
            ok = fail(f"Unexpected overview args: {args}") and ok

    inputs = funcs.get("show_workflow_input_requirements")
    if inputs:
        args = [a.arg for a in inputs.args.args]
        if args != ["workflow", "dependency_validation"]:
            ok = fail(f"Unexpected input-display args: {args}") and ok

    required_strings = [
        'st.metric("Tool options", len(tool_ids))',
        'st.metric("Required inputs", len(required_inputs))',
        '"✅ Workflow path is technically complete."',
        '"🔗 Technical details"',
        'show_workflow_overview_and_export(\n        workflow,\n        dependency_validation\n    )',
        'show_workflow_input_requirements(\n        workflow,\n        dependency_validation\n    )',
    ]
    for marker in required_strings:
        if marker not in text:
            ok = fail(f"Missing release-polish marker: {marker}") and ok

    if 'st.metric("Candidate tools"' in text:
        ok = fail("Old Candidate tools metric label is still present") and ok

    main_dep = text.rfind("    dependency_validation = (")
    main_overview = text.rfind("    show_workflow_overview_and_export(")
    if main_dep == -1 or main_overview == -1 or main_dep > main_overview:
        ok = fail(
            "Dependency validation must be resolved before workflow overview rendering"
        ) and ok

    print("=" * 72)
    print("BioFlow Release Polish v1.1")
    print("=" * 72)

    if ok:
        print("")
        print("RESULT: PASS")
        print("Release polish v1.1 integration is structurally valid.")
        return 0

    print("")
    print("RESULT: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
