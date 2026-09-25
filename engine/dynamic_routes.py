from __future__ import annotations

from copy import deepcopy
import re


EUKARYOTIC_SAMPLE_TYPE = "Eukaryotic genome"
BACTERIAL_SAMPLE_TYPE = "Bacterial isolate"
ILLUMINA = "Illumina"


_EUKARYOTIC_GOAL_SPECS = {
    "Variant analysis": [
        {
            "id": "variant_analysis",
            "template_id": "eukaryotic_genome_illumina_variant_analysis",
            "route_class": "read_adaptive",
            "skip_if_exact_static": True,
            "description": (
                "Reference-based small-variant analysis. The route adapts "
                "read mapping to paired-end or single-end Illumina FASTQ."
            ),
        }
    ],
    "Genome quality assessment": [
        {
            "id": "genome_quality_from_assembly",
            "template_id": "eukaryotic_genome_quality",
            "route_class": "prerequisite",
            "description": (
                "Assembly-level quality assessment from an existing "
                "eukaryotic genome assembly."
            ),
        }
    ],
    "Repeat annotation": [
        {
            "id": "repeat_annotation_from_assembly",
            "template_id": "eukaryotic_genome_repeat_annotation",
            "route_class": "prerequisite",
            "description": (
                "Repeat discovery and masking from an existing "
                "eukaryotic genome assembly."
            ),
        }
    ],
    "Gene prediction": [
        {
            "id": "gene_prediction_braker",
            "template_id": "eukaryotic_genome_gene_prediction_braker",
            "route_class": "prerequisite",
            "description": (
                "Protein-evidence gene prediction from an existing "
                "assembly using BRAKER4."
            ),
        },
        {
            "id": "gene_prediction_augustus",
            "template_id": "eukaryotic_genome_gene_prediction_augustus",
            "route_class": "prerequisite",
            "description": (
                "Ab initio gene prediction from an existing "
                "assembly using AUGUSTUS."
            ),
        },
    ],
    "Functional annotation": [
        {
            "id": "functional_annotation_from_proteins",
            "template_id": "eukaryotic_genome_functional_annotation",
            "route_class": "prerequisite",
            "description": (
                "Functional annotation from predicted "
                "eukaryotic proteins."
            ),
        }
    ],
    "Comparative genomics": [
        {
            "id": "comparative_genomics_from_assemblies",
            "template_id": "eukaryotic_genome_comparative_genomics",
            "route_class": "prerequisite",
            "description": (
                "Pairwise structural comparison from two existing "
                "chromosome-level assemblies."
            ),
        }
    ],
}


_BACTERIAL_SINGLE_END_SPECS = {
    "Whole genome characterization": [
        "bacterial_illumina_wgs",
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
    "Variant analysis": [
        "bacterial_illumina_variant_analysis",
    ],
    "Species identification": [
        "bacterial_illumina_species_identification_gtdbtk",
        "bacterial_illumina_species_identification_fastani",
    ],
    "Plasmid detection": [
        "bacterial_illumina_plasmid_mobsuite",
        "bacterial_illumina_plasmid_replicon",
        "bacterial_illumina_plasmid_genomad",
    ],
}


def _context_value(value):
    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):
        return " + ".join(
            str(item)
            for item in value
        )

    if value is None:
        return ""

    return str(value)


def _slug(value):
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        str(value).lower(),
    ).strip("_")


def _is_eukaryotic_context(
    sample_type,
    sequencing,
):
    return (
        sample_type
        ==
        EUKARYOTIC_SAMPLE_TYPE
        and
        sequencing
        ==
        ILLUMINA
    )


def _is_bacterial_context(
    sample_type,
    sequencing,
):
    return (
        sample_type
        ==
        BACTERIAL_SAMPLE_TYPE
        and
        sequencing
        ==
        ILLUMINA
    )


def get_dynamic_read_types(
    sample_type,
    sequencing,
):
    if (
        _is_eukaryotic_context(
            sample_type,
            sequencing,
        )
        or
        _is_bacterial_context(
            sample_type,
            sequencing,
        )
    ):
        return [
            "Paired-end",
            "Single-end",
        ]

    return []


