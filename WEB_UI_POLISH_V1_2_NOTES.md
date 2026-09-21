# BioFlow Web UI Polish v1.2

This update follows the first visual review of the public BioFlow interface.

## Changes

- reduces the top-heavy page spacing;
- makes the hero title more compact;
- makes the GitHub button compact;
- renames Step 4 to **Review & export**;
- keeps **Workflow overview** near the beginning;
- moves Markdown/JSON export to the end of the recommended workflow;
- adds a dedicated final **Review & export** section.

Scientific scoring, constraints, ranking, workflow definitions, fallback semantics,
dependency validation, operational feasibility, and evidence logic are unchanged.

## Apply

```powershell
& ".\.venv\Scripts\python.exe" apply_bioflow_web_ui_polish_v1_2.py
```

Preview:

```powershell
& ".\.venv\Scripts\python.exe" -m streamlit run app.py
```

If it looks correct:

```powershell
git add app.py
git commit -m "Refine BioFlow web flow and export placement"
git push
```
