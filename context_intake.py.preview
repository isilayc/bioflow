from __future__ import annotations

from copy import deepcopy
import re


RAW_READS = "raw_reads"
GENOME_ASSEMBLY = "genome_assembly"
PREDICTED_PROTEINS = "predicted_proteins"

GENOME_SAMPLE_TYPES = {
    "Bacterial isolate",
    "Eukaryotic genome",
}

_DATA_STATE_OPTIONS = {
    "Bacterial isolate": [
        {
            "id": RAW_READS,
            "label": "Raw sequencing reads",
        },
        {
            "id": GENOME_ASSEMBLY,
            "label": "Genome assembly FASTA",
        },
    ],
    "Eukaryotic genome": [
        {
            "id": RAW_READS,
            "label": "Raw sequencing reads",
        },
        {
            "id": GENOME_ASSEMBLY,
            "label": "Genome assembly FASTA",
        },
        {
            "id": PREDICTED_PROTEINS,
            "label": "Predicted protein FASTA",
        },
    ],
}

_EUKARYOTIC_ASSEMBLY_ROUTES = {
    "Genome quality assessment": [
        "eukaryotic_genome_quality",
    ],
    "Repeat annotation": [
        "eukaryotic_genome_repeat_annotation",
    ],
    "Gene prediction": [
        "eukaryotic_genome_gene_prediction_braker",
        "eukaryotic_genome_gene_prediction_augustus",
    ],
    "Comparative genomics": [
        "eukaryotic_genome_comparative_genomics",
    ],
}

_EUKARYOTIC_PROTEIN_ROUTES = {
    "Functional annotation": [
        "eukaryotic_genome_functional_annotation",
    ],
}

_BACTERIAL_ASSEMBLY_ROUTES = {
    "Whole genome characterization": [
        "bacterial_illumina_wgs",
    ],
    "Species identification": [
        "bacterial_illumina_species_identification_gtdbtk",
    ],
    "Antimicrobial resistance detection": [
        "bacterial_illumina_amr",
    ],
    "Virulence profiling": [
        "bacterial_illumina_virulence",
    ],
    "MLST / strain typing": [
        "bacterial_illumina_mlst",
    ],
    "Prophage detection": [
        "bacterial_illumina_prophage",
    ],
    "Plasmid detection": [
        "bacterial_illumina_plasmid_mobsuite",
        "bacterial_illumina_plasmid_replicon",
        "bacterial_illumina_plasmid_genomad",
    ],
}

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
        sample_type == "Eukaryotic genome"
        and data_state == GENOME_ASSEMBLY
    ):
        return list(
            _EUKARYOTIC_ASSEMBLY_ROUTES.keys()
        )

    if (
        sample_type == "Eukaryotic genome"
        and data_state == PREDICTED_PROTEINS
    ):
        return list(
            _EUKARYOTIC_PROTEIN_ROUTES.keys()
        )

    if (
        sample_type == "Bacterial isolate"
        and data_state == GENOME_ASSEMBLY
    ):
        return list(
            _BACTERIAL_ASSEMBLY_ROUTES.keys()
        )

    return []


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


def _context_route_map(
    sample_type: str,
    data_state: str,
):
    if (
        sample_type == "Eukaryotic genome"
        and data_state == GENOME_ASSEMBLY
    ):
        return _EUKARYOTIC_ASSEMBLY_ROUTES

    if (
        sample_type == "Eukaryotic genome"
        and data_state == PREDICTED_PROTEINS
    ):
        return _EUKARYOTIC_PROTEIN_ROUTES

    if (
        sample_type == "Bacterial isolate"
        and data_state == GENOME_ASSEMBLY
    ):
        return _BACTERIAL_ASSEMBLY_ROUTES

    return {}


def get_context_workflow_strategies(
    sample_type: str,
    data_state: str,
    goal: str,
    workflows: dict,
) -> list[dict]:
    if data_state == RAW_READS:
        return []

    route_map = _context_route_map(
        sample_type,
        data_state,
    )

    template_ids = route_map.get(
        goal,
        [],
    )

    results = []

    for template_id in template_ids:
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
                    +
                    (
                        " — from existing assembly"
                        if data_state == GENOME_ASSEMBLY
                        else " — from predicted proteins"
                    )
                ),
                "description": (
                    "Start from the data you already have; upstream sequencing "
                    "and reconstruction steps are not repeated."
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

    strategies = (
        get_context_workflow_strategies(
            sample_type,
            data_state,
            goal,
            workflows,
        )
    )

    selected = next(
        (
            item
            for item in strategies
            if item["id"]
            == workflow_id
        ),
        None,
    )

    if selected is None:
        return None

    template = workflows.get(
        selected["template_id"]
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
    workflow["name"] = selected["name"]
    workflow["dynamic_route"] = True
    workflow["route_class"] = "current_data_state"
    workflow["route_origin"] = (
        selected["template_id"]
    )
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

    if (
        sample_type == "Bacterial isolate"
        and data_state == GENOME_ASSEMBLY
    ):
        remove_operations = {
            "raw_read_qc",
            "read_preprocessing",
            "genome_assembly",
        }

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

        workflow["external_inputs"] = [
            "genome_fasta"
        ]

    return workflow
