# OmicsRoute Context Engine v2

Extends the context-aware intake model beyond eukaryotic WGS.

## Added

- Bacterial isolate
  - Illumina Single-end becomes selectable.
  - Assembly-based WGS/AMR/virulence/MLST/prophage/species/plasmid routes can
    adapt to Single-end input when their actual tool dependencies allow it.
  - Variant analysis still requires a selected reference.

- Metagenome
  - Existing assembled contigs can be used directly for:
    - virulence profiling,
    - viral analysis,
    - plasmid analysis.
  - OmicsRoute does not force the user to repeat read QC/assembly.

- Virome
  - Existing viral FASTA can be used directly for:
    - CheckV quality assessment,
    - viral taxonomy,
    - host prediction,
    - vOTU clustering,
    - viral functional annotation.

- Bulk transcriptome
  - Existing gene count matrix -> differential expression.
  - Significant gene list -> functional enrichment.
  - Ranked gene list -> pathway analysis.

The patch also adds the missing SPAdes Single-end artifact route and declares
Single-end support in the curated SPAdes metadata.

## Apply

```powershell
& ".\.venv\Scripts\python.exe" apply_context_engine_v2.py
```

Then:

```powershell
& ".\.venv\Scripts\python.exe" -m streamlit run app.py
```
