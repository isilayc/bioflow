from __future__ import annotations

import json
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.exporter import export_filename, workflow_to_json, workflow_to_markdown


def fail(msg: str) -> None:
    print("FAIL:", msg)
    raise SystemExit(1)


def main() -> int:
    app = ROOT / "app.py"
    exporter = ROOT / "engine" / "exporter.py"

    if not app.exists() or not exporter.exists():
        fail("app.py or engine/exporter.py is missing")

    py_compile.compile(str(app), doraise=True)
    py_compile.compile(str(exporter), doraise=True)

    text = app.read_text(encoding="utf-8")
    required = [
        "from engine.exporter import (",
        "def show_workflow_overview_and_export(",
        "show_workflow_overview_and_export(",
        "Recommended next action",
        "download_button(",
    ]
    for marker in required:
        if marker not in text:
            fail(f"app.py integration marker missing: {marker}")

    # Internal workflow IDs should no longer be printed in the recovery list.
    forbidden = "f\" (`{strategy.get('id')}`)\""
    if forbidden in text:
        fail("Recovery UI still exposes internal workflow IDs")

    sample = {
        "id": "demo_workflow",
        "name": "Demo workflow",
        "description": "A validation workflow.",
        "context": {
            "sample_type": "Metagenome",
            "sequencing": "Illumina",
            "goal": "MAG reconstruction",
        },
        "external_inputs": ["paired_fastq"],
        "steps": [
            {
                "operation": "raw_read_qc",
                "name": "Read QC",
                "description": "Inspect read quality.",
                "tools": [
                    {
                        "id": "fastqc",
                        "name": "FastQC",
                        "score": {"total": 88},
                    }
                ],
            }
        ],
    }

    md = workflow_to_markdown(sample)
    js = workflow_to_json(sample)
    parsed = json.loads(js)

    if "# Demo workflow" not in md or "FastQC" not in md:
        fail("Markdown export is incomplete")
    if parsed["workflow"]["steps"][0]["candidate_tools"][0]["name"] != "FastQC":
        fail("JSON export is incomplete")
    if export_filename(sample, "json") != "demo_workflow.json":
        fail("Export filename sanitization failed")

    print("=" * 72)
    print("BioFlow Final UI/UX + Workflow Export v1")
    print("=" * 72)
    print("App compile: PASS")
    print("Exporter compile: PASS")
    print("Markdown export: PASS")
    print("JSON export: PASS")
    print("Recovery UI ID hiding: PASS")
    print("")
    print("RESULT: PASS")
    print("Final UI/UX + Workflow Export v1 is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
