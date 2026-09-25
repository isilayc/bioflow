# OmicsRoute API Foundation v1

Run:

```powershell
& ".\.venv\Scripts\python.exe" -m uvicorn api.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/docs`.

Initial endpoints:

- `GET /health`
- `GET /v1/sample-types`
- `GET /v1/data-states`
- `GET /v1/sequencing-options`
- `GET /v1/read-types`
- `POST /v1/goals`
- `POST /v1/strategies`
- `POST /v1/workflow`
- `GET /v1/reference/taxa`
- `GET /v1/reference/assemblies`
- `GET /v1/reference/assembly/{accession}`
