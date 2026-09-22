from __future__ import annotations

from copy import deepcopy
import re

PILOT_SAMPLE_TYPE = "Eukaryotic genome"
PILOT_SEQUENCING = "Illumina"

_GOAL_SPECS = {
    "Variant analysis": [
        {
            "id": "variant_analysis",
            "template_id": "eukaryotic_genome_illumina_variant_analysis",
            "route_class": "read_adaptive",
            "skip_if_exact_static": True,
            "description": (
                "Reference-based small-variant analysis. The route adapts the "
                "read-mapping input to paired-end or single-end Illumina FASTQ."
            ),
        }
    ],
    "Genome quality assessment": [
        {
            "id": "genome_quality_from_assembly",
            "template_id": "eukaryotic_genome_quality",
            "route_class": "prerequisite",
            "description": (
                "Assembly-level quality assessment from an existing eukaryotic "
                "genome assembly."
            ),
        }
    ],
    "Repeat annotation": [
        {
            "id": "repeat_annotation_from_assembly",
            "template_id": "eukaryotic_genome_repeat_annotation",
            "route_class": "prerequisite",
            "description": (
                "Repeat discovery and masking from an existing eukaryotic genome assembly."
            ),
        }
    ],
    "Gene prediction": [
        {
            "id": "gene_prediction_braker",
            "template_id": "eukaryotic_genome_gene_prediction_braker",
            "route_class": "prerequisite",
            "description": (
                "Protein-evidence gene prediction from an existing assembly using BRAKER4."
            ),
        },
        {
            "id": "gene_prediction_augustus",
            "template_id": "eukaryotic_genome_gene_prediction_augustus",
            "route_class": "prerequisite",
            "description": (
                "Ab initio gene prediction from an existing assembly using AUGUSTUS."
            ),
        },
    ],
    "Functional annotation": [
        {
            "id": "functional_annotation_from_proteins",
            "template_id": "eukaryotic_genome_functional_annotation",
            "route_class": "prerequisite",
            "description": (
                "Functional annotation from predicted eukaryotic proteins."
            ),
        }
    ],
    "Comparative genomics": [
        {
            "id": "comparative_genomics_from_assemblies",
            "template_id": "eukaryotic_genome_comparative_genomics",
            "route_class": "prerequisite",
            "description": (
                "Pairwise structural comparison from two existing chromosome-level assemblies."
            ),
        }
    ],
}

def _context_value(value):
    if isinstance(value, (list, tuple, set)):
        return " + ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)