def get_dynamic_goal_options(
    sample_type,
    sequencing,
    read_type,
):
    if read_type not in {
        "Paired-end",
        "Single-end",
    }:
        return []

    if _is_eukaryotic_context(
        sample_type,
        sequencing,
    ):
        return list(
            _EUKARYOTIC_GOAL_SPECS.keys()
        )

    if (
        _is_bacterial_context(
            sample_type,
            sequencing,
        )
        and
        read_type
        ==
        "Single-end"
    ):
        return list(
            _BACTERIAL_SINGLE_END_SPECS.keys()
        )

    return []


def get_dynamic_goal_availability(
    sample_type,
    sequencing,
    read_type,
):
    if not _is_eukaryotic_context(
        sample_type,
        sequencing,
    ):
        return []

    if read_type not in {
        "Paired-end",
        "Single-end",
    }:
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
            "note": "Starts from an existing eukaryotic genome assembly.",
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
                "No Illumina-only eukaryotic de novo assembly route "
                "is currently curated."
            ),
        },
        {
            "goal": "Hybrid genome assembly",
            "status": "additional_data",
            "selectable": False,
            "note": "Requires long-read data in addition to Illumina reads.",
        },
    ]


def _has_exact_static_workflow(
    workflows,
    sample_type,
    sequencing,
    read_type,
    goal,
):
    for workflow in workflows.values():
        if not isinstance(
            workflow,
            dict,
        ):
            continue

        context = (
            workflow.get(
                "context",
                {},
            )
            or
            {}
        )

        if (
            _context_value(
                context.get(
                    "sample_type"
                )
            )
            ==
            sample_type
            and
            _context_value(
                context.get(
                    "sequencing"
                )
            )
            ==
            sequencing
            and
            _context_value(
                context.get(
                    "read_type"
                )
            )
            ==
            read_type
            and
            _context_value(
                context.get(
                    "goal"
                )
            )
            ==
            goal
        ):
            return True

    return False


def _eukaryotic_strategy_id(
    read_type,
    spec_id,
):
    return (
        "dynamic__eukaryotic_genome__illumina__"
        f"{_slug(read_type)}__{_slug(spec_id)}"
    )


def _bacterial_strategy_id(
    read_type,
    template_id,
):
    return (
        "dynamic__bacterial_isolate__illumina__"
        f"{_slug(read_type)}__{_slug(template_id)}"
    )


