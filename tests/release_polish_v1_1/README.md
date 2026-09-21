# BioFlow Release Polish v1.1

This is the final small release-polish patch after Final UI/UX + Workflow Export v1.

It does **not** change scientific scoring, constraints, ranking, fallback semantics, or benchmark expectations.

Changes:

- Fixes `Required inputs = 0` for older workflows that do not explicitly declare `external_inputs` by using the initial artifacts already resolved by BioFlow's dependency validator.
- Uses the same resolved inputs in the `Required user inputs` expander.
- Renames `Candidate tools` to `Tool options` so the overview does not imply that every listed tool must be run.
- Simplifies the technical-path status message to `Workflow path is technically complete.`
- Renames the dependency expander to `Technical details`.

Run from the BioFlow project root:

```powershell
python apply_release_polish_v1_1.py
```

A timestamped backup is created automatically. Existing Final UI/Export, Fallback Semantics, and Scientific Benchmark validators are rerun when present.
