from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path.cwd()
APP = ROOT / "app.py"
BACKUPS = ROOT / "backups"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
PYTHON = VENV if VENV.exists() else Path(sys.executable)


def fail(message: str) -> None:
    print("")
    print("=" * 76)
    print("RESULT: FAIL")
    print(message)
    raise SystemExit(1)


def main() -> None:
    print("=" * 76)
    print("OmicsRoute safe app.py restore")
    print("=" * 76)

    if not APP.exists():
        fail("Run this script from the project root containing app.py.")

    BACKUPS.mkdir(parents=True, exist_ok=True)

    broken_backup = BACKUPS / f"app_broken_before_safe_restore_{STAMP}.py"
    shutil.copy2(APP, broken_backup)

    candidates = sorted(
        BACKUPS.glob("app_before_dependency_perf_v1_*.py"),
        key=lambda p: p.stat().st_mtime_ns,
        reverse=True,
    )

    if not candidates:
        fail(
            "Could not find backups/app_before_dependency_perf_v1_*.py. "
            "Do not make more edits; send me the filenames inside the backups folder."
        )

    good = candidates[0]
    text = good.read_text(encoding="utf-8")

    suspicious = ("â€¢", "â†", "ğŸ", "Ã", "Â", "�")
    found = [token for token in suspicious if token in text]

    if found:
        fail(
            f"The selected backup also appears encoding-damaged: {good.name}. "
            f"Suspicious markers: {found}"
        )

    text = text.replace(
        "BIOFLOW • WEB RELEASE CANDIDATE",
        "OMICSROUTE • WEB RELEASE CANDIDATE",
    )

    old_reports = '''    dependency_signature = (
        get_dependency_signature()
    )

    for workflow_id in workflows:

        reports[
            workflow_id
        ] = (
            cached_validate_workflow(
                workflow_id,
                dependency_signature
            )
        )
'''

    new_reports = '''    # The complete audit is already cached by cached_dependency_coverage().
    # Avoid creating a separate Streamlit cache entry for every workflow.
    for workflow_id in workflows:

        reports[
            workflow_id
        ] = (
            validate_workflow(
                workflow_id
            )
        )
'''

    if old_reports in text:
        text = text.replace(old_reports, new_reports, 1)

    old_caption = '''            "The full dependency audit is calculated only when requested "
            "and then cached. This keeps normal workflow selection fast."'''

    new_caption = '''            "The full dependency audit is calculated only when requested "
            "and then cached. The first run validates the complete workflow "
            "catalogue; later loads are reused until catalogue files change."'''

    if old_caption in text:
        text = text.replace(old_caption, new_caption, 1)

    APP.write_text(text, encoding="utf-8")

    result = subprocess.run(
        [str(PYTHON), "-m", "py_compile", str(APP)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        shutil.copy2(broken_backup, APP)
        fail(
            "Restored file failed syntax validation, so the previous app.py "
            "was put back.\n" + (result.stderr or result.stdout)
        )

    final = APP.read_text(encoding="utf-8")

    bad_markers = [token for token in suspicious if token in final]

    if bad_markers:
        fail(
            "Encoding markers are still present after restore: "
            + ", ".join(bad_markers)
        )

    if "OMICSROUTE • WEB RELEASE CANDIDATE" not in final:
        fail("OmicsRoute release-candidate header was not found after restore.")

    print(f"Restored from: {good}")
    print(f"Broken copy saved as: {broken_backup}")
    print("")
    print("Encoding check: PASS")
    print("Python syntax check: PASS")
    print("OmicsRoute header check: PASS")
    print("")
    print("=" * 76)
    print("RESULT: PASS")
    print("app.py was restored from the last known-good UTF-8 backup.")
    print("")
    print("Now restart Streamlit:")
    print(r'  & ".\.venv\Scripts\python.exe" -m streamlit run app.py')


if __name__ == "__main__":
    main()
