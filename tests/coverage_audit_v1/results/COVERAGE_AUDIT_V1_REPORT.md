# BioFlow Coverage Audit v1

This is an internal product-coverage audit. It is not an external scientific validation.

## Executive summary

- Workflows: **107**
- Workflow steps: **327**
- Unique candidate tools used by workflows: **114**
- Candidate tools with dataset constraints: **11 / 114 (9.65%)**
- Steps with only one candidate tool: **223 (68.20%)**
- Singleton steps whose only tool has a constraint and could therefore BLOCK with no fallback: **27**
- Unknown candidate references: **0**
- Candidate references without tool_io route: **0**
- Operations represented by only one unique tool across all workflows: **35**

## Highest-priority fallback gaps

| Workflow | Step | Operation | Tool | Why it matters |
|---|---:|---|---|---|
| `metagenome_illumina_viral` | 5 | `viral_quality` | `checkv` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `metagenome_illumina_viral` | 6 | `viral_taxonomy` | `genomad` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `amplicon_illumina_16s` | 2 | `asv_inference` | `dada2` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `amplicon_illumina_18s` | 2 | `asv_inference` | `dada2` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `amplicon_illumina_its` | 2 | `asv_inference` | `dada2` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `amplicon_illumina_asv_inference` | 2 | `asv_inference` | `dada2` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `amplicon_illumina_taxonomic_assignment` | 2 | `asv_inference` | `dada2` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_viral_detection` | 3 | `viral_sequence_detection` | `genomad` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_quality_assessment` | 3 | `viral_sequence_detection` | `genomad` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_quality_assessment` | 4 | `viral_genome_quality` | `checkv` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_viral_taxonomy` | 3 | `viral_taxonomy` | `genomad` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_host_prediction` | 3 | `viral_sequence_detection` | `genomad` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_host_prediction` | 4 | `viral_genome_quality` | `checkv` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_host_prediction` | 5 | `viral_host_prediction` | `iphop` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_votu_clustering` | 3 | `viral_sequence_detection` | `genomad` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_votu_clustering` | 4 | `viral_genome_quality` | `checkv` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_functional_annotation` | 3 | `viral_sequence_detection` | `genomad` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_functional_annotation` | 4 | `viral_genome_quality` | `checkv` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_amg_analysis` | 3 | `dramv_preparation` | `virsorter2` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `eukaryotic_genome_quality` | 2 | `genome_quality_assessment` | `busco` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `bacterial_illumina_species_identification_gtdbtk` | 5 | `species_identification` | `gtdbtk` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `bacterial_illumina_plasmid_genomad` | 5 | `plasmid_detection` | `genomad` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `metagenome_illumina_plasmid_genomad` | 4 | `plasmid_detection` | `genomad` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_viral_abundance_contig` | 3 | `viral_sequence_detection` | `genomad` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_viral_abundance_contig` | 4 | `viral_genome_quality` | `checkv` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_viral_abundance_votu` | 3 | `viral_sequence_detection` | `genomad` | Constraint can BLOCK the only candidate; no automatic fallback exists. |
| `virome_illumina_viral_abundance_votu` | 4 | `viral_genome_quality` | `checkv` | Constraint can BLOCK the only candidate; no automatic fallback exists. |

## All single-candidate steps

| Workflow | Step | Operation | Tool |
|---|---:|---|---|
| `bacterial_illumina_wgs` | 1 | `raw_read_qc` | `fastqc` |
| `bacterial_illumina_wgs` | 4 | `assembly_qc` | `quast` |
| `bacterial_nanopore_wgs` | 1 | `raw_read_qc` | `nanoplot` |
| `bacterial_nanopore_wgs` | 4 | `assembly_qc` | `quast` |
| `metagenome_illumina_strain_phylogenomics` | 1 | `raw_read_qc` | `fastqc` |
| `metagenome_illumina_strain_phylogenomics` | 3 | `taxonomic_profiling` | `metaphlan` |
| `metagenome_illumina_strain_phylogenomics` | 4 | `marker_reconstruction` | `sample2markers` |
| `metagenome_illumina_strain_phylogenomics` | 5 | `strain_profiling` | `strainphlan` |
| `metagenome_illumina_microdiversity` | 1 | `raw_read_qc` | `fastqc` |
| `metagenome_illumina_microdiversity` | 3 | `read_mapping` | `bowtie2` |
| `metagenome_illumina_microdiversity` | 4 | `alignment_processing` | `samtools` |
| `metagenome_illumina_microdiversity` | 5 | `strain_profiling` | `instrain` |
| `bacterial_illumina_amr` | 1 | `raw_read_qc` | `fastqc` |
| `bacterial_illumina_amr` | 4 | `assembly_qc` | `quast` |
| `bacterial_illumina_virulence` | 1 | `raw_read_qc` | `fastqc` |
| `bacterial_illumina_virulence` | 4 | `assembly_qc` | `quast` |
| `bacterial_illumina_mlst` | 1 | `raw_read_qc` | `fastqc` |
| `bacterial_illumina_mlst` | 4 | `assembly_qc` | `quast` |
| `bacterial_illumina_prophage` | 1 | `raw_read_qc` | `fastqc` |
| `bacterial_illumina_prophage` | 4 | `assembly_qc` | `quast` |
| `bacterial_illumina_variant_analysis` | 1 | `raw_read_qc` | `fastqc` |
| `bacterial_illumina_variant_analysis` | 3 | `read_mapping` | `bwa_mem2` |
| `bacterial_illumina_variant_analysis` | 4 | `alignment_processing` | `samtools` |
| `bacterial_illumina_variant_analysis` | 6 | `variant_filtering` | `bcftools` |
| `bacterial_illumina_pangenome` | 1 | `raw_read_qc` | `fastqc` |
| `bacterial_illumina_pangenome` | 4 | `assembly_qc` | `quast` |
| `bacterial_illumina_phylogenomics` | 1 | `raw_read_qc` | `fastqc` |
| `bacterial_illumina_phylogenomics` | 4 | `assembly_qc` | `quast` |
| `bacterial_illumina_phylogenomics` | 6 | `core_genome_alignment` | `panaroo` |
| `bacterial_illumina_ont_hybrid` | 1 | `raw_read_qc` | `fastqc` |
| `bacterial_illumina_ont_hybrid` | 2 | `raw_read_qc` | `nanoplot` |
| `bacterial_illumina_ont_hybrid` | 6 | `assembly_qc` | `quast` |
| `bacterial_illumina_pacbio_hybrid` | 1 | `raw_read_qc` | `fastqc` |
| `bacterial_illumina_pacbio_hybrid` | 2 | `raw_read_qc` | `nanoplot` |
| `bacterial_illumina_pacbio_hybrid` | 4 | `read_preprocessing` | `filtlong` |
| `bacterial_illumina_pacbio_hybrid` | 6 | `assembly_qc` | `quast` |
| `metagenome_illumina_functional` | 1 | `raw_read_qc` | `fastqc` |
| `metagenome_illumina_functional` | 3 | `functional_profiling` | `humann` |
| `metagenome_illumina_pathways` | 1 | `raw_read_qc` | `fastqc` |
| `metagenome_illumina_pathways` | 3 | `pathway_analysis` | `humann` |
| `metagenome_illumina_virulence` | 1 | `raw_read_qc` | `fastqc` |
| `metagenome_illumina_virulence` | 4 | `virulence_profiling` | `pathofact2` |
| `metagenome_illumina_viral` | 1 | `raw_read_qc` | `fastqc` |
| `metagenome_illumina_viral` | 5 | `viral_quality` | `checkv` |
| `metagenome_illumina_viral` | 6 | `viral_taxonomy` | `genomad` |
| `amplicon_illumina_16s` | 1 | `primer_trimming` | `cutadapt` |
| `amplicon_illumina_16s` | 2 | `asv_inference` | `dada2` |
| `amplicon_illumina_16s_qiime2_asv` | 1 | `amplicon_end_to_end` | `qiime2_asv_workflow` |
| `amplicon_illumina_16s_nfcore` | 1 | `amplicon_end_to_end` | `nfcore_ampliseq_workflow` |
| `amplicon_illumina_16s_frogs` | 1 | `amplicon_end_to_end` | `frogs_workflow` |
| `amplicon_illumina_16s_lotus2` | 1 | `amplicon_end_to_end` | `lotus2_workflow` |
| `amplicon_illumina_16s_obitools4` | 1 | `amplicon_end_to_end` | `obitools4_workflow` |
| `amplicon_illumina_16s_mothur` | 1 | `amplicon_end_to_end` | `mothur_otu_workflow` |
| `amplicon_illumina_16s_vsearch_otu` | 1 | `amplicon_end_to_end` | `vsearch_otu_workflow` |
| `amplicon_illumina_16s_qiime2_otu` | 1 | `amplicon_end_to_end` | `qiime2_otu_workflow` |
| `amplicon_illumina_16s_silvangs` | 1 | `silvangs_input_preparation` | `silvangs_input_prep` |
| `amplicon_illumina_16s_silvangs` | 2 | `amplicon_end_to_end` | `silvangs_workflow` |
| `amplicon_illumina_18s` | 1 | `primer_trimming` | `cutadapt` |
| `amplicon_illumina_18s` | 2 | `asv_inference` | `dada2` |
| `amplicon_illumina_18s_qiime2_asv` | 1 | `amplicon_end_to_end` | `qiime2_asv_workflow` |
| `amplicon_illumina_18s_nfcore` | 1 | `amplicon_end_to_end` | `nfcore_ampliseq_workflow` |
| `amplicon_illumina_18s_frogs` | 1 | `amplicon_end_to_end` | `frogs_workflow` |
| `amplicon_illumina_18s_lotus2` | 1 | `amplicon_end_to_end` | `lotus2_workflow` |
| `amplicon_illumina_18s_obitools4` | 1 | `amplicon_end_to_end` | `obitools4_workflow` |
| `amplicon_illumina_18s_mothur` | 1 | `amplicon_end_to_end` | `mothur_otu_workflow` |
| `amplicon_illumina_18s_vsearch_otu` | 1 | `amplicon_end_to_end` | `vsearch_otu_workflow` |
| `amplicon_illumina_18s_qiime2_otu` | 1 | `amplicon_end_to_end` | `qiime2_otu_workflow` |
| `amplicon_illumina_18s_silvangs` | 1 | `silvangs_input_preparation` | `silvangs_input_prep` |
| `amplicon_illumina_18s_silvangs` | 2 | `amplicon_end_to_end` | `silvangs_workflow` |
| `amplicon_illumina_its` | 1 | `primer_trimming` | `cutadapt` |
| `amplicon_illumina_its` | 2 | `asv_inference` | `dada2` |
| `amplicon_illumina_its_qiime2_asv` | 1 | `amplicon_end_to_end` | `qiime2_asv_workflow` |
| `amplicon_illumina_its_nfcore` | 1 | `amplicon_end_to_end` | `nfcore_ampliseq_workflow` |
| `amplicon_illumina_its_frogs` | 1 | `amplicon_end_to_end` | `frogs_workflow` |
| `amplicon_illumina_its_lotus2` | 1 | `amplicon_end_to_end` | `lotus2_workflow` |
| `amplicon_illumina_its_obitools4` | 1 | `amplicon_end_to_end` | `obitools4_workflow` |
| `amplicon_illumina_its_mothur` | 1 | `amplicon_end_to_end` | `mothur_otu_workflow` |
| `amplicon_illumina_its_vsearch_otu` | 1 | `amplicon_end_to_end` | `vsearch_otu_workflow` |
| `amplicon_illumina_its_qiime2_otu` | 1 | `amplicon_end_to_end` | `qiime2_otu_workflow` |
| `amplicon_illumina_asv_inference` | 1 | `primer_trimming` | `cutadapt` |
| `amplicon_illumina_asv_inference` | 2 | `asv_inference` | `dada2` |
| `amplicon_illumina_taxonomic_assignment` | 1 | `primer_trimming` | `cutadapt` |
| `amplicon_illumina_taxonomic_assignment` | 2 | `asv_inference` | `dada2` |
| `amplicon_illumina_taxonomic_assignment_otu` | 1 | `primer_trimming` | `cutadapt` |
| `bulk_transcriptome_illumina_alignment_based` | 3 | `alignment_processing` | `samtools` |
| `bulk_transcriptome_illumina_alignment_based` | 4 | `gene_quantification` | `featurecounts` |
| `bulk_transcriptome_illumina_differential_expression_alignment` | 3 | `alignment_processing` | `samtools` |
| `bulk_transcriptome_illumina_differential_expression_alignment` | 4 | `gene_quantification` | `featurecounts` |
| `bulk_transcriptome_illumina_differential_expression_lightweight` | 3 | `transcript_to_gene_summarization` | `tximport` |
| `bulk_transcriptome_illumina_transcript_assembly_guided` | 3 | `alignment_processing` | `samtools` |
| `bulk_transcriptome_illumina_transcript_assembly_guided` | 4 | `transcript_assembly` | `stringtie` |
| `bulk_transcriptome_illumina_transcript_assembly_denovo` | 1 | `transcript_assembly` | `trinity` |
| `bulk_transcriptome_illumina_alternative_splicing` | 3 | `alignment_processing` | `samtools` |
| `bulk_transcriptome_illumina_alternative_splicing` | 4 | `alternative_splicing` | `rmats` |
| `bulk_transcriptome_functional_enrichment` | 1 | `functional_enrichment` | `clusterprofiler` |
| `bulk_transcriptome_pathway_analysis` | 1 | `pathway_analysis` | `fgsea` |
| `virome_illumina_viral_detection` | 1 | `read_preprocessing` | `fastp` |
| `virome_illumina_viral_detection` | 2 | `metagenome_assembly` | `megahit` |
| `virome_illumina_viral_detection` | 3 | `viral_sequence_detection` | `genomad` |
| `virome_illumina_quality_assessment` | 1 | `read_preprocessing` | `fastp` |
| `virome_illumina_quality_assessment` | 2 | `metagenome_assembly` | `megahit` |
| `virome_illumina_quality_assessment` | 3 | `viral_sequence_detection` | `genomad` |
| `virome_illumina_quality_assessment` | 4 | `viral_genome_quality` | `checkv` |
| `virome_illumina_viral_taxonomy` | 1 | `read_preprocessing` | `fastp` |
| `virome_illumina_viral_taxonomy` | 2 | `metagenome_assembly` | `megahit` |
| `virome_illumina_viral_taxonomy` | 3 | `viral_taxonomy` | `genomad` |
| `virome_illumina_host_prediction` | 1 | `read_preprocessing` | `fastp` |
| `virome_illumina_host_prediction` | 2 | `metagenome_assembly` | `megahit` |
| `virome_illumina_host_prediction` | 3 | `viral_sequence_detection` | `genomad` |
| `virome_illumina_host_prediction` | 4 | `viral_genome_quality` | `checkv` |
| `virome_illumina_host_prediction` | 5 | `viral_host_prediction` | `iphop` |
| `virome_illumina_votu_clustering` | 1 | `read_preprocessing` | `fastp` |
| `virome_illumina_votu_clustering` | 2 | `metagenome_assembly` | `megahit` |
| `virome_illumina_votu_clustering` | 3 | `viral_sequence_detection` | `genomad` |
| `virome_illumina_votu_clustering` | 4 | `viral_genome_quality` | `checkv` |
| `virome_illumina_votu_clustering` | 5 | `viral_votu_clustering` | `vclust` |
| `virome_illumina_functional_annotation` | 1 | `read_preprocessing` | `fastp` |
| `virome_illumina_functional_annotation` | 2 | `metagenome_assembly` | `megahit` |
| `virome_illumina_functional_annotation` | 3 | `viral_sequence_detection` | `genomad` |
| `virome_illumina_functional_annotation` | 4 | `viral_genome_quality` | `checkv` |
| `virome_illumina_functional_annotation` | 5 | `viral_gene_prediction` | `prodigal_gv` |
| `virome_illumina_functional_annotation` | 6 | `viral_functional_annotation` | `eggnog_mapper` |
| `virome_illumina_amg_analysis` | 1 | `read_preprocessing` | `fastp` |
| `virome_illumina_amg_analysis` | 2 | `metagenome_assembly` | `megahit` |
| `virome_illumina_amg_analysis` | 3 | `dramv_preparation` | `virsorter2` |
| `virome_illumina_amg_analysis` | 4 | `auxiliary_metabolic_gene_analysis` | `dramv` |
| `eukaryotic_genome_ont_assembly` | 1 | `genome_assembly` | `flye` |
| `eukaryotic_genome_pacbio_assembly` | 1 | `genome_assembly` | `hifiasm` |
| `eukaryotic_genome_illumina_ont_hybrid` | 1 | `hybrid_genome_assembly` | `masurca` |
| `eukaryotic_genome_quality` | 1 | `assembly_qc` | `quast` |
| `eukaryotic_genome_quality` | 2 | `genome_quality_assessment` | `busco` |
| `eukaryotic_genome_repeat_annotation` | 1 | `repeat_discovery` | `repeatmodeler` |
| `eukaryotic_genome_repeat_annotation` | 2 | `repeat_annotation` | `repeatmasker` |
| `eukaryotic_genome_gene_prediction_braker` | 1 | `repeat_discovery` | `repeatmodeler` |
| `eukaryotic_genome_gene_prediction_braker` | 2 | `repeat_annotation` | `repeatmasker` |
| `eukaryotic_genome_gene_prediction_braker` | 3 | `gene_prediction` | `braker4` |
| `eukaryotic_genome_gene_prediction_augustus` | 1 | `repeat_discovery` | `repeatmodeler` |
| `eukaryotic_genome_gene_prediction_augustus` | 2 | `repeat_annotation` | `repeatmasker` |
| `eukaryotic_genome_gene_prediction_augustus` | 3 | `gene_prediction` | `augustus` |
| `eukaryotic_genome_functional_annotation` | 1 | `functional_annotation` | `eggnog_mapper` |
| `eukaryotic_genome_illumina_variant_analysis` | 1 | `read_mapping` | `bwa_mem2` |
| `eukaryotic_genome_illumina_variant_analysis` | 2 | `alignment_processing` | `samtools` |
| `eukaryotic_genome_comparative_genomics` | 1 | `whole_genome_alignment` | `mummer4` |
| `eukaryotic_genome_comparative_genomics` | 2 | `comparative_genomics` | `syri` |
| `metatranscriptome_illumina_host_removal` | 1 | `host_read_removal` | `bowtie2` |
| `metatranscriptome_illumina_rrna_assessment` | 1 | `rrna_depletion_assessment` | `sortmerna` |
| `metatranscriptome_illumina_taxonomy` | 1 | `host_read_removal` | `bowtie2` |
| `metatranscriptome_illumina_taxonomy` | 2 | `rrna_depletion_assessment` | `sortmerna` |
| `metatranscriptome_illumina_differential_expression` | 1 | `host_read_removal` | `bowtie2` |
| `metatranscriptome_illumina_differential_expression` | 2 | `rrna_depletion_assessment` | `sortmerna` |
| `metatranscriptome_illumina_differential_expression` | 3 | `read_mapping` | `bowtie2` |
| `metatranscriptome_illumina_differential_expression` | 4 | `alignment_processing` | `samtools` |
| `metatranscriptome_illumina_differential_expression` | 5 | `gene_quantification` | `featurecounts` |
| `metagenome_illumina_taxonomy_prokaryotic` | 1 | `raw_read_qc` | `fastqc` |
| `metagenome_illumina_taxonomy_eukaryotic` | 1 | `raw_read_qc` | `fastqc` |
| `metagenome_illumina_taxonomy_broad` | 1 | `raw_read_qc` | `fastqc` |
| `amplicon_illumina_alpha_phylogenetic` | 1 | `alpha_diversity` | `qiime2_diversity` |
| `bacterial_illumina_species_identification_gtdbtk` | 1 | `raw_read_qc` | `fastqc` |
| `bacterial_illumina_species_identification_gtdbtk` | 4 | `assembly_qc` | `quast` |
| `bacterial_illumina_species_identification_gtdbtk` | 5 | `species_identification` | `gtdbtk` |
| `bacterial_illumina_species_identification_fastani` | 1 | `raw_read_qc` | `fastqc` |
| `bacterial_illumina_species_identification_fastani` | 4 | `assembly_qc` | `quast` |
| `bacterial_illumina_species_identification_fastani` | 5 | `species_identification` | `fastani` |
| `bacterial_illumina_plasmid_mobsuite` | 1 | `raw_read_qc` | `fastqc` |
| `bacterial_illumina_plasmid_mobsuite` | 4 | `assembly_qc` | `quast` |
| `bacterial_illumina_plasmid_mobsuite` | 5 | `plasmid_detection` | `mobsuite` |
| `bacterial_illumina_plasmid_replicon` | 1 | `raw_read_qc` | `fastqc` |
| `bacterial_illumina_plasmid_replicon` | 4 | `assembly_qc` | `quast` |
| `bacterial_illumina_plasmid_replicon` | 5 | `plasmid_detection` | `plasmidfinder` |
| `bacterial_illumina_plasmid_genomad` | 1 | `raw_read_qc` | `fastqc` |
| `bacterial_illumina_plasmid_genomad` | 4 | `assembly_qc` | `quast` |
| `bacterial_illumina_plasmid_genomad` | 5 | `plasmid_detection` | `genomad` |
| `metagenome_illumina_resistome_deeparg` | 1 | `raw_read_qc` | `fastqc` |
| `metagenome_illumina_resistome_deeparg` | 3 | `resistome_profiling` | `deeparg` |
| `metagenome_illumina_resistome_rgi` | 1 | `raw_read_qc` | `fastqc` |
| `metagenome_illumina_resistome_rgi` | 3 | `resistome_profiling` | `rgi` |
| `metagenome_illumina_resistome_amrplusplus` | 1 | `resistome_profiling` | `amrplusplus` |
| `metagenome_illumina_plasmid_genomad` | 1 | `raw_read_qc` | `fastqc` |
| `metagenome_illumina_plasmid_genomad` | 4 | `plasmid_detection` | `genomad` |
| `metagenome_illumina_plasmid_plasx` | 1 | `raw_read_qc` | `fastqc` |
| `metagenome_illumina_plasmid_plasx` | 4 | `plasmid_detection` | `plasx_workflow` |
| `virome_illumina_viral_abundance_contig` | 1 | `read_preprocessing` | `fastp` |
| `virome_illumina_viral_abundance_contig` | 2 | `metagenome_assembly` | `megahit` |
| `virome_illumina_viral_abundance_contig` | 3 | `viral_sequence_detection` | `genomad` |
| `virome_illumina_viral_abundance_contig` | 4 | `viral_genome_quality` | `checkv` |
| `virome_illumina_viral_abundance_contig` | 5 | `read_mapping` | `bowtie2` |
| `virome_illumina_viral_abundance_contig` | 6 | `alignment_processing` | `samtools` |
| `virome_illumina_viral_abundance_contig` | 7 | `viral_abundance_profiling` | `coverm` |
| `virome_illumina_viral_abundance_votu` | 1 | `read_preprocessing` | `fastp` |
| `virome_illumina_viral_abundance_votu` | 2 | `metagenome_assembly` | `megahit` |
| `virome_illumina_viral_abundance_votu` | 3 | `viral_sequence_detection` | `genomad` |
| `virome_illumina_viral_abundance_votu` | 4 | `viral_genome_quality` | `checkv` |
| `virome_illumina_viral_abundance_votu` | 5 | `viral_votu_clustering` | `vclust` |
| `virome_illumina_viral_abundance_votu` | 6 | `sequence_selection` | `seqkit` |
| `virome_illumina_viral_abundance_votu` | 7 | `read_mapping` | `bowtie2` |
| `virome_illumina_viral_abundance_votu` | 8 | `alignment_processing` | `samtools` |
| `virome_illumina_viral_abundance_votu` | 9 | `viral_abundance_profiling` | `coverm` |
| `metatranscriptome_illumina_functional_isolated` | 1 | `host_read_removal` | `bowtie2` |
| `metatranscriptome_illumina_functional_isolated` | 2 | `rrna_depletion_assessment` | `sortmerna` |
| `metatranscriptome_illumina_functional_isolated` | 3 | `functional_profiling` | `humann` |
| `metatranscriptome_illumina_functional_dna_informed` | 1 | `host_read_removal` | `bowtie2` |
| `metatranscriptome_illumina_functional_dna_informed` | 2 | `rrna_depletion_assessment` | `sortmerna` |
| `metatranscriptome_illumina_functional_dna_informed` | 3 | `functional_profiling` | `humann` |
| `metatranscriptome_illumina_pathways_isolated` | 1 | `host_read_removal` | `bowtie2` |
| `metatranscriptome_illumina_pathways_isolated` | 2 | `rrna_depletion_assessment` | `sortmerna` |
| `metatranscriptome_illumina_pathways_isolated` | 3 | `pathway_analysis` | `humann` |
| `metatranscriptome_illumina_pathways_dna_informed` | 1 | `host_read_removal` | `bowtie2` |
| `metatranscriptome_illumina_pathways_dna_informed` | 2 | `rrna_depletion_assessment` | `sortmerna` |
| `metatranscriptome_illumina_pathways_dna_informed` | 3 | `pathway_analysis` | `humann` |
| `metagenome_illumina_mag_single` | 1 | `raw_read_qc` | `fastqc` |
| `metagenome_illumina_mag_single` | 4 | `assembly_qc` | `quast` |
| `metagenome_illumina_mag_single` | 5 | `read_mapping` | `bowtie2` |
| `metagenome_illumina_mag_single` | 6 | `alignment_processing` | `samtools` |
| `metagenome_illumina_mag_single` | 7 | `coverage_estimation` | `jgi_depth` |
| `metagenome_illumina_mag_single` | 9 | `bin_refinement` | `dastool` |
| `metagenome_illumina_mag_single` | 10 | `mag_quality` | `checkm2` |
| `metagenome_illumina_mag_coassembly` | 1 | `raw_read_qc` | `fastqc` |
| `metagenome_illumina_mag_coassembly` | 4 | `assembly_qc` | `quast` |
| `metagenome_illumina_mag_coassembly` | 5 | `read_mapping` | `bowtie2` |
| `metagenome_illumina_mag_coassembly` | 6 | `alignment_processing` | `samtools` |
| `metagenome_illumina_mag_coassembly` | 7 | `coverage_estimation` | `jgi_depth` |
| `metagenome_illumina_mag_coassembly` | 9 | `bin_refinement` | `dastool` |
| `metagenome_illumina_mag_coassembly` | 10 | `mag_quality` | `checkm2` |

## Operations with shallow alternative coverage

| Operation | Unique tools | Tool IDs |
|---|---:|---|
| `alignment_processing` | 1 | samtools |
| `alternative_splicing` | 1 | rmats |
| `assembly_qc` | 1 | quast |
| `asv_inference` | 1 | dada2 |
| `auxiliary_metabolic_gene_analysis` | 1 | dramv |
| `bin_refinement` | 1 | dastool |
| `comparative_genomics` | 1 | syri |
| `core_genome_alignment` | 1 | panaroo |
| `coverage_estimation` | 1 | jgi_depth |
| `differential_expression` | 2 | deseq2, edger |
| `dramv_preparation` | 1 | virsorter2 |
| `functional_annotation` | 1 | eggnog_mapper |
| `functional_enrichment` | 1 | clusterprofiler |
| `functional_profiling` | 1 | humann |
| `gene_prediction` | 2 | augustus, braker4 |
| `gene_quantification` | 1 | featurecounts |
| `genome_annotation` | 2 | bakta, prokka |
| `genome_quality_assessment` | 1 | busco |
| `host_read_removal` | 1 | bowtie2 |
| `lightweight_quantification` | 2 | kallisto, salmon |
| `mag_quality` | 1 | checkm2 |
| `marker_reconstruction` | 1 | sample2markers |
| `metagenome_assembly` | 2 | megahit, metaspades |
| `mlst_typing` | 2 | mlst, pymlst |
| `otu_clustering` | 2 | mothur, vsearch |
| `pangenome_analysis` | 2 | panaroo, ppanggolin |
| `pathway_analysis` | 2 | fgsea, humann |
| `phylogenetic_inference` | 2 | iqtree2, raxmlng |
| `primer_trimming` | 1 | cutadapt |
| `prophage_detection` | 2 | genomad, phispy |
| `raw_read_qc` | 2 | fastqc, nanoplot |
| `read_mapping` | 2 | bowtie2, bwa_mem2 |
| `repeat_annotation` | 1 | repeatmasker |
| `repeat_discovery` | 1 | repeatmodeler |
| `rna_alignment` | 2 | hisat2, star |
| `rrna_depletion_assessment` | 1 | sortmerna |
| `sequence_selection` | 1 | seqkit |
| `silvangs_input_preparation` | 1 | silvangs_input_prep |
| `species_identification` | 2 | fastani, gtdbtk |
| `strain_profiling` | 2 | instrain, strainphlan |
| `transcript_assembly` | 2 | stringtie, trinity |
| `transcript_to_gene_summarization` | 1 | tximport |
| `variant_calling` | 2 | bcftools, freebayes |
| `variant_filtering` | 1 | bcftools |
| `viral_abundance_profiling` | 1 | coverm |
| `viral_functional_annotation` | 1 | eggnog_mapper |
| `viral_gene_prediction` | 1 | prodigal_gv |
| `viral_genome_quality` | 1 | checkv |
| `viral_host_prediction` | 1 | iphop |
| `viral_quality` | 1 | checkv |
| `viral_sequence_detection` | 2 | genomad, virsorter2 |
| `viral_taxonomy` | 1 | genomad |
| `viral_votu_clustering` | 1 | vclust |
| `whole_genome_alignment` | 1 | mummer4 |

## Structural problems

No unknown workflow candidates or missing tool I/O routes were detected.

## Interpretation

The most important number for product robustness is not raw tool count but the number of constrained single-candidate steps. Those are the places where BioFlow can correctly identify that a tool is unsuitable yet still fail to offer a usable alternative. These should be filled before cosmetic UI work.