# OmicsRoute Dynamic Route Engine v1

Pilot scope:

**Eukaryotic genome → Illumina → Paired-end / Single-end**

This patch stops treating exact `workflows.yaml` context enumeration as the only
source of UI choices for the pilot context.

It adds:

- Single-end as a real Illumina read layout
- dynamic Single-end variant analysis
- assembly-level downstream routes independent of raw read layout
- two gene-prediction strategies
- explicit route-availability messaging
- an explicit "not curated" state for Illumina-only eukaryotic de novo assembly
  instead of inventing an unsuitable bacterial assembly route

Apply:

```powershell
& ".\.venv\Scripts\python.exe" apply_dynamic_route_engine_v1.py
```

Expected:

```text
RESULT: PASS
OmicsRoute Dynamic Route Engine v1 was applied successfully.
```

Preview:

```powershell
& ".\.venv\Scripts\python.exe" -m streamlit run app.py
```
