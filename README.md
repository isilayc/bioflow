# OmicsRoute

**OmicsRoute** is an evidence-aware bioinformatics workflow recommendation system that helps users choose analysis strategies and tools based on sample type, sequencing technology, analysis goal, dataset constraints, and operational feasibility.

🌐 **Live web app:** https://bioflow1.streamlit.app

> **Project naming:** OmicsRoute was developed initially under the working name BioFlow. The project was renamed before manuscript submission to avoid ambiguity with existing bioinformatics software.

## What OmicsRoute does

OmicsRoute builds context-specific bioinformatics workflows rather than returning a generic list of tools. The recommendation engine separates:

- scientific fit,
- dataset-specific constraints,
- technical input/output compatibility,
- operational feasibility,
- fallback and recovery strategies,
- literature and registry evidence.

OmicsRoute does **not** execute the underlying bioinformatics tools. It is a workflow planning and decision-support interface.

## Current scope

The catalogue currently covers multiple analysis families including:

- bacterial isolate genomics,
- eukaryotic genome analysis,
- environmental shotgun metagenomics,
- amplicon workflows,
- transcriptomics,
- viral and phage analysis,
- MAG-oriented workflows,
- taxonomy, quality assessment, host prediction, and related downstream analyses.

Supported workflow decisions can depend on sequencing platform, read type, analysis objective, reference/database availability, dataset characteristics, and compute profile.

## Recommendation logic

OmicsRoute keeps different decision layers separate:

1. **Scientific fit** — whether a tool or strategy is appropriate for the requested biological analysis.
2. **Technical dependency validation** — whether the required input artifacts can be produced by the upstream workflow.
3. **Dataset constraints** — explicit PASS / WARNING / BLOCK logic for tools with known applicability requirements.
4. **Operational feasibility** — compute and runtime requirements where relevant.
5. **Fallback semantics** — direct alternatives, workflow-strategy changes, or remediation guidance when no equivalent replacement exists.

A blocked tool is not silently replaced with an unrelated method.

## Evidence

OmicsRoute can query external scientific resources and literature services through its research layer, including bio.tools, OpenAlex, Europe PMC, and PubMed-oriented services.

The curated catalogue and evidence layer are kept separate so literature support does not override hard technical or dataset constraints.

## Workflow export

Generated workflows can be exported as:

- Markdown
- JSON

Exports are intended for methods planning, sharing, and reproducibility notes.

## Validation

The repository contains internal validation and audit suites for:

- scientific recommendation scenarios,
- workflow dependency structure,
- constraint-aware ranking,
- fallback semantics,
- UI/export integration,
- catalogue coverage.

The current scientific benchmark is an **internal curated benchmark**, not an independent external gold-standard validation.

## Run locally

OmicsRoute requires Python and Streamlit.

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app then opens in a local web browser.

## Repository structure

```text
app.py                 Streamlit user interface
data/                  Workflow, tool, constraint, and capability catalogues
engine/                Recommendation and validation logic
services/              External registry and literature integrations
tests/                 Benchmark and regression validation
.streamlit/            Web application configuration
```

## Web deployment

The public web version is deployed with Streamlit Community Cloud from the `main` branch of this repository.

## Project status

OmicsRoute is under active development. The current public deployment should be treated as a research software release candidate while catalogue coverage, external validation, documentation, and manuscript preparation continue.

## Disclaimer

OmicsRoute provides bioinformatics workflow decision support. Recommendations should be interpreted together with the requirements of the user's dataset, computational environment, reference databases, and the documentation of the underlying bioinformatics tools.