def get_dynamic_workflow_strategies(
    sample_type,
    sequencing,
    read_type,
    goal,
    workflows,
):
    if read_type not in {
        "Paired-end",
        "Single-end",
    }:
        return []

    results = []

    if _is_eukaryotic_context(
        sample_type,
        sequencing,
    ):

        for spec in _EUKARYOTIC_GOAL_SPECS.get(
            goal,
            [],
        ):
            if (
                spec.get(
                    "skip_if_exact_static",
                    False,
                )
                and
                _has_exact_static_workflow(
                    workflows,
                    sample_type,
                    sequencing,
                    read_type,
                    goal,
                )
            ):
                continue

            template = workflows.get(
                spec[
                    "template_id"
                ]
            )

            if not isinstance(
                template,
                dict,
            ):
                continue

            route_id = (
                _eukaryotic_strategy_id(
                    read_type,
                    spec[
                        "id"
                    ],
                )
            )

            template_name = (
                template.get(
                    "name",
                    spec[
                        "template_id"
                    ],
                )
            )

            if (
                spec[
                    "route_class"
                ]
                ==
                "read_adaptive"
            ):
                name = (
                    "Eukaryotic genome — Illumina "
                    f"{read_type.lower()} "
                    f"{goal.lower()}"
                )
            else:
                name = (
                    f"{template_name} — "
                    f"{read_type.lower()} project context"
                )

            results.append(
                {
                    "id": route_id,
                    "name": name,
                    "description": spec[
                        "description"
                    ],
                    "dynamic": True,
                    "route_class": spec[
                        "route_class"
                    ],
                    "template_id": spec[
                        "template_id"
                    ],
                }
            )

    if (
        _is_bacterial_context(
            sample_type,
            sequencing,
        )
        and
        read_type
        ==
        "Single-end"
    ):

        for template_id in (
            _BACTERIAL_SINGLE_END_SPECS.get(
                goal,
                [],
            )
        ):
            template = workflows.get(
                template_id
            )

            if not isinstance(
                template,
                dict,
            ):
                continue

            results.append(
                {
                    "id": (
                        _bacterial_strategy_id(
                            read_type,
                            template_id,
                        )
                    ),
                    "name": (
                        template.get(
                            "name",
                            template_id,
                        )
                        + " — single-end"
                    ),
                    "description": (
                        "Single-end Illumina adaptation of the curated "
                        "bacterial route. Read-level candidates that do not "
                        "support single-end input remain blocked rather than "
                        "being silently substituted."
                    ),
                    "dynamic": True,
                    "route_class": "read_adaptive",
                    "template_id": template_id,
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
    if (
        not workflow_id
        or not str(
            workflow_id
        ).startswith(
            "dynamic__"
        )
    ):
        return None

    selected = next(
        (
            item
            for item
            in get_dynamic_workflow_strategies(
                sample_type,
                sequencing,
                read_type,
                goal,
                workflows,
            )
            if item[
                "id"
            ]
            ==
            workflow_id
        ),
        None,
    )

    if selected is None:
        return None

    template = workflows.get(
        selected[
            "template_id"
        ]
    )

    if not isinstance(
        template,
        dict,
    ):
        return None

    workflow = deepcopy(
        template
    )

    workflow[
        "id"
    ] = workflow_id

    workflow[
        "name"
    ] = selected[
        "name"
    ]

    workflow[
        "dynamic_route"
    ] = True

    workflow[
        "route_class"
    ] = selected[
        "route_class"
    ]

    workflow[
        "route_origin"
    ] = selected[
        "template_id"
    ]

    workflow[
        "context"
    ] = {
        **(
            workflow.get(
                "context",
                {},
            )
            or
            {}
        ),
        "sample_type": sample_type,
        "sequencing": sequencing,
        "read_type": read_type,
        "goal": goal,
    }

    original_description = (
        workflow.get(
            "description",
            "",
        )
    )

    workflow[
        "description"
    ] = selected[
        "description"
    ]

    if original_description:
        workflow[
            "description"
        ] += (
            "\n\nCurated route basis: "
            + original_description
        )

    if (
        selected[
            "route_class"
        ]
        ==
        "read_adaptive"
    ):
        workflow[
            "infer_read_inputs"
        ] = True

        external_inputs = list(
            workflow.get(
                "external_inputs",
                [],
            )
            or
            []
        )

        if read_type == "Single-end":
            external_inputs = [
                (
                    "raw_single_fastq"
                    if item
                    ==
                    "raw_paired_fastq"
                    else item
                )
                for item
                in external_inputs
            ]

            for step in (
                workflow.get(
                    "steps",
                    [],
                )
                or
                []
            ):
                if not isinstance(
                    step,
                    dict,
                ):
                    continue

                for field in (
                    "name",
                    "description",
                ):
                    value = step.get(
                        field
                    )

                    if isinstance(
                        value,
                        str,
                    ):
                        step[
                            field
                        ] = (
                            value
                            .replace(
                                "paired-end",
                                "single-end",
                            )
                            .replace(
                                "Paired-end",
                                "Single-end",
                            )
                        )

        workflow[
            "external_inputs"
        ] = external_inputs

    else:
        workflow[
            "infer_read_inputs"
        ] = False

    return workflow

# ==================================================
# METAGENOME PLATFORM COVERAGE V1
# ==================================================

_legacy_get_dynamic_read_types_metagenome_v1 = get_dynamic_read_types
_legacy_get_dynamic_goal_options_metagenome_v1 = get_dynamic_goal_options
_legacy_get_dynamic_workflow_strategies_metagenome_v1 = get_dynamic_workflow_strategies
_legacy_materialize_dynamic_workflow_metagenome_v1 = materialize_dynamic_workflow

METAGENOME_SAMPLE_TYPE = "Metagenome"
ONT = "Oxford Nanopore"
PACBIO = "PacBio"
LONG_READ_PLATFORMS = {ONT, PACBIO}

_METAGENOME_SINGLE_END_SPECS = {
    "Taxonomic profiling": [
        "metagenome_illumina_taxonomy_prokaryotic",
        "metagenome_illumina_taxonomy_eukaryotic",
        "metagenome_illumina_taxonomy_broad",
    ],
    "Functional profiling": ["metagenome_illumina_functional"],
    "Pathway analysis": ["metagenome_illumina_pathways"],
    "Antibiotic resistance profiling": [
        "metagenome_illumina_resistome_deeparg",
        "metagenome_illumina_resistome_rgi",
        "metagenome_illumina_resistome_amrplusplus",
    ],
    "Virulence profiling": ["metagenome_illumina_virulence"],
    "Viral analysis": ["metagenome_illumina_viral"],
    "Plasmid analysis": [
        "metagenome_illumina_plasmid_genomad",
        "metagenome_illumina_plasmid_plasx",
    ],
    "MAG reconstruction": ["metagenome_illumina_mag_single"],
    "Microdiversity profiling": ["metagenome_illumina_microdiversity"],
}

_METAGENOME_LONG_GOALS = (
    "Taxonomic profiling",
    "MAG reconstruction",
    "Antibiotic resistance profiling",
    "Virulence profiling",
    "Viral analysis",
    "Plasmid analysis",
)


def get_dynamic_sequencing_options(sample_type):
    if sample_type == METAGENOME_SAMPLE_TYPE:
        return [ILLUMINA, ONT, PACBIO]
    return []


def get_dynamic_read_types(sample_type, sequencing):
    legacy = list(
        _legacy_get_dynamic_read_types_metagenome_v1(
            sample_type,
            sequencing,
        )
        or []
    )

    if sample_type != METAGENOME_SAMPLE_TYPE:
        return legacy

    if sequencing == ILLUMINA:
        for value in ("Paired-end", "Single-end"):
            if value not in legacy:
                legacy.append(value)
        return legacy

    if sequencing in LONG_READ_PLATFORMS:
        return ["Long reads"]

    return legacy


def get_dynamic_goal_options(sample_type, sequencing, read_type):
    legacy = list(
        _legacy_get_dynamic_goal_options_metagenome_v1(
            sample_type,
            sequencing,
            read_type,
        )
        or []
    )

    if sample_type != METAGENOME_SAMPLE_TYPE:
        return legacy

    if sequencing == ILLUMINA and read_type == "Single-end":
        extra = list(_METAGENOME_SINGLE_END_SPECS.keys())
    elif sequencing in LONG_READ_PLATFORMS and read_type == "Long reads":
        extra = list(_METAGENOME_LONG_GOALS)
    else:
        extra = []

    for goal in extra:
        if goal not in legacy:
            legacy.append(goal)

    return legacy


def _metagenome_single_strategy_id(template_id):
    return (
        "dynamic__metagenome__illumina__single_end__"
        f"{_slug(template_id)}"
    )


def _metagenome_long_strategy_id(sequencing, goal):
    return (
        "dynamic__metagenome__"
        f"{_slug(sequencing)}__long_reads__"
        f"{_slug(goal)}"
    )


def _long_read_platform_note(sequencing):
    if sequencing == ONT:
        return (
            "Oxford Nanopore long-read metagenome route. "
            "Long-read QC/filtering precedes platform-appropriate "
            "profiling or Flye --meta assembly."
        )

    return (
        "PacBio long-read metagenome route. "
        "For HiFi data, Flye should use the PacBio HiFi input mode "
        "together with --meta for uneven metagenomic coverage."
    )


def _long_read_common_steps():
    return [
        {
            "operation": "raw_read_qc",
            "name": "Long-read quality control",
            "description": (
                "Inspect read length and quality distributions before "
                "downstream metagenomic analysis."
            ),
            "candidates": ["nanoplot"],
        },
        {
            "operation": "read_preprocessing",
            "name": "Long-read filtering",
            "description": (
                "Apply quality/length filtering when indicated by QC. "
                "Chopper and Filtlong are alternatives."
            ),
            "candidates": ["chopper", "filtlong"],
        },
    ]


def _long_read_assembly_step():
    return {
        "operation": "metagenome_assembly",
        "name": "Long-read metagenome assembly",
        "description": (
            "Assemble the metagenome with Flye in metagenome/uneven-coverage "
            "mode (--meta), using the platform-specific Flye read mode."
        ),
        "candidates": ["flye"],
    }


def _build_metagenome_long_workflow(sequencing, goal, workflow_id):
    steps = _long_read_common_steps()

    if goal == "Taxonomic profiling":
        steps.append(
            {
                "operation": "taxonomic_profiling",
                "name": "Long-read taxonomic profiling",
                "description": (
                    "Profile long-read shotgun metagenomes with MetaPhlAn "
                    "using its dedicated long-read mode."
                ),
                "candidates": ["metaphlan"],
            }
        )

    elif goal == "Antibiotic resistance profiling":
        steps.append(
            {
                "operation": "resistome_profiling",
                "name": "Long-read resistome profiling",
                "description": (
                    "Profile antimicrobial resistance determinants from "
                    "quality-controlled long metagenomic reads with DeepARG."
                ),
                "candidates": ["deeparg"],
            }
        )

    elif goal == "Virulence profiling":
        steps.extend(
            [
                _long_read_assembly_step(),
                {
                    "operation": "virulence_profiling",
                    "name": "Virulence factor profiling",
                    "description": (
                        "Detect potential virulence factors and toxins from "
                        "assembled metagenomic contigs with PathoFact 2.0."
                    ),
                    "candidates": ["pathofact2"],
                },
            ]
        )

    elif goal == "Viral analysis":
        steps.extend(
            [
                _long_read_assembly_step(),
                {
                    "operation": "viral_sequence_detection",
                    "name": "Viral sequence detection",
                    "description": (
                        "Identify candidate viral contigs from the long-read "
                        "metagenome assembly."
                    ),
                    "candidates": ["genomad", "virsorter2"],
                },
                {
                    "operation": "viral_quality",
                    "name": "Viral genome quality assessment",
                    "description": (
                        "Assess candidate viral sequence completeness and "
                        "contamination with CheckV."
                    ),
                    "candidates": ["checkv"],
                },
                {
                    "operation": "viral_taxonomy",
                    "name": "Viral taxonomic classification",
                    "description": (
                        "Assign viral taxonomy with geNomad's marker/ICTV "
                        "taxonomy framework."
                    ),
                    "candidates": ["genomad"],
                },
            ]
        )

    elif goal == "Plasmid analysis":
        steps.extend(
            [
                _long_read_assembly_step(),
                {
                    "operation": "plasmid_detection",
                    "name": "Plasmid sequence prediction",
                    "description": (
                        "Identify plasmid-associated assembled metagenomic "
                        "contigs with geNomad."
                    ),
                    "candidates": ["genomad"],
                },
            ]
        )

    elif goal == "MAG reconstruction":
        steps.extend(
            [
                _long_read_assembly_step(),
                {
                    "operation": "assembly_qc",
                    "name": "Assembly quality control",
                    "description": (
                        "Review metagenome assembly statistics before "
                        "coverage estimation and binning."
                    ),
                    "candidates": ["quast"],
                },
                {
                    "operation": "read_mapping",
                    "name": "Map long reads back to the assembly",
                    "description": (
                        "Map original long reads to assembled contigs with "
                        "Minimap2. Identity filtering should match the actual "
                        "long-read platform/error profile."
                    ),
                    "candidates": ["minimap2"],
                },
                {
                    "operation": "alignment_processing",
                    "name": "Alignment sorting and indexing",
                    "description": (
                        "Convert the long-read mapping into a coordinate-sorted "
                        "BAM and create its index."
                    ),
                    "candidates": ["samtools"],
                },
                {
                    "operation": "coverage_estimation",
                    "name": "Contig coverage estimation",
                    "description": (
                        "Summarize per-contig depth from mapped long reads."
                    ),
                    "candidates": ["jgi_depth"],
                },
                {
                    "operation": "genome_binning",
                    "name": "Independent MAG binning",
                    "description": (
                        "Run multiple independent binners and require at least "
                        "two successful bin sets before consensus refinement."
                    ),
                    "mode": "parallel",
                    "min_successful_candidates": 2,
                    "aggregate_produces": ["multiple_mag_bin_sets"],
                    "candidates": ["semibin2", "metabat2", "concoct"],
                },
                {
                    "operation": "bin_refinement",
                    "name": "Consensus bin refinement",
                    "description": (
                        "Integrate independent binning results with DAS Tool."
                    ),
                    "candidates": ["dastool"],
                },
                {
                    "operation": "mag_quality",
                    "name": "MAG quality assessment",
                    "description": (
                        "Estimate completeness and contamination of refined MAGs."
                    ),
                    "candidates": ["checkm2"],
                },
                {
                    "operation": "mag_taxonomy",
                    "name": "MAG taxonomic classification",
                    "description": (
                        "Assign standardized taxonomy to quality-controlled "
                        "bacterial/archaeal MAGs."
                    ),
                    "candidates": ["gtdbtk", "catbat", "sourmash"],
                },
            ]
        )

    else:
        return None

    return {
        "id": workflow_id,
        "name": f"Metagenome — {sequencing} long-read {goal.lower()}",
        "description": _long_read_platform_note(sequencing),
        "dynamic_route": True,
        "route_class": "long_read_metagenome",
        "route_origin": "metagenome_platform_coverage_v1",
        "context": {
            "sample_type": METAGENOME_SAMPLE_TYPE,
            "sequencing": sequencing,
            "read_type": "Long reads",
            "goal": goal,
        },
        "external_inputs": [],
        "steps": steps,
    }


def get_dynamic_workflow_strategies(
    sample_type,
    sequencing,
    read_type,
    goal,
    workflows,
):
    legacy = list(
        _legacy_get_dynamic_workflow_strategies_metagenome_v1(
            sample_type,
            sequencing,
            read_type,
            goal,
            workflows,
        )
        or []
    )

    if sample_type != METAGENOME_SAMPLE_TYPE:
        return legacy

    results = list(legacy)

    if sequencing == ILLUMINA and read_type == "Single-end":
        for template_id in _METAGENOME_SINGLE_END_SPECS.get(goal, []):
            template = workflows.get(template_id)

            if not isinstance(template, dict):
                continue

            results.append(
                {
                    "id": _metagenome_single_strategy_id(template_id),
                    "name": template.get("name", template_id) + " — single-end",
                    "description": (
                        "Single-end Illumina adaptation of the curated "
                        "metagenome route."
                    ),
                    "dynamic": True,
                    "route_class": "read_adaptive",
                    "template_id": template_id,
                }
            )

    elif (
        sequencing in LONG_READ_PLATFORMS
        and read_type == "Long reads"
        and goal in _METAGENOME_LONG_GOALS
    ):
        results.append(
            {
                "id": _metagenome_long_strategy_id(sequencing, goal),
                "name": f"Metagenome — {sequencing} long-read {goal.lower()}",
                "description": _long_read_platform_note(sequencing),
                "dynamic": True,
                "route_class": "long_read_metagenome",
                "template_id": None,
            }
        )

    return results


def _adapt_metagenome_single_end(workflow, workflow_id, name, goal):
    workflow = deepcopy(workflow)

    original_template_id = workflow.get("id")
    workflow["id"] = workflow_id
    workflow["name"] = name
    workflow["dynamic_route"] = True
    workflow["route_class"] = "read_adaptive"
    workflow["route_origin"] = original_template_id or "curated_metagenome_template"

    workflow["context"] = {
        **(workflow.get("context", {}) or {}),
        "sample_type": METAGENOME_SAMPLE_TYPE,
        "sequencing": ILLUMINA,
        "read_type": "Single-end",
        "goal": goal,
    }

    workflow["infer_read_inputs"] = True

    external_inputs = []
    for item in workflow.get("external_inputs", []) or []:
        if item == "raw_paired_fastq":
            item = "raw_single_fastq"
        if item == "raw_paired_fastq_collection":
            continue
        external_inputs.append(item)

    workflow["external_inputs"] = external_inputs

    for step in workflow.get("steps", []) or []:
        if not isinstance(step, dict):
            continue

        if step.get("operation") == "metagenome_assembly":
            step["candidates"] = [
                item
                for item in (step.get("candidates", []) or [])
                if item != "metaspades"
            ]

        for field in ("name", "description"):
            value = step.get(field)
            if isinstance(value, str):
                step[field] = (
                    value
                    .replace("paired-end", "single-end")
                    .replace("Paired-end", "Single-end")
                )

    original_description = workflow.get("description", "")
    workflow["description"] = (
        "Single-end Illumina adaptation of a curated metagenome route."
    )

    if original_description:
        workflow["description"] += (
            "\n\nCurated route basis: " + original_description
        )

    return workflow


def materialize_dynamic_workflow(
    sample_type,
    sequencing,
    read_type,
    goal,
    workflow_id,
    workflows,
):
    legacy = _legacy_materialize_dynamic_workflow_metagenome_v1(
        sample_type,
        sequencing,
        read_type,
        goal,
        workflow_id,
        workflows,
    )

    if legacy is not None:
        return legacy

    if sample_type != METAGENOME_SAMPLE_TYPE:
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
            if item.get("id") == workflow_id
        ),
        None,
    )

    if selected is None:
        return None

    if selected.get("route_class") == "read_adaptive":
        template = workflows.get(selected.get("template_id"))
        if not isinstance(template, dict):
            return None

        return _adapt_metagenome_single_end(
            template,
            workflow_id,
            selected.get("name", workflow_id),
            goal,
        )

    if selected.get("route_class") == "long_read_metagenome":
        return _build_metagenome_long_workflow(
            sequencing,
            goal,
            workflow_id,
        )

    return None
