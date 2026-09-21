# BioFlow Web UI Polish v1.3

v1.2 failed because the existing `Final UI/UX + Workflow Export v1` regression
validator explicitly requires `show_workflow_overview_and_export()` to remain in
`app.py`.

v1.3 preserves that legacy integration marker, but the function now renders only
the top workflow overview. The actual Markdown/JSON export controls are rendered
in a separate final **Review & export** section.

No scientific logic is changed.

Run:

```powershell
& ".\.venv\Scripts\python.exe" apply_bioflow_web_ui_polish_v1_3.py
```

Then preview:

```powershell
& ".\.venv\Scripts\python.exe" -m streamlit run app.py
```
