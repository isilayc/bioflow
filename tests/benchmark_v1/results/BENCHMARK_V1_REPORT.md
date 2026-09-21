# BioFlow Scientific Recommendation Benchmark v1

Generated: 2026-09-21T13:59:42+03:00

## Summary

- Overall status: **PASS**
- Curated scenarios: **17**
- Hard benchmark score: **100.00%** (252/252)
- Hard failures: **0**
- Soft warnings: **0**
- Regression validator failures: **0**

This v1 benchmark is a curated internal scientific-content validation panel. It is useful for regression testing and manuscript methods development, but it is not yet an independent external expert benchmark.

## Scenario results

### Bacterial isolate — Illumina WGS — PASS

Workflow: `bacterial_illumina_wgs`

- All benchmark checks passed.

### Bacterial isolate — Oxford Nanopore WGS — PASS

Workflow: `bacterial_nanopore_wgs`

- All benchmark checks passed.

### Bacterial isolate — AMR detection — PASS

Workflow: `bacterial_illumina_amr`

- All benchmark checks passed.

### Metagenome — single-sample MAG reconstruction — PASS

Workflow: `metagenome_illumina_mag_single`

- All benchmark checks passed.

### Metagenome — coassembly MAG reconstruction — PASS

Workflow: `metagenome_illumina_mag_coassembly`

- All benchmark checks passed.

### Metagenome — viral analysis — PASS

Workflow: `metagenome_illumina_viral`

- All benchmark checks passed.

### Virome — viral host prediction — PASS

Workflow: `virome_illumina_host_prediction`

- All benchmark checks passed.

### Virome — vOTU clustering — PASS

Workflow: `virome_illumina_votu_clustering`

- All benchmark checks passed.

### Amplicon — modular 16S ASV workflow — PASS

Workflow: `amplicon_illumina_16s`

- All benchmark checks passed.

### Amplicon — ASV inference — PASS

Workflow: `amplicon_illumina_asv_inference`

- All benchmark checks passed.

### Amplicon — repeated-measures differential abundance — PASS

Workflow: `amplicon_illumina_da_repeated`

- All benchmark checks passed.

### Bulk RNA-seq — alignment-based differential expression — PASS

Workflow: `bulk_transcriptome_illumina_differential_expression_alignment`

- All benchmark checks passed.

### Bulk RNA-seq — lightweight differential expression — PASS

Workflow: `bulk_transcriptome_illumina_differential_expression_lightweight`

- All benchmark checks passed.

### Eukaryotic genome — ONT assembly — PASS

Workflow: `eukaryotic_genome_ont_assembly`

- All benchmark checks passed.

### Eukaryotic genome — gene prediction with repeat masking — PASS

Workflow: `eukaryotic_genome_gene_prediction_braker`

- All benchmark checks passed.

### Metatranscriptome — differential expression — PASS

Workflow: `metatranscriptome_illumina_differential_expression`

- All benchmark checks passed.

### Metagenome — broad taxonomic profiling — PASS

Workflow: `metagenome_illumina_taxonomy_broad`

- All benchmark checks passed.

## Global registry/contract audit

- **PASS** `global:tool_registry` — No workflow candidate(s) missing from tools.yaml. Audited 459 workflow candidate references.
- **PASS** `global:operation_contract` — No workflow candidate(s) do not declare their workflow operation. Audited 459 workflow candidate references.
- **PASS** `global:tool_io` — No workflow candidate(s) missing from tool_io.yaml. Audited 459 workflow candidate references.
- **PASS** `global:duplicate_candidates` — No workflow step(s) contain duplicate candidate IDs. Audited 459 workflow candidate references.

## Existing regression validators

### validate_scoring_v2.py — PASS

```text
Score range: 61 to 100
Unique score values: 23
100/100 appearances: 12
Fit labels: {'curated': 411, 'strong': 34, 'supported': 9, 'conditional': 5}
Compatibility gate: PASS
Operation gate: PASS
Scientific-fit priority: PASS
RESULT: PASS
```

### validate_constraints.py — PASS

```text
BioFlow constraints structural validation
========================================================================
Tool constraints:     11
Workflow constraints: 10
Errors:               0
Warnings:             0

RESULT: PASS
```

### validate_constraint_coverage_v1.py — PASS

```text
[PASS] DADA2 overlap warning: warning
[PASS] DADA2 missing overlap inputs: needs_input
[PASS] Pangenome workflow 2 genomes: pass
[PASS] Pangenome workflow 1 genome: block

========================================================================
RESULT: PASS
Constraint coverage v1 is structurally valid and functional tests passed.
```

### validate_constraint_aware_ranking_v3.py — PASS

```text
[PASS] app.py marker: Constraint-aware ranking v3 is active.
[PASS] app.py marker: dataset-specific constraint blocks this branch
[PASS] Sequential ranking gate order is correct
[PASS] Old advisory-only constraint caption removed

========================================================================
RESULT: PASS
Constraint-aware ranking v3 is structurally valid and behavior tests passed.
```

### validate_mag_taxonomy_fallback_v1.py — PASS

```text
MAG taxonomy workflows: metagenome_illumina_mag_coassembly, metagenome_illumina_mag_single
GTDB-Tk database unavailable -> BLOCK: PASS
CAT/BAT database available -> PASS: PASS
sourmash database+taxonomy available -> PASS: PASS
Non-bacterial/non-archaeal domain mismatch blocks curated MAG fallbacks: PASS
Ranking hard-gate fallback behavior: PASS
RESULT: PASS
```
