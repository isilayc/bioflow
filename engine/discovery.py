import re


# ==================================================
# OPERATION LANGUAGE
# ==================================================

OPERATION_QUERY_ALIASES = {

    "raw_read_qc": [
        "sequencing read quality control",
        "FASTQ quality assessment"
    ],

    "read_preprocessing": [
        "sequencing read trimming",
        "adapter trimming quality filtering"
    ],

    "genome_assembly": [
        "genome assembly",
        "de novo genome assembler"
    ],

    "hybrid_genome_assembly": [
        "hybrid genome assembly",
        "short read long read hybrid assembler"
    ],

    "metagenome_assembly": [
        "metagenome assembly",
        "metagenomic assembler"
    ],

    "assembly_qc": [
        "assembly quality assessment",
        "genome assembly evaluation"
    ],

    "genome_annotation": [
        "genome annotation",
        "prokaryotic genome annotation"
    ],

    "functional_annotation": [
        "functional annotation",
        "protein functional annotation"
    ],

    "taxonomic_profiling": [
        "taxonomic profiling",
        "taxonomic classification"
    ],

    "taxonomy_assignment": [
        "amplicon taxonomic assignment",
        "amplicon taxonomic classification"
    ],

    "amplicon_end_to_end": [
        "amplicon analysis pipeline",
        "marker gene analysis workflow",
        "metabarcoding analysis pipeline"
    ],

    "asv_inference": [
        "amplicon sequence variant inference",
        "ASV denoising"
    ],

    "otu_clustering": [
        "amplicon OTU clustering",
        "operational taxonomic unit clustering",
        "similarity based amplicon clustering"
    ],

    "primer_trimming": [
        "amplicon primer trimming",
        "primer removal"
    ],

    "amplicon_phylogeny": [
        "amplicon phylogeny",
        "phylogenetic tree amplicon"
    ],

    "alpha_diversity": [
        "alpha diversity microbiome",
        "within sample diversity"
    ],

    "beta_diversity": [
        "beta diversity microbiome",
        "community dissimilarity ordination"
    ],

    "differential_abundance": [
        "microbiome differential abundance",
        "compositional differential abundance"
    ],

    "read_mapping": [
        "sequence read mapping",
        "sequence alignment mapping"
    ],

    "alignment_processing": [
        "BAM sorting indexing",
        "alignment processing"
    ],

    "coverage_estimation": [
        "sequence coverage estimation",
        "contig depth estimation"
    ],

    "genome_binning": [
        "metagenomic genome binning",
        "MAG binning"
    ],

    "bin_refinement": [
        "metagenomic bin refinement",
        "consensus MAG refinement"
    ],

    "mag_quality": [
        "MAG quality assessment",
        "genome completeness contamination"
    ],

    "mag_taxonomy": [
        "MAG taxonomy",
        "genome taxonomic classification"
    ],

    "amr_detection": [
        "antimicrobial resistance detection",
        "AMR gene detection"
    ],

    "resistome_profiling": [
        "metagenomic resistome profiling",
        "antimicrobial resistance metagenome"
    ],

    "virulence_profiling": [
        "virulence factor profiling",
        "pathogenicity factor detection"
    ],

    "mlst_typing": [
        "multilocus sequence typing",
        "MLST strain typing"
    ],

    "species_identification": [
        "genome species identification",
        "average nucleotide identity taxonomy"
    ],

    "plasmid_detection": [
        "plasmid detection",
        "plasmid reconstruction"
    ],

    "prophage_detection": [
        "prophage detection",
        "integrated phage prediction"
    ],

    "variant_calling": [
        "variant calling",
        "SNP indel calling"
    ],

    "variant_filtering": [
        "variant filtering",
        "VCF filtering normalization"
    ],

    "pangenome_analysis": [
        "pangenome analysis",
        "pan genome gene family analysis"
    ],

    "core_genome_alignment": [
        "core genome alignment",
        "core gene alignment"
    ],

    "phylogenetic_inference": [
        "phylogenetic inference",
        "maximum likelihood phylogeny"
    ],

    "whole_genome_alignment": [
        "whole genome alignment",
        "genome to genome alignment"
    ],

    "comparative_genomics": [
        "comparative genomics",
        "synteny structural genome comparison"
    ],

    "genome_quality_assessment": [
        "genome completeness assessment",
        "eukaryotic assembly completeness"
    ],

    "repeat_discovery": [
        "de novo repeat discovery",
        "repeat family discovery"
    ],

    "repeat_annotation": [
        "repeat annotation masking",
        "repeat masking"
    ],

    "gene_prediction": [
        "eukaryotic gene prediction",
        "gene model prediction"
    ],

    "transcriptome_indexing": [
        "RNA-seq reference indexing",
        "transcriptome index"
    ],

    "rna_alignment": [
        "RNA-seq alignment",
        "splice aware read alignment"
    ],

    "gene_quantification": [
        "RNA-seq gene quantification",
        "gene read counting"
    ],

    "lightweight_quantification": [
        "RNA-seq lightweight quantification",
        "transcript pseudoalignment quantification"
    ],

    "transcript_to_gene_summarization": [
        "transcript to gene summarization",
        "transcript abundance gene aggregation"
    ],

    "differential_expression": [
        "RNA-seq differential expression",
        "gene expression differential analysis"
    ],

    "transcript_assembly": [
        "transcriptome assembly",
        "transcript reconstruction"
    ],

    "alternative_splicing": [
        "alternative splicing analysis",
        "differential splicing"
    ],

    "functional_enrichment": [
        "functional enrichment analysis",
        "gene ontology enrichment"
    ],

    "pathway_analysis": [
        "pathway analysis",
        "gene set pathway enrichment"
    ],

    "host_read_removal": [
        "host read removal",
        "host depletion bioinformatics"
    ],

    "rrna_depletion_assessment": [
        "rRNA removal assessment",
        "rRNA filtering"
    ],

    "functional_profiling": [
        "metagenomic functional profiling",
        "microbial functional profiling"
    ],

    "strain_profiling": [
        "strain level profiling",
        "microbial strain phylogenomics"
    ],

    "viral_detection": [
        "viral sequence detection",
        "virus identification metagenome"
    ],

    "viral_sequence_detection": [
        "viral sequence detection",
        "virus identification virome"
    ],

    "viral_quality": [
        "viral genome quality assessment",
        "viral completeness contamination"
    ],

    "viral_genome_quality": [
        "viral genome quality assessment",
        "viral completeness contamination"
    ],

    "viral_taxonomy": [
        "viral taxonomic classification",
        "virus taxonomy assignment"
    ],

    "viral_abundance_profiling": [
        "viral abundance profiling",
        "virome abundance estimation"
    ],

    "viral_host_prediction": [
        "virus host prediction",
        "phage host prediction"
    ],

    "viral_votu_clustering": [
        "viral genome clustering vOTU",
        "virus ANI clustering"
    ],

    "viral_gene_prediction": [
        "viral gene prediction",
        "virus ORF prediction"
    ],

    "viral_functional_annotation": [
        "viral functional annotation",
        "virus protein annotation"
    ],

    "auxiliary_metabolic_gene_analysis": [
        "viral auxiliary metabolic gene analysis",
        "AMG analysis virome"
    ],

    "dramv_preparation": [
        "viral sequence preparation DRAM-v",
        "VirSorter2 DRAM-v preparation"
    ]
}


