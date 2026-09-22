from __future__ import annotations

from copy import deepcopy
import re


RAW_READS = "raw_reads"
GENOME_ASSEMBLY = "genome_assembly"
PREDICTED_PROTEINS = "predicted_proteins"

METAGENOME_CONTIGS = "metagenome_contigs"
VIRAL_FASTA = "viral_fasta"

GENE_COUNT_MATRIX = "gene_count_matrix"
SIGNIFICANT_GENE_LIST = "significant_gene_list"
RANKED_GENE_LIST = "ranked_gene_list"


GENOME_SAMPLE_TYPES = {
    "Bacterial isolate",
    "Eukaryotic genome",
}


_DATA_STATE_OPTIONS = {
    "Bacterial isolate": [
        {"id": RAW_READS, "label": "Raw sequencing reads"},
        {"id": GENOME_ASSEMBLY, "label": "Genome assembly FASTA"},
    ],
    "Eukaryotic genome": [
        {"id": RAW_READS, "label": "Raw sequencing reads"},
        {"id": GENOME_ASSEMBLY, "label": "Genome assembly FASTA"},
        {"id": PREDICTED_PROTEINS, "label": "Predicted protein FASTA"},
    ],
    "Metagenome": [
        {"id": RAW_READS, "label": "Raw sequencing reads"},
        {"id": METAGENOME_CONTIGS, "label": "Assembled metagenome contigs FASTA"},
    ],
    "Virome": [
        {"id": RAW_READS, "label": "Raw sequencing reads"},
        {"id": VIRAL_FASTA, "label": "Viral sequences FASTA"},
    ],
    "Bulk transcriptome": [
        {"id": RAW_READS, "label": "Raw RNA-seq reads"},
        {"id": GENE_COUNT_MATRIX, "label": "Gene count matrix"},
        {"id": SIGNIFICANT_GENE_LIST, "label": "Significant gene list"},
        {"id": RANKED_GENE_LIST, "label": "Ranked gene list"},
    ],
}


