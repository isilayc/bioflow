# OmicsRoute Public Beta

OmicsRoute is an evidence-aware bioinformatics workflow planning and decision-support system.

## What the public beta does

- accepts a biological/sample context and the data state you currently have;
- exposes compatible sequencing/read-layout contexts and biological goals;
- compares curated workflow strategies;
- validates technical dependencies;
- checks dataset-specific constraints where encoded;
- considers the user-entered compute environment;
- surfaces tool options, evidence, recovery guidance and exportable workflow plans.

OmicsRoute does **not** upload or execute user sequencing files in the web planner.

## Validation status

Before this beta milestone, the local catalogue/backend coverage audit and the web end-to-end smoke test were both run successfully with zero critical/high issues reported by the test suite.

These are internal software/regression checks, not independent scientific validation or a universal benchmark of every supported tool and dataset.

## Beta feedback

Use the `Send feedback` control in the web interface or open a GitHub issue using the Beta feedback template.

Do not submit confidential, patient-identifiable, or otherwise sensitive data in feedback issues.