INPUT_KEYWORDS = {

    "raw_read_qc": [
        "fastq",
        "reads"
    ],

    "read_preprocessing": [
        "fastq",
        "reads"
    ],

    "genome_assembly": [
        "fastq",
        "reads"
    ],

    "hybrid_genome_assembly": [
        "fastq",
        "short reads",
        "long reads"
    ],

    "metagenome_assembly": [
        "fastq",
        "reads",
        "metagenomic"
    ],

    "assembly_qc": [
        "fasta",
        "assembly",
        "contig"
    ],

    "genome_annotation": [
        "fasta",
        "genome",
        "contig"
    ],

    "functional_annotation": [
        "protein",
        "fasta",
        "genes"
    ],

    "taxonomic_profiling": [
        "fastq",
        "reads",
        "sequence"
    ],

    "taxonomy_assignment": [
        "representative sequence",
        "fasta",
        "amplicon"
    ],

    "primer_trimming": [
        "fastq",
        "reads",
        "amplicon"
    ],

    "asv_inference": [
        "fastq",
        "amplicon",
        "reads"
    ],

    "otu_clustering": [
        "fastq",
        "fasta",
        "amplicon",
        "reads",
        "sequence"
    ],

    "amplicon_phylogeny": [
        "sequence",
        "fasta",
        "representative"
    ],

    "alpha_diversity": [
        "feature table",
        "otu",
        "asv"
    ],

    "beta_diversity": [
        "feature table",
        "otu",
        "asv"
    ],

    "differential_abundance": [
        "count table",
        "feature table",
        "otu",
        "asv"
    ],

    "read_mapping": [
        "fastq",
        "fasta",
        "reads",
        "reference"
    ],

    "alignment_processing": [
        "sam",
        "bam",
        "alignment"
    ],

    "coverage_estimation": [
        "bam",
        "alignment",
        "contig"
    ],

    "genome_binning": [
        "fasta",
        "contig",
        "coverage",
        "bam"
    ],

    "bin_refinement": [
        "bin",
        "genome",
        "fasta"
    ],

    "mag_quality": [
        "genome",
        "fasta",
        "bin"
    ],

    "mag_taxonomy": [
        "genome",
        "fasta",
        "bin"
    ],

    "amr_detection": [
        "fasta",
        "fastq",
        "genome",
        "contig",
        "protein"
    ],

    "resistome_profiling": [
        "fastq",
        "fasta",
        "reads",
        "contig"
    ],

    "virulence_profiling": [
        "fasta",
        "fastq",
        "genome",
        "contig"
    ],

    "mlst_typing": [
        "fasta",
        "fastq",
        "genome",
        "assembly"
    ],

    "species_identification": [
        "fasta",
        "genome",
        "assembly"
    ],

    "plasmid_detection": [
        "fasta",
        "fastq",
        "assembly",
        "contig"
    ],

    "prophage_detection": [
        "fasta",
        "genbank",
        "genome",
        "assembly"
    ],

    "variant_calling": [
        "bam",
        "cram",
        "fasta",
        "reference"
    ],

    "variant_filtering": [
        "vcf",
        "bcf",
        "variant"
    ],

    "pangenome_analysis": [
        "gff",
        "genome",
        "annotation",
        "genbank"
    ],

    "core_genome_alignment": [
        "gff",
        "genome",
        "alignment",
        "annotation"
    ],

    "phylogenetic_inference": [
        "alignment",
        "fasta",
        "phylip"
    ],

    "viral_sequence_detection": [
        "fasta",
        "contig",
        "assembly"
    ],

    "viral_genome_quality": [
        "viral",
        "fasta",
        "contig"
    ],

    "viral_host_prediction": [
        "viral",
        "fasta",
        "genome"
    ],

    "viral_votu_clustering": [
        "viral",
        "fasta",
        "genome"
    ],

    "rna_alignment": [
        "fastq",
        "rna",
        "reads"
    ],

    "gene_quantification": [
        "bam",
        "gtf",
        "annotation"
    ],

    "lightweight_quantification": [
        "fastq",
        "transcriptome"
    ],

    "differential_expression": [
        "count",
        "matrix",
        "metadata"
    ]
}


