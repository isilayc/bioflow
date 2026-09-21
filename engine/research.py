from engine.capabilities import (
    CAPABILITY_FILE,
    capability_catalog_candidates,
    attach_capability_to_registry_candidate,
    resolve_capability_record,
    normalize_name
)

from engine.discovery import (
    get_discovery_query_family,
    screen_discovered_tools
)

from services.biotools import (
    search_biotools_structured
)


# ==================================================
# STRUCTURED SEARCH TERMS
# ==================================================

BIOFLOW_TO_EDAM_OPERATION = {

    "raw_read_qc": [
        "Sequence quality control"
    ],

    "read_preprocessing": [
        "Sequence trimming"
    ],

    "primer_trimming": [
        "Sequence trimming"
    ],

    "genome_assembly": [
        "Genome assembly"
    ],

    "hybrid_genome_assembly": [
        "Genome assembly"
    ],

    "metagenome_assembly": [
        "Genome assembly"
    ],

    "assembly_qc": [
        "Genome assembly validation"
    ],

    "genome_annotation": [
        "Genome annotation"
    ],

    "functional_annotation": [
        "Functional annotation"
    ],

    "taxonomic_profiling": [
        "Taxonomic classification"
    ],

    "taxonomy_assignment": [
        "Taxonomic classification"
    ],

    "amplicon_end_to_end": [
        "Sequence clustering",
        "Taxonomic classification"
    ],

    "asv_inference": [
        "Sequence clustering"
    ],

    "otu_clustering": [
        "Sequence clustering"
    ],

    "alpha_diversity": [
        "Diversity analysis"
    ],

    "beta_diversity": [
        "Diversity analysis"
    ],

    "differential_abundance": [
        "Differential expression analysis"
    ],

    "read_mapping": [
        "Sequence alignment"
    ],

    "alignment_processing": [
        "Sequence alignment"
    ],

    "coverage_estimation": [
        "Sequence alignment analysis"
    ],

    "genome_binning": [
        "Genome binning"
    ],

    "bin_refinement": [
        "Genome binning"
    ],

    "mag_quality": [
        "Genome quality assessment"
    ],

    "mag_taxonomy": [
        "Taxonomic classification"
    ],

    "amr_detection": [
        "Antimicrobial resistance prediction"
    ],

    "virulence_profiling": [
        "Virulence prediction"
    ],

    "mlst_typing": [
        "Sequence typing"
    ],

    "species_identification": [
        "Taxonomic classification"
    ],

    "plasmid_detection": [
        "Plasmid detection"
    ],

    "prophage_detection": [
        "Prophage prediction"
    ],

    "variant_calling": [
        "Variant calling"
    ],

    "variant_filtering": [
        "Variant filtering"
    ],

    "pangenome_analysis": [
        "Pangenome analysis"
    ],

    "phylogenetic_inference": [
        "Phylogenetic tree generation"
    ],

    "rna_alignment": [
        "Sequence alignment"
    ],

    "gene_quantification": [
        "Gene expression profiling"
    ],

    "differential_expression": [
        "Differential expression analysis"
    ],

    "viral_detection": [
        "Virus detection"
    ],

    "viral_sequence_detection": [
        "Virus detection"
    ],

    "viral_taxonomy": [
        "Taxonomic classification"
    ]
}


# ==================================================
# HELPERS
# ==================================================

