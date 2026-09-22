# OmicsRoute Context Intake + Reference Finder v1

New genome-analysis intake:

**Sample type → Current data → Sequencing/read layout (when relevant) →
Organism/reference → Analysis goal**

For genome-oriented projects the user can now start from raw reads, an existing
genome assembly, or (for eukaryotic projects) predicted proteins.

The integrated Reference Finder uses the current NCBI Datasets v2 REST API to:

- search NCBI Taxonomy by scientific/common name or Taxonomy ID,
- find genome assemblies for the selected taxon,
- distinguish NCBI-designated reference genomes from representative or ordinary
  same-species assemblies,
- verify a user-supplied `GCF_...` / `GCA_...` assembly accession.

Reference-based Variant analysis remains hidden until a usable reference is
selected.

Apply:

```powershell
& ".\.venv\Scripts\python.exe" apply_context_intake_reference_finder_v1.py
```

Then preview:

```powershell
& ".\.venv\Scripts\python.exe" -m streamlit run app.py
```

Installation tests do not require internet. Live NCBI searching is exercised
from the web UI.
