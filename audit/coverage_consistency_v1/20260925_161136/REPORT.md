# OmicsRoute Coverage & Consistency Audit v1

Generated: 2026-09-25T16:11:37

## Executive summary

- Sample types: **7**
- Raw sequencing/read-layout contexts: **28**
- Biological goal exposures audited: **145**
- Workflow strategies discovered: **203**
- Workflow strategies built successfully: **203**
- Issues recorded: **0**
- Critical issues: **0**
- High issues: **0**

## Sample-type coverage

| Sample type | Platform/read contexts | Goal exposures | Strategies | Dependency failures | Compatibility failures |
|---|---:|---:|---:|---:|---:|
| Bacterial isolate | 5 | 21 | 27 | 0 | 0 |
| Metagenome | 6 | 39 | 50 | 0 | 0 |
| Amplicon | 3 | 13 | 44 | 0 | 0 |
| Bulk transcriptome | 3 | 15 | 17 | 0 | 0 |
| Virome | 3 | 24 | 27 | 0 | 0 |
| Eukaryotic genome | 5 | 20 | 23 | 0 | 0 |
| Metatranscriptome | 3 | 13 | 15 | 0 | 0 |

## Issue categories

- No issues detected.

## Interpretation

A visible sequencing platform/read-layout/goal is treated as a UI promise. The audit flags a critical issue when that promise has no strategy or cannot be built. Dependency failures and steps with no compatible candidate tools are reported separately so catalogue breadth is not confused with executable coverage.

Reference-gated genome goals are audited twice: first as the UI appears without a selected reference, then with a placeholder usable-reference context. This avoids incorrectly treating a deliberately hidden reference-dependent goal as missing.

Non-raw data states are reported separately because they are artifact-driven rather than sequencing-platform-driven.

## Files

- `raw_coverage_matrix.csv` — platform/read-layout/goal coverage by sample type
- `raw_route_audit.csv` — every discovered strategy with dependency/tool-compatibility result
- `issues.csv` — actionable gaps and failures
- `nonraw_context_state_audit.csv` — assembly/table/FASTA downstream-state visibility
- `summary.json` — machine-readable audit totals
