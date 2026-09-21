# OmicsRoute Brand Rename v1

This package rebrands the public project from **BioFlow** to **OmicsRoute**.

## It changes

- Streamlit page title and visible application copy
- About / Methodology wording
- recommendation/support-score wording
- Markdown and JSON export branding
- exported score key from `bioflow_score` to `omicsroute_score`
- fallback export filename from `bioflow_workflow` to `omicsroute_workflow`
- README branding and future GitHub links
- selected public deployment/release documentation
- CSS presentation class names
- `prepare_bioflow_web_deploy.py` -> `prepare_omicsroute_web_deploy.py`
- visible version string to **OmicsRoute v1.1.0**

## It deliberately does not change

- workflow IDs
- tool IDs
- scientific scoring equations
- constraints
- fallback semantics
- dependency rules
- benchmark cases
- validator source files
- the local folder name `bioflow`
- the currently working Streamlit URL `bioflow1.streamlit.app`

The old validator sources retain the historical BioFlow label so they can verify
that the brand migration did not accidentally change scientific or structural
behaviour.

## Apply

Extract into the current project root and run:

```powershell
& ".\.venv\Scripts\python.exe" apply_omicsroute_brand_rename_v1.py
```

Preview:

```powershell
& ".\.venv\Scripts\python.exe" -m streamlit run app.py
```

If the UI looks correct:

```powershell
git add -A
git commit -m "Rename BioFlow to OmicsRoute"
git pull --rebase origin main
git push
```

After the push, rename the GitHub repository in GitHub:

**Settings -> General -> Repository name -> `omicsroute` -> Rename**

Then update the local remote:

```powershell
git remote set-url origin https://github.com/isilayc/omicsroute.git
git remote -v
```

The Streamlit URL can be renamed separately once an OmicsRoute subdomain is
confirmed available.