def _unique(
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


def _merge_candidate(
    existing,
    incoming
):
    """
    Merge registry metadata with the canonical capability seed.
    """

    result = existing.copy()

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
        "query_matches"
    ]

    for field in list_fields:

        result[
            field
        ] = _unique(
            (
                result.get(
                    field,
                    []
                )
                or
                []
            )
            +
            (
                incoming.get(
                    field,
                    []
                )
                or
                []
            )
        )

    for field in [
        "description",
        "homepage",
        "biotools_id",
        "biotools_url"
    ]:

        if incoming.get(
            field
        ):

            # Prefer structured registry descriptions/links where
            # available, while keeping capability metadata separately.
            result[
                field
            ] = incoming[
                field
            ]

    result[
        "publication_count"
    ] = max(
        result.get(
            "publication_count",
            0
        )
        or
        0,
        incoming.get(
            "publication_count",
            0
        )
        or
        0
    )

    result[
        "source_provenance"
    ] = (
        result.get(
            "source_provenance",
            []
        )
        or
        []
    ) + (
        incoming.get(
            "source_provenance",
            []
        )
        or
        []
    )

    if incoming.get(
        "capability_record"
    ):

        result[
            "capability_record"
        ] = incoming[
            "capability_record"
        ]

    if incoming.get(
        "capability_evaluation"
    ):

        result[
            "capability_evaluation"
        ] = incoming[
            "capability_evaluation"
        ]

    if incoming.get(
        "capability_id"
    ):

        result[
            "capability_id"
        ] = incoming[
            "capability_id"
        ]

    return result


def _candidate_identity(
    candidate
):
    """
    Prefer canonical capability identity, then bio.tools ID,
    then normalized name.
    """

    capability_id = candidate.get(
        "capability_id"
    )

    if capability_id:

        return (
            "capability",
            capability_id
        )

    biotools_id = candidate.get(
        "biotools_id"
    )

    if biotools_id:

        return (
            "biotools",
            str(
                biotools_id
            ).lower()
        )

    return (
        "name",
        normalize_name(
            candidate.get(
                "name"
            )
        )
    )


def _curated_capability_ids(
    curated_tools
):
    """
    Resolve current official step candidates to canonical resource IDs.
    This prevents the same underlying package from appearing twice
    merely because one card uses a component name.
    """

    ids = set()
    names = set()

    for tool in curated_tools or []:

        if not isinstance(
            tool,
            dict
        ):
            continue

        name = tool.get(
            "name"
        )

        if name:

            names.add(
                normalize_name(
                    name
                )
            )

            resource_id, _ = resolve_capability_record(
                name
            )

            if resource_id:

                ids.add(
                    resource_id
                )

    return ids, names


def _remove_curated(
    candidates,
    curated_tools
):

    curated_ids, curated_names = (
        _curated_capability_ids(
            curated_tools
        )
    )

    result = []

    for candidate in candidates:

        capability_id = candidate.get(
            "capability_id"
        )

        if (
            capability_id
            and
            capability_id
            in curated_ids
        ):

            continue

        if (
            normalize_name(
                candidate.get(
                    "name"
                )
            )
            in curated_names
        ):

            continue

        result.append(
            candidate
        )

    return result


# ==================================================
# SYSTEMATIC DISCOVERY V3
# ==================================================

