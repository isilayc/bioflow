# BioFlow Coverage Audit v1

Run from the BioFlow project root:

```powershell
python .\tests\coverage_audit_v1\run_coverage_audit.py
```

Outputs are written to `tests\coverage_audit_v1\results\`.

The audit does not modify application code or YAML files. It identifies:
- workflow steps with only one candidate tool,
- single-candidate steps where a dataset constraint may BLOCK the only tool,
- operations with shallow alternative coverage,
- workflow candidates missing from `tools.yaml`,
- candidate tools missing from `tool_io.yaml`,
- candidate-tool constraint coverage.

Use the generated report to decide which fallback tools should be added next.
