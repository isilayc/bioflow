# Deploy OmicsRoute Public Beta

The application is split into:

- `frontend/`: Next.js browser interface
- `api/`: FastAPI backend
- `engine/`, `data/`, `services/`: scientific planning engine and catalogue

A straightforward public-beta deployment is:

- **Frontend:** Vercel
- **Backend:** Render

## 1. Push the validated local project to GitHub

From the project root:

```powershell
git status
git add -A
git commit -m "Prepare OmicsRoute public beta"
git push origin main
```

Do not create the release tag until this push succeeds.

## 2. Deploy the FastAPI backend on Render

Create a new Blueprint/Web Service from the GitHub repository. The repository includes `render.yaml`.

The service uses:

- build: `pip install -r requirements.txt`
- start: `python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- health check: `/health`

For the first deploy, temporarily set:

```text
OMICSROUTE_CORS_ORIGINS=http://localhost:3000
```

After the Vercel frontend exists, replace it with the real Vercel origin, for example:

```text
OMICSROUTE_CORS_ORIGINS=https://your-omicsroute.vercel.app
```

If you later add a custom domain, include that origin as well. Multiple origins are comma-separated.

## 3. Deploy the Next.js frontend on Vercel

Import the same GitHub repository into Vercel.

Set **Root Directory** to:

```text
frontend
```

Vercel should auto-detect Next.js.

Add:

```text
NEXT_PUBLIC_OMICSROUTE_API_URL=https://YOUR-RENDER-BACKEND.onrender.com
```

Deploy.

## 4. Final production check

Open the public frontend and verify:

1. API badge becomes `API connected`.
2. Select at least one short-read and one long-read context.
3. Build a workflow.
4. Change the computer profile and rebuild.
5. Open a tool card.
6. Download Markdown and JSON.
7. Click `Send feedback`.
8. Check the layout on a phone-sized browser window.

## 5. Create the beta tag

After the public deployment passes:

```powershell
git tag -a v0.1.0-beta.1 -m "OmicsRoute public beta 0.1.0-beta.1"
git push origin v0.1.0-beta.1
```

The release tag should point to the exact commit that was deployed and tested.