_ROUTE_SPECS = {
    ("Eukaryotic genome", GENOME_ASSEMBLY): {
        "Genome quality assessment": [
            {
                "template_id": "eukaryotic_genome_quality",
                "external_inputs": [
                    "eukaryotic_genome_fasta",
                    "busco_lineage_database",
                ],
                "remove_operations": [],
            },
        ],
        "Repeat annotation": [
            {
                "template_id": "eukaryotic_genome_repeat_annotation",
                "external_inputs": ["eukaryotic_genome_fasta"],
                "remove_operations": [],
            },
        ],
        "Gene prediction": [
            {
                "template_id": "eukaryotic_genome_gene_prediction_braker",
                "external_inputs": [
                    "eukaryotic_genome_fasta",
                    "protein_evidence_fasta",
                ],
                "remove_operations": [],
            },
            {
                "template_id": "eukaryotic_genome_gene_prediction_augustus",
                "external_inputs": [
                    "eukaryotic_genome_fasta",
                    "augustus_species_model",
                ],
                "remove_operations": [],
            },
        ],
        "Comparative genomics": [
            {
                "template_id": "eukaryotic_genome_comparative_genomics",
                "external_inputs": [
                    "reference_eukaryotic_genome_fasta",
                    "query_eukaryotic_genome_fasta",
                ],
                "remove_operations": [],
            },
        ],
    },

    ("Eukaryotic genome", PREDICTED_PROTEINS): {
        "Functional annotation": [
            {
                "template_id": "eukaryotic_genome_functional_annotation",
                "external_inputs": [
                    "eukaryotic_protein_fasta",
                    "orthology_database",
                ],
                "remove_operations": [],
            },
        ],
    },

    ("Bacterial isolate", GENOME_ASSEMBLY): {
        "Whole genome characterization": [
            {
                "template_id": "bacterial_illumina_wgs",
                "external_inputs": ["genome_fasta"],
                "remove_operations": [
                    "raw_read_qc",
                    "read_preprocessing",
                    "genome_assembly",
                ],
            },
        ],
        "Species identification": [
            {
                "template_id": "bacterial_illumina_species_identification_gtdbtk",
                "external_inputs": ["genome_fasta"],
                "remove_operations": [
                    "raw_read_qc",
                    "read_preprocessing",
                    "genome_assembly",
                ],
            },
        ],
        "Antimicrobial resistance detection": [
            {
                "template_id": "bacterial_illumina_amr",
                "external_inputs": ["genome_fasta"],
                "remove_operations": [
                    "raw_read_qc",
                    "read_preprocessing",
                    "genome_assembly",
                    "assembly_qc",
                ],
            },
        ],
        "Virulence profiling": [
            {
                "template_id": "bacterial_illumina_virulence",
                "external_inputs": ["genome_fasta"],
                "remove_operations": [
                    "raw_read_qc",
                    "read_preprocessing",
                    "genome_assembly",
                    "assembly_qc",
                ],
            },
        ],
        "MLST / strain typing": [
            {
                "template_id": "bacterial_illumina_mlst",
                "external_inputs": ["genome_fasta"],
                "remove_operations": [
                    "raw_read_qc",
                    "read_preprocessing",
                    "genome_assembly",
                    "assembly_qc",
                ],
            },
        ],
        "Prophage detection": [
            {
                "template_id": "bacterial_illumina_prophage",
                "external_inputs": ["genome_fasta"],
                "remove_operations": [
                    "raw_read_qc",
                    "read_preprocessing",
                    "genome_assembly",
                    "assembly_qc",
                ],
            },
        ],
        "Plasmid detection": [
            {
                "template_id": "bacterial_illumina_plasmid_mobsuite",
                "external_inputs": ["genome_fasta"],
                "remove_operations": [
                    "raw_read_qc",
                    "read_preprocessing",
                    "genome_assembly",
                    "assembly_qc",
                ],
            },
            {
                "template_id": "bacterial_illumina_plasmid_replicon",
                "external_inputs": ["genome_fasta"],
                "remove_operations": [
                    "raw_read_qc",
                    "read_preprocessing",
                    "genome_assembly",
                    "assembly_qc",
                ],
            },
            {
                "template_id": "bacterial_illumina_plasmid_genomad",
                "external_inputs": ["genome_fasta"],
                "remove_operations": [
                    "raw_read_qc",
                    "read_preprocessing",
                    "genome_assembly",
                    "assembly_qc",
                ],
            },
        ],
    },

    ("Metagenome", METAGENOME_CONTIGS): {
        "Virulence profiling": [
            {
                "template_id": "metagenome_illumina_virulence",
                "external_inputs": ["metagenome_contigs_fasta"],
                "remove_operations": [
                    "raw_read_qc",
                    "read_preprocessing",
                    "metagenome_assembly",
                ],
            },
        ],
        "Viral analysis": [
            {
                "template_id": "metagenome_illumina_viral",
                "external_inputs": ["metagenome_contigs_fasta"],
                "remove_operations": [
                    "raw_read_qc",
                    "read_preprocessing",
                    "metagenome_assembly",
                ],
            },
        ],
        "Plasmid analysis": [
            {
                "template_id": "metagenome_illumina_plasmid_genomad",
                "external_inputs": ["metagenome_contigs_fasta"],
                "remove_operations": [
                    "raw_read_qc",
                    "read_preprocessing",
                    "metagenome_assembly",
                ],
            },
            {
                "template_id": "metagenome_illumina_plasmid_plasx",
                "external_inputs": ["metagenome_contigs_fasta"],
                "remove_operations": [
                    "raw_read_qc",
                    "read_preprocessing",
                    "metagenome_assembly",
                ],
            },
        ],
    },

    ("Virome", VIRAL_FASTA): {
        "Viral genome quality assessment": [
            {
                "template_id": "virome_illumina_quality_assessment",
                "external_inputs": ["viral_fasta"],
                "remove_operations": [
                    "read_preprocessing",
                    "metagenome_assembly",
                    "viral_sequence_detection",
                ],
            },
        ],
        "Viral taxonomy": [
            {
                "template_id": "virome_illumina_viral_taxonomy",
                "external_inputs": ["viral_fasta"],
                "remove_operations": [
                    "read_preprocessing",
                    "metagenome_assembly",
                ],
            },
        ],
        "Viral host prediction": [
            {
                "template_id": "virome_illumina_host_prediction",
                "external_inputs": [
                    "viral_fasta",
                    "iphop_database",
                ],
                "remove_operations": [
                    "read_preprocessing",
                    "metagenome_assembly",
                    "viral_sequence_detection",
                ],
            },
        ],
        "Viral clustering / vOTU analysis": [
            {
                "template_id": "virome_illumina_votu_clustering",
                "external_inputs": ["viral_fasta"],
                "remove_operations": [
                    "read_preprocessing",
                    "metagenome_assembly",
                    "viral_sequence_detection",
                ],
            },
        ],
        "Viral functional annotation": [
            {
                "template_id": "virome_illumina_functional_annotation",
                "external_inputs": [
                    "viral_fasta",
                    "eggnog_database",
                ],
                "remove_operations": [
                    "read_preprocessing",
                    "metagenome_assembly",
                    "viral_sequence_detection",
                ],
            },
        ],
    },

    ("Bulk transcriptome", GENE_COUNT_MATRIX): {
        "Differential expression": [
            {
                "template_id": "bulk_transcriptome_illumina_differential_expression_alignment",
                "external_inputs": [
                    "gene_count_matrix",
                    "sample_metadata",
                    "analysis_design",
                ],
                "remove_operations": [
                    "transcriptome_indexing",
                    "rna_alignment",
                    "alignment_processing",
                    "gene_quantification",
                ],
            },
        ],
    },

    ("Bulk transcriptome", SIGNIFICANT_GENE_LIST): {
        "Functional enrichment": [
            {
                "template_id": "bulk_transcriptome_functional_enrichment",
                "external_inputs": [
                    "significant_gene_list",
                    "gene_identifier_mapping",
                    "gene_set_database",
                ],
                "remove_operations": [],
            },
        ],
    },

    ("Bulk transcriptome", RANKED_GENE_LIST): {
        "Pathway analysis": [
            {
                "template_id": "bulk_transcriptome_pathway_analysis",
                "external_inputs": [
                    "ranked_gene_list",
                    "pathway_gene_sets",
                ],
                "remove_operations": [],
            },
        ],
    },
}