# ==================================================
# TEXT UTILITIES
# ==================================================

def normalize_text(
    value
):

    if value is None:
        return ""

    return (
        str(
            value
        )
        .lower()
        .strip()
    )


def normalize_tool_name(
    value
):

    if value is None:
        return ""

    return re.sub(
        r"[^a-z0-9]+",
        "",
        str(
            value
        ).lower()
    )


def unique_values(
    values
):

    result = []
    seen = set()

    for value in values or []:

        if value is None:
            continue

        text = str(
            value
        ).strip()

        if not text:
            continue

        key = text.lower()

        if key in seen:
            continue

        seen.add(
            key
        )

        result.append(
            text
        )

    return result


def join_metadata(
    values
):

    return " ".join(
        normalize_text(
            value
        )
        for value in values or []
        if value
    )


def contains_any(
    text,
    keywords
):

    text = normalize_text(
        text
    )

    for keyword in keywords or []:

        if normalize_text(
            keyword
        ) in text:

            return True

    return False


# ==================================================
# CONTEXT / QUERY FAMILY
# ==================================================

def _marker_from_context(
    context
):

    if not isinstance(
        context,
        dict
    ):

        return None

    explicit_marker = (
        context.get(
            "marker"
        )
    )

    if explicit_marker:

        explicit_marker = str(
            explicit_marker
        ).strip()

        if explicit_marker.lower() == "16s":

            return "16S rRNA"

        if explicit_marker.lower() == "18s":

            return "18S rRNA"

        return explicit_marker

    combined = " ".join(
        str(
            context.get(
                field,
                ""
            )
        )
        for field in [
            "goal",
            "sample_type"
        ]
    ).lower()

    for marker in [
        "16s",
        "18s",
        "its",
        "coi"
    ]:

        if marker in combined:

            if marker == "16s":
                return "16S rRNA"

            if marker == "18s":
                return "18S rRNA"

            return marker.upper()

    return None


def _sample_phrase(
    context
):

    if not isinstance(
        context,
        dict
    ):

        return ""

    value = (
        context.get(
            "sample_type"
        )
        or
        ""
    )

    return str(
        value
    ).strip()


def _goal_phrase(
    context
):

    if not isinstance(
        context,
        dict
    ):

        return ""

    value = (
        context.get(
            "goal"
        )
        or
        ""
    )

    return str(
        value
    ).strip()


def get_discovery_query_family(
    operation,
    context=None,
    max_queries=8
):
    """
    Generate complementary discovery queries instead of
    relying on one manually chosen phrase.

    The family intentionally contains:
      - operation language
      - biological/sample context
      - goal language
      - pipeline/framework language
      - online/web-service language

    This is what allows resources described as integrated
    pipelines or web services to compete with standalone
    command-line tools in discovery.
    """

    aliases = (
        OPERATION_QUERY_ALIASES.get(
            operation
        )
        or
        [
            str(
                operation
            ).replace(
                "_",
                " "
            )
        ]
    )

    sample_type = _sample_phrase(
        context
    )

    goal = _goal_phrase(
        context
    )

    marker = _marker_from_context(
        context
    )

    queries = []

    queries.extend(
        aliases[
            :2
        ]
    )

    primary = aliases[
        0
    ]

    feature_strategy = normalize_text(
        (
            context
            or
            {}
        ).get(
            "feature_strategy"
        )
    )

    if feature_strategy in (
        "asv",
        "otu",
        "motu"
    ):

        queries.append(
            f"{feature_strategy.upper()} {primary}"
        )

        if operation == "taxonomy_assignment":

            queries.append(
                f"{feature_strategy.upper()} taxonomic classification"
            )

    if sample_type:

        if (
            normalize_text(
                sample_type
            )
            not in
            normalize_text(
                primary
            )
        ):

            queries.append(
                f"{sample_type} {primary}"
            )

    if goal:

        queries.append(
            f"{goal} software"
        )

        queries.append(
            f"{goal} pipeline"
        )

    if marker:

        queries.append(
            f"{marker} {primary}"
        )

        queries.append(
            f"{marker} analysis software"
        )

        queries.append(
            f"{marker} analysis pipeline"
        )

        queries.append(
            f"{marker} web server"
        )

        if operation in (
            "taxonomy_assignment",
            "taxonomic_profiling"
        ):

            queries.append(
                f"{marker} taxonomic classification pipeline"
            )

    else:

        queries.append(
            f"{primary} software"
        )

        queries.append(
            f"{primary} pipeline"
        )

        queries.append(
            f"{primary} web server"
        )

    if (
        sample_type
        and
        goal
    ):

        queries.append(
            f"{sample_type} {goal} workflow"
        )

    return unique_values(
        queries
    )[
        :max(
            1,
            int(
                max_queries
            )
        )
    ]


