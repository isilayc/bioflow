# OmicsRoute Web parity v1

This package ports the accepted Streamlit decision-support features into the
FastAPI + Next.js application while leaving the Streamlit beta untouched.

Included in this pass:

- NCBI organism/reference finder
- data-state-aware planning
- route/strategy selection
- workflow overview and required inputs
- dependency-path validation
- dynamic dataset constraint fields
- workflow- and tool-level constraint reports
- compute-environment feasibility and operational ranking
- 0–100 OmicsRoute score breakdown
- ranked alternatives vs parallel branches
- fallback/recovery guidance
- marker/reference database guidance
- on-demand literature evidence
- live bio.tools metadata
- advanced registry discovery
- catalogue coverage + on-demand full dependency audit
- Markdown / JSON export
- About / Methodology / Interpretation content

Run API:

```powershell
& ".\.venv\Scripts\python.exe" -m uvicorn api.main:app --reload --port 8000
```

Run frontend:

```powershell
cd frontend
npm.cmd run dev
```

Open:

```text
http://localhost:3000
```
