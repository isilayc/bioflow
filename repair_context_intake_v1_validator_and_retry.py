from __future__ import annotations

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


def main() -> None:
    print("=" * 78)
    print("OmicsRoute Context Intake v1 - validator compatibility repair")
    print("=" * 78)

    if not VALIDATOR.exists():
        fail("Dynamic Route v1 validator was not found.")

    if not INSTALLER.exists():
        fail(
            "apply_context_intake_reference_finder_v1.py was not found in the "
            "project root. Extract the v1 ZIP there first."
        )

    BACKUPS.mkdir(parents=True, exist_ok=True)

    validator_backup = (
        BACKUPS
        / f"validate_dynamic_route_v1_before_context_repair_{STAMP}.py"
    )
    shutil.copy2(VALIDATOR, validator_backup)

    text = VALIDATOR.read_text(encoding="utf-8")

    old_block = '''    goals = get_goal_options(
        "Eukaryotic genome",
        "Illumina",
        "Single-end",
    )
'''

    new_block = '''    reference_context = {
        "status": "ncbi_reference",
        "usable_reference": True,
        "reference_accession": "GCF_TEST.1",
    }

    goals = get_goal_options(
        "Eukaryotic genome",
        "Illumina",
        "Single-end",
        reference_context=reference_context,
    )
'''

    if old_block in text:
        text = text.replace(
            old_block,
            new_block,
            1
        )
        VALIDATOR.write_text(
            text,
            encoding="utf-8"
        )
        print("Updated Dynamic Route v1 validator for reference-aware semantics.")
    elif "reference_context=reference_context" in text:
        print("Dynamic Route v1 validator is already reference-aware.")
    else:
        fail(
            "Could not locate the expected goal-options test block in the "
            "Dynamic Route v1 validator."
        )

    if CONTEXT.exists():
        CONTEXT.unlink()
        print("Removed partial engine/context_intake.py")

    if NCBI.exists():
        NCBI.unlink()
        print("Removed partial services/ncbi_reference.py")

    if CONTEXT_TEST_DIR.exists():
        shutil.rmtree(CONTEXT_TEST_DIR)
        print("Removed partial tests/context_intake_v1")

    print("")
    print("Re-running Context Intake + Reference Finder v1...")
    print("")

    result = subprocess.run(
        [str(PYTHON), str(INSTALLER)],
        cwd=ROOT
    )

    if result.returncode != 0:
        fail(
            "The repaired installer still failed. Send me the new terminal "
            "output; the original project files should have been restored by "
            "the installer."
        )

    print("")
    print("=" * 78)
    print("RESULT: PASS")
    print("Validator compatibility repaired and Context Intake v1 installed.")
    print("")
    print("The semantic change is intentional:")
    print("  - Variant analysis is hidden when no usable reference is selected.")
    print("  - The old Dynamic Route test now supplies a reference before expecting")
    print("    Variant analysis to appear.")
    print("")
    print("Preview:")
    print(r'  & ".\.venv\Scripts\python.exe" -m streamlit run app.py')


if __name__ == "__main__":
    main()