def get_discovery_search_term(
    operation,
    context=None
):
    """
    Backward-compatible primary query.
    """

    family = get_discovery_query_family(
        operation,
        context=context,
        max_queries=1
    )

    if family:

        return family[
            0
        ]

    return str(
        operation
    ).replace(
        "_",
        " "
    )


# ==================================================
# RESOURCE-TYPE NORMALIZATION
# ==================================================

def infer_resource_type(
    tool
):
    """
    Normalize resource presentation into a small BioFlow
    taxonomy without pretending all candidates are CLI tools.
    """

    resource_types = [
        normalize_text(
            value
        )
        for value in (
            tool.get(
                "resource_types",
                []
            )
            or
            []
        )
    ]

    text = " ".join(
        [
            normalize_text(
                tool.get(
                    "name"
                )
            ),
            normalize_text(
                tool.get(
                    "description"
                )
            ),
            " ".join(
                resource_types
            )
        ]
    )

    if (
        "web application"
        in text
        or
        "web server"
        in text
        or
        "web service"
        in text
        or
        "online service"
        in text
    ):

        return "web_service"

    if (
        "workflow"
        in text
        or
        "pipeline"
        in text
    ):

        return "pipeline"

    if (
        "framework"
        in text
    ):

        return "framework"

    if (
        "database"
        in text
        and
        "software"
        not in text
        and
        "tool"
        not in text
    ):

        return "database"

    if (
        "library"
        in text
        or
        "package"
        in text
    ):

        return "package"

    if (
        "desktop application"
        in text
        or
        "desktop"
        in text
    ):

        return "desktop_application"

    return "software_tool"


# ==================================================
# REMOVE CURATED DUPLICATES
# ==================================================

def remove_existing_tools(
    discovered_tools,
    curated_tools
):

    curated_names = {
        normalize_tool_name(
            tool.get(
                "name"
            )
        )
        for tool in curated_tools or []
        if tool.get(
            "name"
        )
    }

    results = []

    for tool in discovered_tools or []:

        name = normalize_tool_name(
            tool.get(
                "name"
            )
        )

        if (
            name
            and
            name not in curated_names
        ):

            results.append(
                tool
            )

    return results


# ==================================================
# LITERATURE CANDIDATE EXTRACTION
# ==================================================

GENERIC_ENTITY_STOPWORDS = {
    "analysis",
    "automatic",
    "both",
    "our",
    "package",
    "packages",
    "platform",
    "platforms",
    "method",
    "methods",
    "workflow",
    "workflows",
    "pipeline",
    "pipelines",
    "miseq",
    "novaseq",
    "hiseq",
    "nextseq",
    "miniseq",
    "illumina",
    "nanopore",
    "pacbio",
    "ont",
    "a",
    "an",
    "and",
    "as",
    "by",
    "for",
    "from",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "was",
    "were",
    "with",
    "approach",
    "algorithm",
    "amplicon",
    "assembly",
    "bacteria",
    "bacterial",
    "classifier",
    "classification",
    "community",
    "database",
    "dna",
    "fasta",
    "fastq",
    "gene",
    "genome",
    "genomic",
    "illumina",
    "method",
    "methods",
    "microbiome",
    "pipeline",
    "protein",
    "pubmed",
    "rna",
    "rrna",
    "sequence",
    "sequencing",
    "service",
    "software",
    "study",
    "tool",
    "tools",
    "web",
    "workflow",
    "server",
    "reads",
    "samples",
    "data",
    "otu",
    "otus",
    "asv",
    "asvs",
    "pcr",
    "ngs",
    "blast",
    "blastn"
}


