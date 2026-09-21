# OmicsRoute Final UI/UX + Workflow Export v1

This patch is intentionally product-facing. It does not change OmicsRoute's scientific scoring or constraint logic.

It adds:

- a compact workflow overview at the top of each built workflow,
- Markdown and JSON workflow export buttons,
- a cleaner blocked-tool recovery panel,
- human-readable fallback strategy names without internal workflow IDs,
- shorter ranking explanations while preserving transparency,
- regression validation for the exporter and UI integration.

Run from the OmicsRoute project root:

```powershell
python apply_final_ui_export_v1.py
```

The installer creates a timestamped backup before changing files and reruns existing fallback/benchmark validators when they are available.
