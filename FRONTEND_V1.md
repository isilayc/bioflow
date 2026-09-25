# OmicsRoute Frontend v1

Terminal 1:

```powershell
& ".\.venv\Scripts\python.exe" -m uvicorn api.main:app --reload --port 8000
```

Terminal 2:

```powershell
cd frontend
npm run dev
```

Open `http://localhost:3000`.
