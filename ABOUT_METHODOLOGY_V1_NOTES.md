# BioFlow About & Methodology v1

Adds a compact **About BioFlow & methodology** section to the public interface.

The section contains three tabs:

- About
- Methodology
- Interpretation

It explains BioFlow v1.0.0, the recommendation layers, technical dependency
validation, dataset/operational constraints, evidence/fallback logic, and the
limits of the current internal benchmark.

No scientific recommendation logic is changed.

## Apply

```powershell
& ".\.venv\Scripts\python.exe" apply_bioflow_about_methodology_v1.py
```

## Preview

```powershell
& ".\.venv\Scripts\python.exe" -m streamlit run app.py
```

If it looks correct:

```powershell
git add app.py
git commit -m "Add BioFlow about and methodology section"
git push
```