_METAGENOME_ALL_GOALS = [
    "Taxonomic profiling",
    "MAG reconstruction",
    "Functional profiling",
    "Pathway analysis",
    "Antibiotic resistance profiling",
    "Virulence profiling",
    "Viral analysis",
    "Plasmid analysis",
    "Strain-level phylogenomics",
    "Microdiversity profiling",
]


_REFERENCE_REQUIRED_GOALS = {
    "Variant analysis",
}


def get_data_state_options(
    sample_type: str,
) -> list[dict]:
    options = _DATA_STATE_OPTIONS.get(
        sample_type
    )

    if options:
        return [
            item.copy()
            for item in options
        ]

    return [
        {
            "id": RAW_READS,
            "label": "Raw sequencing data",
        }
    ]


def get_data_state_label(
    sample_type: str,
    data_state: str,
) -> str:
    for item in get_data_state_options(
        sample_type
    ):
        if item["id"] == data_state:
            return item["label"]

    return str(data_state)


def data_state_requires_reads(
    data_state: str,
) -> bool:
    return data_state == RAW_READS


def supports_reference_finder(
    sample_type: str,
    data_state: str,
) -> bool:
    return (
        sample_type in GENOME_SAMPLE_TYPES
        and data_state in {
            RAW_READS,
            GENOME_ASSEMBLY,
        }
    )


def reference_is_usable(
    reference_context: dict | None,
) -> bool:
    if not isinstance(
        reference_context,
        dict
    ):
        return False

    return bool(
        reference_context.get(
            "usable_reference",
            False
        )
        and
        reference_context.get(
            "reference_accession"
        )
    )


def get_context_goal_options(
    sample_type: str,
    data_state: str,
) -> list[str]:
    if data_state == RAW_READS:
        return []

    if (
        sample_type == "Metagenome"
        and data_state == METAGENOME_CONTIGS
    ):
        return list(
            _METAGENOME_ALL_GOALS
        )

    route_map = _ROUTE_SPECS.get(
        (
            sample_type,
            data_state,
        ),
        {},
    )

    return list(
        route_map.keys()
    )


def get_goal_availability(
    sample_type: str,
    data_state: str,
    goal: str,
) -> dict:
    """
    Return concise route availability for the selected starting data.
    """

    if (
        sample_type != "Metagenome"
        or data_state != METAGENOME_CONTIGS
    ):
        return {
            "status": "ready",
            "selectable": True,
            "note": "",
        }

    direct = {
        "Virulence profiling",
        "Viral analysis",
        "Plasmid analysis",
    }

    if goal in direct:
        return {
            "status": "ready",
            "selectable": True,
            "note": "Ready from assembled metagenome contigs.",
        }

    if goal == "MAG reconstruction":
        return {
            "status": "needs_input",
            "selectable": False,
            "note": (
                "Contigs are available, but the curated MAG route also needs "
                "the original reads to estimate coverage for binning."
            ),
        }

    read_dependent = {
        "Taxonomic profiling",
        "Functional profiling",
        "Pathway analysis",
        "Antibiotic resistance profiling",
        "Strain-level phylogenomics",
        "Microdiversity profiling",
    }

    if goal in read_dependent:
        return {
            "status": "needs_input",
            "selectable": False,
            "note": (
                "The current curated route starts from sequencing reads. "
                "Choose Raw sequencing reads if those files are available."
            ),
        }

    return {
        "status": "unavailable",
        "selectable": False,
        "note": "No compatible route is curated for this starting data yet.",
    }