def run_systematic_discovery(
    operation,
    context=None,
    curated_tools=None,
    registry_per_query=15,
    registry_max_total=100,
    literature_years=None,
    literature_max_queries=None,
    literature_per_source=None
):
    """
    BioFlow Research Engine v3.

    IMPORTANT DESIGN CHANGE
    -----------------------
    Candidate generation no longer mines arbitrary words from paper
    abstracts. That approach produced false tools and then became so
    restrictive that Deep discovery could return zero.

    Candidate generation now comes from:
      A. BioFlow's curated capability catalogue
      B. structured bio.tools registry searches

    Literature is reserved for the separate evidence-verification
    button after a named resource has been identified.

    Results are separated into:
      compatible_results
        direct alternatives for this exact operation + ASV/OTU context

      related_results
        relevant resources that use another feature strategy, represent
        an end-to-end service/framework, or need a different input route

      unverified_results
        registry leads whose ASV/OTU/marker capability has not yet been
        curated
    """

    context = (
        context
        if isinstance(
            context,
            dict
        )
        else
        {}
    )

    if not CAPABILITY_FILE.exists():

        return {
            "operation": operation,
            "context": context,
            "query_family": [],
            "structured_operation_terms": [],
            "compatible_results": [],
            "related_results": [],
            "unverified_results": [],
            "compatible_count": 0,
            "related_count": 0,
            "unverified_count": 0,
            "registry_candidate_count": 0,
            "catalogue_candidate_count": 0,
            "providers_searched": [],
            "partial_errors": [],
            "error": (
                "BioFlow capability catalogue is missing: "
                "data/resource_capabilities.yaml. "
                "Core curated workflows still work, but advanced discovery "
                "cannot run until this file is installed."
            )
        }

    curated_tools = (
        curated_tools
        if isinstance(
            curated_tools,
            list
        )
        else
        []
    )

    query_family = get_discovery_query_family(
        operation,
        context=context,
        max_queries=8
    )

    operation_terms = (
        BIOFLOW_TO_EDAM_OPERATION.get(
            operation,
            []
        )
        or
        []
    )

    # The structured operation field is the main lane. A few broad
    # free-text queries are kept to recover framework/web-service names
    # whose bio.tools operation annotation may be incomplete.
    broad_queries = query_family[
        :4
    ]

    registry_result = search_biotools_structured(
        operation_terms=operation_terms,
        query_terms=broad_queries,
        per_query=registry_per_query,
        max_total=registry_max_total
    )

    catalogue_candidates = capability_catalog_candidates(
        operation,
        context=context
    )

    merged = {}

    for candidate in catalogue_candidates:

        merged[
            _candidate_identity(
                candidate
            )
        ] = candidate

    for raw_candidate in registry_result.get(
        "results",
        []
    ) or []:

        candidate = attach_capability_to_registry_candidate(
            raw_candidate,
            operation,
            context=context
        )

        key = _candidate_identity(
            candidate
        )

        if key in merged:

            merged[
                key
            ] = _merge_candidate(
                merged[
                    key
                ],
                candidate
            )

        else:

            merged[
                key
            ] = candidate

    candidates = _remove_curated(
        list(
            merged.values()
        ),
        curated_tools
    )

    compatible = []
    related = []
    unverified = []

    for candidate in candidates:

        evaluation = (
            candidate.get(
                "capability_evaluation",
                {}
            )
            or
            {}
        )

        category = evaluation.get(
            "category",
            "unverified"
        )

        if category == "compatible":

            compatible.append(
                candidate
            )

        elif category == "related":

            related.append(
                candidate
            )

        elif category == "unverified":

            unverified.append(
                candidate
            )

    # Registry-only candidates still receive the old discovery-screening
    # score, but that score does NOT promote them to compatible.
    unverified = screen_discovered_tools(
        unverified,
        operation,
        context=context
    )

    compatible.sort(
        key=lambda item: (
            item.get(
                "name",
                ""
            ).lower()
        )
    )

    related.sort(
        key=lambda item: (
            item.get(
                "name",
                ""
            ).lower()
        )
    )

    return {
        "operation": operation,
        "context": context,
        "query_family": query_family,
        "structured_operation_terms": operation_terms,
        "compatible_results": compatible,
        "related_results": related,
        "unverified_results": unverified,
        "compatible_count": len(
            compatible
        ),
        "related_count": len(
            related
        ),
        "unverified_count": len(
            unverified
        ),
        "registry_candidate_count": len(
            registry_result.get(
                "results",
                []
            )
            or
            []
        ),
        "catalogue_candidate_count": len(
            catalogue_candidates
        ),
        "providers_searched": [
            "BioFlow capability catalogue",
            "bio.tools"
        ],
        "partial_errors": registry_result.get(
            "partial_errors",
            []
        )
        or
        [],
        "error": (
            registry_result.get(
                "error"
            )
            if (
                not compatible
                and
                not related
                and
                not unverified
            )
            else
            None
        )
    }
