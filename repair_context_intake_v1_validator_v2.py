from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path.cwd()
VALIDATOR = ROOT / "tests" / "dynamic_route_v1" / "validate_dynamic_route_v1.py"
CONTEXT = ROOT / "engine" / "context_intake.py"
NCBI = ROOT / "services" / "ncbi_reference.py"
CONTEXT_TEST_DIR = ROOT / "tests" / "context_intake_v1"
INSTALLER = ROOT / "apply_context_intake_reference_finder_v1.py"
BACKUPS = ROOT / "backups"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
PYTHON = VENV if VENV.exists() else Path(sys.executable)


def fail(message: str) -> None:
    print("")
    print("=" * 78)
    print("RESULT: FAIL")
    print(message)
    raise SystemExit(1)


def patch_validator(source: str) -> tuple[str, str]:
    if "reference_accession" in source and "get_goal_options" in source:
        # Already likely patched. Leave it alone.
        return source, "already_reference_aware"

    pattern = re.compile(
        r'''get_goal_options\(\s*
            ["']Eukaryotic\ genome["']\s*,\s*
            ["']Illumina["']\s*,\s*
            ["']Single-end["']\s*,?\s*
            \)''',
        re.VERBOSE | re.DOTALL,
    )

    replacement = '''get_goal_options(
        "Eukaryotic genome",
        "Illumina",
        "Single-end",
        reference_context={
            "status": "ncbi_reference",
            "usable_reference": True,
            "reference_accession": "GCF_TEST.1",
        },
    )'''

    updated, count = pattern.subn(
        replacement,
        source,
        count=1,
    )

    if count:
        return updated, "regex"

    # Fallback: inspect Python AST and replace the exact call by source span.
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise RuntimeError(
            f"Dynamic validator is not valid Python: {exc}"
        ) from exc

    target = None

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func
        if not (
            isinstance(func, ast.Name)
            and func.id == "get_goal_options"
        ):
            continue

        constants = []
        for arg in node.args[:3]:
            if isinstance(arg, ast.Constant):
                constants.append(arg.value)
            else:
                constants.append(None)

        if constants == [
            "Eukaryotic genome",
            "Illumina",
            "Single-end",
        ]:
            target = node
            break

    if target is None:
        # Last-resort diagnostic: locate all get_goal_options snippets.
        snippets = []
        lines = source.splitlines()

        for i, line in enumerate(lines):
            if "get_goal_options" in line:
                start = max(0, i - 2)
                end = min(len(lines), i + 12)
                snippets.append(
                    "\n".join(
                        f"{j+1:04d}: {lines[j]}"
                        for j in range(start, end)
                    )
                )

        detail = "\n\n".join(snippets) or "No get_goal_options call found."
        raise RuntimeError(
            "Could not find the Eukaryotic genome / Illumina / Single-end "
            "get_goal_options call.\n\nNearby calls:\n" + detail
        )

    lines = source.splitlines(keepends=True)

    start_line = target.lineno - 1
    end_line = target.end_lineno - 1

    absolute_start = sum(
        len(line)
        for line in lines[:start_line]
    ) + target.col_offset

    absolute_end = sum(
        len(line)
        for line in lines[:end_line]
    ) + target.end_col_offset

    updated = (
        source[:absolute_start]
        + replacement
        + source[absolute_end:]
    )

    return updated, "ast"


def main() -> None:
    print("=" * 78)
    print("OmicsRoute Context Intake v1 - robust validator repair")
    print("=" * 78)

    if not VALIDATOR.exists():
        fail(
            "Dynamic Route v1 validator was not found at:\n"
            f"{VALIDATOR}"
        )

    if not INSTALLER.exists():
        fail(
            "apply_context_intake_reference_finder_v1.py was not found in the "
            "project root. Keep the Context Intake ZIP extracted in the project."
        )

    BACKUPS.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup = (
        BACKUPS
        / f"validate_dynamic_route_v1_before_context_repair2_{STAMP}.py"
    )

    shutil.copy2(
        VALIDATOR,
        backup,
    )

    source = VALIDATOR.read_text(
        encoding="utf-8"
    )

    try:
        updated, method = patch_validator(
            source
        )
    except Exception as exc:
        fail(str(exc))

    VALIDATOR.write_text(
        updated,
        encoding="utf-8"
    )

    print(
        "Dynamic Route validator repair:",
        method
    )

    # Compile the edited validator before touching partial install files.
    compile_result = subprocess.run(
        [
            str(PYTHON),
            "-m",
            "py_compile",
            str(VALIDATOR),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if compile_result.returncode != 0:
        shutil.copy2(
            backup,
            VALIDATOR,
        )

        fail(
            "Validator syntax check failed; original validator restored.\n"
            + (
                compile_result.stderr
                or
                compile_result.stdout
            )
        )

    # Remove only artifacts created by the failed Context Intake installer.
    if CONTEXT.exists():
        CONTEXT.unlink()
        print("Removed partial engine/context_intake.py")

    if NCBI.exists():
        NCBI.unlink()
        print("Removed partial services/ncbi_reference.py")

    if CONTEXT_TEST_DIR.exists():
        shutil.rmtree(
            CONTEXT_TEST_DIR
        )
        print("Removed partial tests/context_intake_v1")

    print("")
    print("Re-running Context Intake + Reference Finder v1...")
    print("")

    result = subprocess.run(
        [
            str(PYTHON),
            str(INSTALLER),
        ],
        cwd=ROOT,
    )

    if result.returncode != 0:
        fail(
            "The installer still failed after repairing the regression test. "
            "Send me the new terminal output."
        )

    print("")
    print("=" * 78)
    print("RESULT: PASS")
    print("Context Intake v1 installed and regression semantics updated.")
    print("")
    print("The old Dynamic Route test now supplies a reference before it")
    print("expects Variant analysis to appear.")
    print("")
    print("Preview:")
    print(
        r'  & ".\.venv\Scripts\python.exe" -m streamlit run app.py'
    )


if __name__ == "__main__":
    main()