def _clean_candidate_name(
    value
):

    if not value:
        return None

    value = str(
        value
    ).strip()

    value = re.sub(
        r"^[\(\[\{\"']+|[\)\]\}\"',;:.]+$",
        "",
        value
    ).strip()

    value = re.sub(
        r"\s+v(?:ersion)?\.?\s*\d+(?:\.\d+)*$",
        "",
        value,
        flags=re.IGNORECASE
    ).strip()

    if not value:
        return None

    if len(
        value
    ) > 60:

        return None

    if len(
        value
    ) < 2:

        return None

    normalized = normalize_text(
        value
    )

    if normalized in GENERIC_ENTITY_STOPWORDS:

        return None

    if re.fullmatch(
        r"\d+(?:\.\d+)*",
        value
    ):

        return None

    words = value.split()

    if len(
        words
    ) > 4:

        return None

    if all(
        normalize_text(
            word
        )
        in
        GENERIC_ENTITY_STOPWORDS
        for word
        in words
    ):

        return None

    return value


def _candidate_context_type(
    context_text
):

    text = normalize_text(
        context_text
    )

    if (
        "web server"
        in text
        or
        "web service"
        in text
        or
        "online"
        in text
        or
        "data analysis service"
        in text
    ):

        return "web_service"

    if (
        "pipeline"
        in text
        or
        "workflow"
        in text
    ):

        return "pipeline"

    if (
        "framework"
        in text
    ):

        return "framework"

    if (
        "package"
        in text
        or
        "library"
        in text
    ):

        return "package"

    if "database" in text:

        return "database"

    return "software_tool"


def extract_candidate_mentions_from_paper(
    paper
):
    """
    Conservative heuristic extraction of software/resource names
    from titles and abstracts.

    These are deliberately labelled as literature leads rather than
    automatically approved tools. Their purpose is to expose candidates
    that a registry-only search may miss.
    """

    title = (
        paper.get(
            "title"
        )
        or
        ""
    )

    abstract = (
        paper.get(
            "abstract"
        )
        or
        ""
    )

    combined = (
        f"{title}. {abstract}"
    )

    mentions = []

    patterns = [
        # "using SILVAngs", "processed by mothur", "submitted to QIIME2"
        r"(?i)\b(?:using|submitted\s+to|processed\s+by|analysed\s+using|analyzed\s+using)\s+(?:the\s+)?([A-Za-z][A-Za-z0-9._+\-]{1,35})",

        # "SILVAngs pipeline", "mothur software", "Galaxy platform"
        r"\b([A-Za-z][A-Za-z0-9._+\-]{1,35})\s+(?:data\s+analysis\s+)?(?:software|pipeline|tool|package|framework|platform|web\s+server|web\s+service|service)\b",

        # "pipeline of the SILVAngs ..."
        r"(?i)\b(?:software|pipeline|tool|package|framework|platform|web\s+server|web\s+service)\s+(?:called\s+|named\s+|of\s+the\s+|of\s+)?([A-Za-z][A-Za-z0-9._+\-]{1,35})\b"
    ]

    for pattern in patterns:

        for match in re.finditer(
            pattern,
            combined
        ):

            name = _clean_candidate_name(
                match.group(
                    1
                )
            )

            if not name:
                continue

            start = max(
                0,
                match.start()
                -
                90
            )

            end = min(
                len(
                    combined
                ),
                match.end()
                +
                90
            )

            context_text = combined[
                start:end
            ]

            matched_phrase = (
                match.group(
                    0
                )
            )

            explicit_resource_language = contains_any(
                matched_phrase,
                [
                    "software",
                    "pipeline",
                    "tool",
                    "package",
                    "framework",
                    "platform",
                    "web server",
                    "web service",
                    "service"
                ]
            )

            extraction_strength = (
                "strong"
                if explicit_resource_language
                else
                "weak"
            )

            mentions.append(
                {
                    "name": name,
                    "resource_type": (
                        _candidate_context_type(
                            matched_phrase
                        )
                    ),
                    "context": context_text.strip(),
                    "extraction_strength": extraction_strength
                }
            )

    # Lists in reviews/comparison papers often expose resources
    # that a registry-only search misses:
    # "pipelines including QIIME, mothur, SILVAngs and MG-RAST"
    list_pattern = re.compile(
        r"(?i)\b(?:tools?|pipelines?|software|resources?|web\s+servers?|"
        r"platforms?|frameworks?)\b[^.;:]{0,40}"
        r"(?:including|such\s+as|e\.g\.?[,]?)\s+([^.;]{2,180})"
    )

    for list_match in list_pattern.finditer(
        combined
    ):

        list_text = list_match.group(
            1
        )

        pieces = re.split(
            r"\s*,\s*|\s+and\s+|\s+or\s+",
            list_text
        )

        for piece in pieces:

            piece = re.sub(
                r"\([^)]*\)",
                "",
                piece
            ).strip()

            piece = re.sub(
                r"\b(?:version|v)\.?\s*\d+(?:\.\d+)*.*$",
                "",
                piece,
                flags=re.IGNORECASE
            ).strip()

            # Keep only short name-like phrases.
            if not re.fullmatch(
                r"[A-Za-z][A-Za-z0-9._+\-]*(?:\s+[A-Za-z0-9._+\-]+){0,2}",
                piece
            ):

                continue

            name = _clean_candidate_name(
                piece
            )

            if not name:
                continue

            mentions.append(
                {
                    "name": name,
                    "resource_type": "software_tool",
                    "context": list_match.group(
                        0
                    ).strip(),
                    "extraction_strength": "strong"
                }
            )

    # Method/software titles often use "ToolName: description"
    if ":" in title:

        prefix, suffix = title.split(
            ":",
            1
        )

        if contains_any(
            suffix,
            [
                "software",
                "pipeline",
                "tool",
                "workflow",
                "platform",
                "package",
                "method",
                "analysis"
            ]
        ):

            name = _clean_candidate_name(
                prefix
            )

            if name:

                mentions.append(
                    {
                        "name": name,
                        "resource_type": (
                            _candidate_context_type(
                                suffix
                            )
                        ),
                        "context": title,
                        "extraction_strength": "strong"
                    }
                )

    # Deduplicate within the paper
    result = []
    seen = set()

    for mention in mentions:

        key = normalize_tool_name(
            mention[
                "name"
            ]
        )

        if not key:
            continue

        if key in seen:
            continue

        seen.add(
            key
        )

        result.append(
            mention
        )

    return result


