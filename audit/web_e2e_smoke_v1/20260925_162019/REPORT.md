# OmicsRoute Web End-to-End Smoke Test v1

Generated: 2026-09-25T16:20:54

## Executive summary

- Frontend reachable: **True**
- API reachable: **True**
- Sample types: **7**
- Raw contexts exercised: **28**
- Goals exercised: **145**
- Strategies exercised: **203**
- Successful workflow/inspect calls: **203**
- Failures recorded: **0**
- Critical: **0**
- High: **0**

## Compute profile

- Test attempted: **True**
- Payload accepted: **True**
- Operational assessments found: **16**

## Failure categories

- None

## Notes

This is an integration smoke test, not a browser visual-regression test. It verifies that the frontend is reachable and then exercises the same API chain used by the web UI: sample type → sequencing → read layout → goals → strategies → workflow inspection.

External live services such as NCBI, OpenAlex, PubMed and bio.tools are not treated as release blockers here because temporary network/API outages should not make the local OmicsRoute application fail release validation.

## Files

- `route_e2e.csv` — every strategy exercised through `/v1/workflow/inspect`
- `failures.csv` — actionable API/frontend integration failures
- `checks.csv` — endpoint and frontend checks
- `summary.json` — machine-readable totals
