# OmicsRoute Dependency Audit Performance v1

This patch targets the slow **Catalogue coverage & validation** audit.

The main bottleneck was repeated parsing of the same YAML catalogues while
validating every workflow, tool route and artifact state. Alternative branches
could also retain dependency states that were strict subsets of richer states.

The patch adds file-version-aware YAML caching, cached artifact expansion,
safe dominance pruning of redundant dependency states, and removes nested
per-workflow Streamlit cache calls from the already-cached full audit.

It does not change workflow definitions, tool routes, scoring, constraints or
fallback logic.

Apply:

```powershell
& ".\.venv\Scripts\python.exe" apply_dependency_audit_performance_v1.py
```

The installer runs the existing regression validators and then validates the
whole workflow catalogue once as a performance smoke test.

Preview:

```powershell
& ".\.venv\Scripts\python.exe" -m streamlit run app.py
```