def extract_literature_candidates(
    papers
):
    """
    Convert candidate mentions from discovery literature into
    unverified BioFlow discovery records.
    """

    merged = {}

    for paper in papers or []:

        mentions = extract_candidate_mentions_from_paper(
            paper
        )

        for mention in mentions:

            key = normalize_tool_name(
                mention[
                    "name"
                ]
            )

            if not key:
                continue

            provider_names = (
                paper.get(
                    "source_providers",
                    []
                )
                or
                []
            )

            paper_ref = {
                "title": paper.get(
                    "title"
                ),
                "extraction_strength": mention.get(
                    "extraction_strength",
                    "weak"
                ),
                "year": paper.get(
                    "year"
                ),
                "doi_url": paper.get(
                    "doi_url"
                ),
                "pubmed_url": paper.get(
                    "pubmed_url"
                ),
                "europepmc_url": paper.get(
                    "europepmc_url"
                ),
                "openalex_url": paper.get(
                    "openalex_url"
                ),
                "providers": provider_names,
                "context": mention.get(
                    "context"
                )
            }

            if key not in merged:

                merged[
                    key
                ] = {
                    "name": mention[
                        "name"
                    ],
                    "biotools_id": None,
                    "description": (
                        "Candidate resource name extracted from "
                        "method/application literature. This is a "
                        "literature lead and requires capability review."
                    ),
                    "homepage": None,
                    "operations": [],
                    "topics": [],
                    "input_data": [],
                    "input_formats": [],
                    "output_data": [],
                    "output_formats": [],
                    "publication_count": 0,
                    "publications": [],
                    "resource_types": [
                        mention[
                            "resource_type"
                        ]
                    ],
                    "operating_systems": [],
                    "languages": [],
                    "biotools_url": None,
                    "discovery_sources": [
                        "literature"
                    ],
                    "query_matches": [],
                    "source_provenance": [],
                    "literature_mentions": []
                }

            item = merged[
                key
            ]

            item[
                "resource_types"
            ] = unique_values(
                item.get(
                    "resource_types",
                    []
                )
                +
                [
                    mention[
                        "resource_type"
                    ]
                ]
            )

            item[
                "literature_mentions"
            ].append(
                paper_ref
            )

            item[
                "publication_count"
            ] = len(
                item[
                    "literature_mentions"
                ]
            )

            for provider in provider_names:

                item[
                    "source_provenance"
                ].append(
                    {
                        "source": provider,
                        "query": (
                            "; ".join(
                                paper.get(
                                    "search_queries",
                                    []
                                )
                                or
                                []
                            )
                        ),
                        "url": (
                            paper.get(
                                "doi_url"
                            )
                            or
                            paper.get(
                                "pubmed_url"
                            )
                            or
                            paper.get(
                                "europepmc_url"
                            )
                            or
                            paper.get(
                                "openalex_url"
                            )
                        )
                    }
                )

    # --------------------------------------------------
    # QUALITY FILTER FOR LITERATURE-ONLY ENTITY EXTRACTION
    # --------------------------------------------------
    #
    # A broad abstract-mining regex can otherwise turn ordinary words
    # ("both", "our", sequencing platform names, etc.) into fake tools.
    #
    # Keep a literature lead if:
    #   A) it was extracted from explicit software/tool/pipeline language,
    #      OR
    #   B) it was independently mentioned in at least two papers.
    #
    # Registry hits are merged later and are not lost by this filter.
    #
    filtered = []

    for item in merged.values():

        mentions = (
            item.get(
                "literature_mentions",
                []
            )
            or
            []
        )

        strong_mention = any(
            mention.get(
                "extraction_strength"
            )
            ==
            "strong"
            for mention in mentions
            if isinstance(
                mention,
                dict
            )
        )

        if (
            strong_mention
            or
            len(
                mentions
            )
            >=
            2
        ):

            filtered.append(
                item
            )

    results = filtered

    results.sort(
        key=lambda item: (
            len(
                item.get(
                    "literature_mentions",
                    []
                )
            ),
            len(
                {
                    provenance.get(
                        "source"
                    )
                    for provenance
                    in item.get(
                        "source_provenance",
                        []
                    )
                    if provenance.get(
                        "source"
                    )
                }
            )
        ),
        reverse=True
    )

    return results