def filter_goal_options(
    goals: list[str],
    sample_type: str,
    data_state: str,
    reference_context: dict | None = None,
) -> list[str]:
    values: list[str] = []
    seen = set()

    for goal in goals:
        if not goal or goal in seen:
            continue

        if (
            data_state == RAW_READS
            and
            sample_type in GENOME_SAMPLE_TYPES
            and
            goal in _REFERENCE_REQUIRED_GOALS
            and
            not reference_is_usable(
                reference_context
            )
        ):
            continue

        seen.add(goal)
        values.append(goal)

    return values


def compact_reference_context(
    reference_context: dict | None,
) -> dict:
    if not isinstance(
        reference_context,
        dict
    ):
        return {}

    keep = [
        "status",
        "usable_reference",
        "reference_accession",
        "reference_name",
        "reference_level",
        "reference_source",
        "reference_category",
        "organism_name",
        "common_name",
        "tax_id",
        "taxon_rank",
    ]

    return {
        key: reference_context.get(key)
        for key in keep
        if reference_context.get(key)
        not in (
            None,
            "",
        )
    }


def _slug(value) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        str(value).lower(),
    ).strip("_")


def get_context_workflow_strategies(
    sample_type: str,
    data_state: str,
    goal: str,
    workflows: dict,
) -> list[dict]:
    if data_state == RAW_READS:
        return []

    route_map = _ROUTE_SPECS.get(
        (
            sample_type,
            data_state,
        ),
        {},
    )

    specs = route_map.get(
        goal,
        [],
    )

    results = []

    for spec in specs:
        template_id = spec[
            "template_id"
        ]

        template = workflows.get(
            template_id
        )

        if not isinstance(
            template,
            dict
        ):
            continue

        route_id = (
            "context__"
            f"{_slug(sample_type)}__"
            f"{_slug(data_state)}__"
            f"{_slug(template_id)}"
        )

        results.append(
            {
                "id": route_id,
                "name": (
                    template.get(
                        "name",
                        template_id,
                    )
                    + " — from "
                    + get_data_state_label(
                        sample_type,
                        data_state,
                    ).lower()
                ),
                "description": (
                    "Start from the data you already have. "
                    "OmicsRoute removes upstream steps that have already been completed."
                ),
                "dynamic": True,
                "route_class": "current_data_state",
                "template_id": template_id,
            }
        )

    return results


def materialize_context_workflow(
    sample_type: str,
    sequencing: str,
    read_type: str,
    goal: str,
    workflow_id: str | None,
    data_state: str | None,
    workflows: dict,
):
    if (
        not workflow_id
        or not str(
            workflow_id
        ).startswith(
            "context__"
        )
        or not data_state
    ):
        return None

    route_map = _ROUTE_SPECS.get(
        (
            sample_type,
            data_state,
        ),
        {},
    )

    specs = route_map.get(
        goal,
        [],
    )

    selected_spec = None

    for spec in specs:
        template_id = spec[
            "template_id"
        ]

        expected_id = (
            "context__"
            f"{_slug(sample_type)}__"
            f"{_slug(data_state)}__"
            f"{_slug(template_id)}"
        )

        if expected_id == workflow_id:
            selected_spec = spec
            break

    if selected_spec is None:
        return None

    template_id = selected_spec[
        "template_id"
    ]

    template = workflows.get(
        template_id
    )

    if not isinstance(
        template,
        dict
    ):
        return None

    workflow = deepcopy(
        template
    )

    workflow["id"] = workflow_id
    workflow["name"] = (
        template.get(
            "name",
            template_id,
        )
        + " — from "
        + get_data_state_label(
            sample_type,
            data_state,
        ).lower()
    )

    workflow["dynamic_route"] = True
    workflow["route_class"] = "current_data_state"
    workflow["route_origin"] = template_id
    workflow["data_state"] = data_state
    workflow["infer_read_inputs"] = False

    workflow["context"] = {
        **(
            workflow.get(
                "context",
                {}
            )
            or
            {}
        ),
        "sample_type": sample_type,
        "sequencing": sequencing,
        "read_type": read_type,
        "goal": goal,
        "data_state": data_state,
    }

    remove_operations = set(
        selected_spec.get(
            "remove_operations",
            [],
        )
        or
        []
    )

    if remove_operations:
        workflow["steps"] = [
            step
            for step in (
                workflow.get(
                    "steps",
                    [],
                )
                or
                []
            )
            if (
                isinstance(
                    step,
                    dict
                )
                and
                step.get(
                    "operation"
                )
                not in remove_operations
            )
        ]

    workflow["external_inputs"] = list(
        selected_spec.get(
            "external_inputs",
            [],
        )
        or
        []
    )

    return workflow
