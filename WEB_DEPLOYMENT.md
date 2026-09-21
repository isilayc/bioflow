# BioFlow Web Deployment

BioFlow is prepared for deployment on Streamlit Community Cloud.

## Repository contents that must be on GitHub

Keep:
- app.py
- data/
- engine/
- services/
- requirements.txt
- .streamlit/config.toml
- any other project source files imported by app.py

Do not upload:
- .venv/
- build/
- release/
- backups/
- logs/

## Deploy

1. Push the BioFlow project to a GitHub repository.
2. Open https://share.streamlit.io
3. Click **Create app**.
4. Select the BioFlow GitHub repository.
5. Branch: normally `main`.
6. Entrypoint: `app.py`.
7. In Advanced settings, choose the same Python major/minor version you use
   locally when possible.
8. Deploy.

The deployed application receives a `*.streamlit.app` URL that works on
Windows, macOS, Linux, phones, and tablets through a browser.