# ==================================================
# SOURCE MERGING
# ==================================================

def merge_discovery_sources(
    registry_candidates,
    literature_candidates
):
    """
    Merge registry-discovered and literature-discovered
    candidates by normalized resource name.
    """

    merged = {}

    for candidate in (
        list(
            registry_candidates
            or
            []
        )
        +
        list(
            literature_candidates
            or
            []
        )
    ):

        name = candidate.get(
            "name"
        )

        key = normalize_tool_name(
            name
        )

        if not key:
            continue

        if key not in merged:

            merged[
                key
            ] = candidate.copy()

            continue

        current = merged[
            key
        ]

        list_fields = [
            "operations",
            "topics",
            "input_data",
            "input_formats",
            "output_data",
            "output_formats",
            "resource_types",
            "operating_systems",
            "languages",
            "discovery_sources",
            "query_matches",
            "literature_mentions"
        ]

        for field in list_fields:

            left = (
                current.get(
                    field,
                    []
                )
                or
                []
            )

            right = (
                candidate.get(
                    field,
                    []
                )
                or
                []
            )

            if field == "literature_mentions":

                # dict objects: preserve by title/year/url tuple
                seen = set()
                combined = []

                for item in left + right:

                    if not isinstance(
                        item,
                        dict
                    ):
                        continue

                    item_key = (
                        item.get(
                            "title"
                        ),
                        item.get(
                            "year"
                        ),
                        item.get(
                            "doi_url"
                        )
                        or
                        item.get(
                            "pubmed_url"
                        )
                    )

                    if item_key in seen:
                        continue

                    seen.add(
                        item_key
                    )

                    combined.append(
                        item
                    )

                current[
                    field
                ] = combined

            else:

                current[
                    field
                ] = unique_values(
                    left
                    +
                    right
                )

        current[
            "source_provenance"
        ] = (
            current.get(
                "source_provenance",
                []
            )
            or
            []
        ) + (
            candidate.get(
                "source_provenance",
                []
            )
            or
            []
        )

        for field in [
            "biotools_id",
            "biotools_url",
            "homepage",
            "description"
        ]:

            if (
                not current.get(
                    field
                )
                and
                candidate.get(
                    field
                )
            ):

                current[
                    field
                ] = candidate[
                    field
                ]

        current[
            "publication_count"
        ] = max(
            current.get(
                "publication_count",
                0
            )
            or
            0,
            candidate.get(
                "publication_count",
                0
            )
            or
            0,
            len(
                current.get(
                    "literature_mentions",
                    []
                )
            )
        )

    return list(
        merged.values()
    )


# ==================================================
# DISCOVERY SCREENING
# ==================================================

def _context_keywords(
    context
):

    if not isinstance(
        context,
        dict
    ):
        return []

    values = []

    for field in [
        "sample_type",
        "sequencing",
        "read_type",
        "goal"
    ]:

        value = context.get(
            field
        )

        if isinstance(
            value,
            list
        ):

            values.extend(
                value
            )

        elif value:

            values.append(
                value
            )

    marker = _marker_from_context(
        context
    )

    if marker:

        values.append(
            marker
        )

    return unique_values(
        values
    )