def _slug(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")

def is_dynamic_pilot_context(sample_type, sequencing):
    return sample_type == PILOT_SAMPLE_TYPE and sequencing == PILOT_SEQUENCING

def get_dynamic_read_types(sample_type, sequencing):
    if not is_dynamic_pilot_context(sample_type, sequencing):
        return []
    return ["Paired-end", "Single-end"]

def get_dynamic_goal_options(sample_type, sequencing, read_type):
    if not is_dynamic_pilot_context(sample_type, sequencing):
        return []
    if read_type not in {"Paired-end", "Single-end"}:
        return []
    return list(_GOAL_SPECS.keys())

def get_dynamic_goal_availability(sample_type, sequencing, read_type):
    if not is_dynamic_pilot_context(sample_type, sequencing):
        return []
    if read_type not in {"Paired-end", "Single-end"}:
        return []
    return [
        {
            "goal": "Variant analysis",
            "status": "direct",
            "selectable": True,
            "note": "Uses the selected Illumina reads plus a reference genome.",
        },
        {
            "goal": "Genome quality assessment",
            "status": "prerequisite",
            "selectable": True,
            "note": "Starts from an existing eukaryotic genome assembly.",
        },
        {
            "goal": "Repeat annotation",
            "status": "prerequisite",
            "selectable": True,
            "note": "Starts from an existing eukaryotic genome assembly.",
        },
        {
            "goal": "Gene prediction",
            "status": "prerequisite",
            "selectable": True,
            "note": (
                "Starts from an existing assembly and requires protein evidence "
                "or an AUGUSTUS species model, depending on route."
            ),
        },
        {
            "goal": "Functional annotation",
            "status": "prerequisite",
            "selectable": True,
            "note": "Starts from predicted eukaryotic proteins.",
        },
        {
            "goal": "Comparative genomics",
            "status": "prerequisite",
            "selectable": True,
            "note": "Starts from two existing chromosome-level assemblies.",
        },
        {
            "goal": "Genome assembly",
            "status": "not_curated",
            "selectable": False,
            "note": (
                "No Illumina-only eukaryotic de novo assembly route is currently "
                "curated. OmicsRoute will not substitute a bacterial assembler."
            ),
        },
        {
            "goal": "Hybrid genome assembly",
            "status": "additional_data",
            "selectable": False,
            "note": "Requires long-read data in addition to Illumina reads.",
        },
    ]

def _has_exact_static_workflow(workflows, sample_type, sequencing, read_type, goal):
    for workflow in workflows.values():
        if not isinstance(workflow, dict):
            continue
        context = workflow.get("context", {}) or {}
        if (
            _context_value(context.get("sample_type")) == sample_type
            and _context_value(context.get("sequencing")) == sequencing
            and _context_value(context.get("read_type")) == read_type
            and _context_value(context.get("goal")) == goal
        ):
            return True
    return False

def _strategy_id(read_type, spec_id):
    return (
        "dynamic__eukaryotic_genome__illumina__"
        f"{_slug(read_type)}__{_slug(spec_id)}"
    )

def get_dynamic_workflow_strategies(
    sample_type,
    sequencing,
    read_type,
    goal,
    workflows,
):
    if not is_dynamic_pilot_context(sample_type, sequencing):
        return []
    if read_type not in {"Paired-end", "Single-end"}:
        return []

    results = []
    for spec in _GOAL_SPECS.get(goal, []):
        if (
            spec.get("skip_if_exact_static", False)
            and _has_exact_static_workflow(
                workflows, sample_type, sequencing, read_type, goal
            )
        ):
            continue

        template = workflows.get(spec["template_id"])
        if not isinstance(template, dict):
            continue

        route_id = _strategy_id(read_type, spec["id"])
        template_name = template.get("name", spec["template_id"])

        if spec["route_class"] == "read_adaptive":
            name = (
                f"Eukaryotic genome — Illumina {read_type.lower()} "
                f"{goal.lower()}"
            )
        else:
            name = (
                f"{template_name} — {read_type.lower()} project context"
            )

        results.append(
            {
                "id": route_id,
                "name": name,
                "description": spec["description"],
                "dynamic": True,
                "route_class": spec["route_class"],
                "template_id": spec["template_id"],
            }
        )
    return results

def materialize_dynamic_workflow(
    sample_type,
    sequencing,
    read_type,
    goal,
    workflow_id,
    workflows,
):
    if not workflow_id or not str(workflow_id).startswith("dynamic__"):
        return None

    selected = next(
        (
            item
            for item in get_dynamic_workflow_strategies(
                sample_type,
                sequencing,
                read_type,
                goal,
                workflows,
            )
            if item["id"] == workflow_id
        ),
        None,
    )
    if selected is None:
        return None

    template = workflows.get(selected["template_id"])
    if not isinstance(template, dict):
        return None

    workflow = deepcopy(template)
    workflow["id"] = workflow_id
    workflow["name"] = selected["name"]
    workflow["dynamic_route"] = True
    workflow["route_class"] = selected["route_class"]
    workflow["route_origin"] = selected["template_id"]
    workflow["context"] = {
        **(workflow.get("context", {}) or {}),
        "sample_type": sample_type,
        "sequencing": sequencing,
        "read_type": read_type,
        "goal": goal,
    }

    original_description = workflow.get("description", "")
    workflow["description"] = selected["description"]
    if original_description:
        workflow["description"] += "\n\nCurated route basis: " + original_description

    if selected["route_class"] == "read_adaptive":
        workflow["infer_read_inputs"] = True
        external_inputs = list(workflow.get("external_inputs", []) or [])

        if read_type == "Single-end":
            external_inputs = [
                "raw_single_fastq" if item == "raw_paired_fastq" else item
                for item in external_inputs
            ]
            for step in workflow.get("steps", []) or []:
                if not isinstance(step, dict):
                    continue
                for field in ("name", "description"):
                    value = step.get(field)
                    if isinstance(value, str):
                        step[field] = (
                            value.replace("paired-end", "single-end")
                            .replace("Paired-end", "Single-end")
                        )

        workflow["external_inputs"] = external_inputs
    else:
        workflow["infer_read_inputs"] = False

    return workflow
