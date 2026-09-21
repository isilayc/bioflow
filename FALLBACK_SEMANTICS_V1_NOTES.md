# OmicsRoute Fallback Semantics v1

This update makes BLOCK states actionable without inventing scientifically unrelated alternatives.

It distinguishes three recovery modes:

1. **Direct same-step fallback** — if a genuinely valid candidate already exists, it remains runnable and is surfaced clearly. geNomad viral detection is upgraded so VirSorter2 is available as a direct curated alternative.
2. **Alternative workflow strategy** — when changing the tool would actually change the scientific method, OmicsRoute suggests another complete route for the same dataset context instead of silently swapping methods.
3. **No equivalent fallback / remediation** — when the catalog has no equivalent substitute, OmicsRoute says so and explains how to repair the current route.

This patch intentionally does **not** force alternatives into every single-tool step. Some tools are methodologically coupled to a workflow or do not have an equivalent replacement in the current catalog.

Run from the OmicsRoute project root:

```powershell
python apply_fallback_semantics_v1.py
```

The installer creates a timestamped backup, patches the project, validates the new logic, and reruns the scientific benchmark when that benchmark is installed.