def score_discovered_tool(
    tool,
    operation,
    context=None
):
    """
    Research Engine v2 discovery confidence.

    This is a screening confidence score, NOT scientific approval.
    """

    reasons = []

    aliases = (
        OPERATION_QUERY_ALIASES.get(
            operation
        )
        or
        [
            str(
                operation
            ).replace(
                "_",
                " "
            )
        ]
    )

    operation_text = join_metadata(
        tool.get(
            "operations",
            []
        )
    )

    description = normalize_text(
        tool.get(
            "description"
        )
    )

    literature_context = " ".join(
        normalize_text(
            item.get(
                "context"
            )
        )
        for item in (
            tool.get(
                "literature_mentions",
                []
            )
            or
            []
        )
        if isinstance(
            item,
            dict
        )
    )

    operation_match = contains_any(
        operation_text,
        aliases
    )

    description_match = (
        contains_any(
            description,
            aliases
        )
        or
        contains_any(
            literature_context,
            aliases
        )
    )

    if operation_match:

        operation_score = 40

        reasons.append(
            "Registered operation matches the BioFlow step."
        )

    elif description_match:

        operation_score = 28

        reasons.append(
            "Description/literature context appears relevant to the BioFlow step."
        )

    elif (
        "literature"
        in
        (
            tool.get(
                "discovery_sources",
                []
            )
            or
            []
        )
    ):

        operation_score = 18

        reasons.append(
            "The candidate was extracted from operation-context literature but lacks structured capability metadata."
        )

    else:

        operation_score = 5

        reasons.append(
            "No strong operation match was found."
        )

    expected_inputs = (
        INPUT_KEYWORDS.get(
            operation,
            []
        )
    )

    input_metadata = (
        (
            tool.get(
                "input_data",
                []
            )
            or
            []
        )
        +
        (
            tool.get(
                "input_formats",
                []
            )
            or
            []
        )
    )

    input_text = join_metadata(
        input_metadata
    )

    if not expected_inputs:

        input_score = 8

    elif not input_metadata:

        input_score = 5

        reasons.append(
            "Input compatibility is not yet verified."
        )

    elif contains_any(
        input_text,
        expected_inputs
    ):

        input_score = 15

        reasons.append(
            "Registered input metadata appears compatible."
        )

    else:

        input_score = 0

        reasons.append(
            "Registered inputs do not clearly match the expected data."
        )

    context_keywords = _context_keywords(
        context
    )

    context_text = " ".join(
        [
            join_metadata(
                tool.get(
                    "topics",
                    []
                )
            ),
            description,
            literature_context
        ]
    )

    if not context_keywords:

        context_score = 6

    else:

        matched_context = [
            keyword
            for keyword in context_keywords
            if normalize_text(
                keyword
            )
            in context_text
        ]

        if len(
            matched_context
        ) >= 2:

            context_score = 10

            reasons.append(
                "Multiple biological/context terms match the selected analysis."
            )

        elif matched_context:

            context_score = 7

            reasons.append(
                "At least one selected context term matches."
            )

        else:

            context_score = 2

            reasons.append(
                "Biological context match is weak or missing."
            )

    query_matches = (
        tool.get(
            "query_matches",
            []
        )
        or
        []
    )

    query_count = len(
        set(
            normalize_text(
                value
            )
            for value in query_matches
            if value
        )
    )

    query_coverage_score = min(
        15,
        query_count
        *
        5
    )

    if query_count >= 2:

        reasons.append(
            f"Recovered by {query_count} independent registry queries."
        )

    literature_mentions = (
        tool.get(
            "literature_mentions",
            []
        )
        or
        []
    )

    literature_provider_names = set()

    for item in literature_mentions:

        if not isinstance(
            item,
            dict
        ):
            continue

        for provider in item.get(
            "providers",
            []
        ) or []:

            literature_provider_names.add(
                provider
            )

    registry_publications = (
        tool.get(
            "publication_count",
            0
        )
        or
        0
    )

    evidence_score = 0

    if registry_publications >= 3:

        evidence_score += 8

    elif registry_publications >= 1:

        evidence_score += 5

    if literature_mentions:

        evidence_score += min(
            5,
            len(
                literature_mentions
            )
            *
            2
        )

    if len(
        literature_provider_names
    ) >= 2:

        evidence_score += 2

        reasons.append(
            "The candidate is visible through multiple literature providers."
        )

    evidence_score = min(
        15,
        evidence_score
    )

    metadata_score = 0

    if tool.get(
        "description"
    ):
        metadata_score += 1

    if tool.get(
        "operations"
    ):
        metadata_score += 1

    if tool.get(
        "biotools_id"
    ):
        metadata_score += 1

    if input_metadata:
        metadata_score += 1

    if (
        tool.get(
            "homepage"
        )
        or
        tool.get(
            "biotools_url"
        )
    ):
        metadata_score += 1

    total = min(
        100,
        (
            operation_score
            +
            input_score
            +
            context_score
            +
            query_coverage_score
            +
            evidence_score
            +
            metadata_score
        )
    )

    resource_type = infer_resource_type(
        tool
    )

    sources = (
        tool.get(
            "discovery_sources",
            []
        )
        or
        []
    )

    if (
        "bio.tools"
        in sources
        and
        "literature"
        in sources
    ):

        verification_state = (
            "registry_plus_literature"
        )

    elif "bio.tools" in sources:

        verification_state = (
            "registry_only"
        )

    else:

        verification_state = (
            "literature_lead"
        )

    if total >= 70:

        label = "Likely relevant"
        status = "likely"

    elif total >= 50:

        label = "Needs review"
        status = "review"

    else:

        label = "Low confidence"
        status = "low"

    return {
        "total": total,
        "label": label,
        "status": status,
        "operation_score": operation_score,
        "input_score": input_score,
        "context_score": context_score,
        "query_coverage_score": query_coverage_score,
        "evidence_score": evidence_score,
        "metadata_score": metadata_score,
        "resource_type": resource_type,
        "verification_state": verification_state,
        "reasons": reasons
    }


def screen_discovered_tools(
    discovered_tools,
    operation,
    context=None
):
    """
    Score and sort all discovered candidates.
    """

    screened = []

    for tool in discovered_tools or []:

        tool_copy = tool.copy()

        tool_copy[
            "discovery_score"
        ] = score_discovered_tool(
            tool_copy,
            operation,
            context=context
        )

        screened.append(
            tool_copy
        )

    screened.sort(
        key=lambda tool: (
            tool.get(
                "discovery_score",
                {}
            ).get(
                "total",
                0
            ),
            len(
                tool.get(
                    "discovery_sources",
                    []
                )
                or
                []
            ),
            len(
                tool.get(
                    "query_matches",
                    []
                )
                or
                []
            ),
            tool.get(
                "publication_count",
                0
            )
            or
            0
        ),
        reverse=True
    )

    return screened
