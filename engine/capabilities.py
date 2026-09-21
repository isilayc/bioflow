from pathlib import Path
import re

import yaml


# ==================================================
# PATH / CACHE
# ==================================================

ENGINE_DIR = Path(
    __file__
).resolve().parent

APP_DIR = ENGINE_DIR.parent

CAPABILITY_FILE = (
    APP_DIR
    / "data"
    / "resource_capabilities.yaml"
)

_cache = {
    "signature": None,
    "data": {}
}


def _signature(
    path
):

    if not path.exists():
        return None

    stat = path.stat()

    return (
        stat.st_mtime_ns,
        stat.st_size
    )


def load_resource_capabilities():
    """
    Load BioFlow's curated resource-capability catalogue.

    This file is deliberately separate from tools.yaml:
    tools.yaml contains executable curated candidates used in
    official workflow rankings, while resource_capabilities.yaml
    can also describe frameworks, web services and whole workflows
    that are useful during discovery.
    """

    signature = _signature(
        CAPABILITY_FILE
    )

    if (
        _cache[
            "signature"
        ]
        ==
        signature
    ):

        return _cache[
            "data"
        ]

    if not CAPABILITY_FILE.exists():

        data = {}

    else:

        with open(
            CAPABILITY_FILE,
            "r",
            encoding="utf-8"
        ) as handle:

            data = (
                yaml.safe_load(
                    handle
                )
                or
                {}
            )

    if not isinstance(
        data,
        dict
    ):

        data = {}

    _cache[
        "signature"
    ] = signature

    _cache[
        "data"
    ] = data

    return data


# ==================================================
# NORMALIZATION
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
        .strip()
        .lower()
    )


def normalize_name(
    value
):

    if value is None:
        return ""

    return re.sub(
        r"[^a-z0-9]+",
        "",
        normalize_text(
            value
        )
    )


def _as_list(
    value
):

    if value is None:
        return []

    if isinstance(
        value,
        list
    ):
        return value

    if isinstance(
        value,
        tuple
    ):
        return list(
            value
        )

    return [
        value
    ]


def _contains_any_value(
    allowed,
    selected
):
    """
    Case-insensitive compatibility with `any` wildcard.
    """

    allowed_normalized = {
        normalize_text(
            item
        )
        for item
        in _as_list(
            allowed
        )
        if item is not None
    }

    if not allowed_normalized:
        return True

    if (
        "any"
        in allowed_normalized
        or
        "*"
        in allowed_normalized
    ):
        return True

    selected_values = {
        normalize_text(
            item
        )
        for item
        in _as_list(
            selected
        )
        if item not in (
            None,
            ""
        )
    }

    if not selected_values:
        return True

    return bool(
        allowed_normalized
        &
        selected_values
    )


# ==================================================
# CONTEXT RESOLUTION
# ==================================================

def infer_marker(
    context
):
    """
    Infer amplicon marker only when BioFlow has enough context.

    Generic amplicon goals remain `any`; the engine does not guess.
    """

    if not isinstance(
        context,
        dict
    ):
        return "any"

    explicit = context.get(
        "marker"
    )

    if explicit:
        return str(
            explicit
        )

    combined = " ".join(
        str(
            context.get(
                field,
                ""
            )
        )
        for field
        in [
            "goal",
            "workflow_name"
        ]
    ).lower()

    if "16s" in combined:
        return "16S"

    if "18s" in combined:
        return "18S"

    if re.search(
        r"\bits\b",
        combined
    ):
        return "ITS"

    if re.search(
        r"\bcoi\b",
        combined
    ):
        return "COI"

    return "any"


def infer_feature_strategy(
    context
):
    """
    Resolve ASV / OTU / MOTU from explicit workflow context first.

    Name-based inference is only a backward-compatible fallback.
    """

    if not isinstance(
        context,
        dict
    ):
        return None

    explicit = normalize_text(
        context.get(
            "feature_strategy"
        )
    )

    if explicit in (
        "asv",
        "otu",
        "motu"
    ):
        return explicit

    combined = " ".join(
        str(
            context.get(
                field,
                ""
            )
        )
        for field
        in [
            "workflow_name",
            "goal"
        ]
    ).lower()

    if "asv" in combined:
        return "asv"

    if "otu" in combined:
        return "otu"

    return None


# ==================================================
# ENTITY RESOLUTION
# ==================================================

def build_alias_index(
    catalogue=None
):
    """
    Map exact normalized aliases to canonical resource IDs.

    SILVA and SILVAngs therefore remain distinct entities.
    """

    catalogue = (
        catalogue
        if isinstance(
            catalogue,
            dict
        )
        else
        load_resource_capabilities()
    )

    index = {}

    for resource_id, record in catalogue.items():

        values = [
            resource_id,
            record.get(
                "name"
            )
        ]

        values.extend(
            record.get(
                "aliases",
                []
            )
            or
            []
        )

        for value in values:

            key = normalize_name(
                value
            )

            if key:

                index[
                    key
                ] = resource_id

    return index


def resolve_capability_record(
    candidate_name,
    catalogue=None
):
    """
    Return (resource_id, record) for an exact alias match.
    """

    catalogue = (
        catalogue
        if isinstance(
            catalogue,
            dict
        )
        else
        load_resource_capabilities()
    )

    alias_index = build_alias_index(
        catalogue
    )

    resource_id = alias_index.get(
        normalize_name(
            candidate_name
        )
    )

    if not resource_id:

        return (
            None,
            None
        )

    return (
        resource_id,
        catalogue.get(
            resource_id
        )
    )


# ==================================================
# CAPABILITY EVALUATION
# ==================================================

def evaluate_capability(
    record,
    operation,
    context=None
):
    """
    Classify one known resource relative to one BioFlow step.

    Categories:
      compatible
        Directly appropriate for this selected strategy/operation.

      related
        Scientifically relevant, but it represents another feature
        strategy, a whole workflow/framework, or requires a different
        input shape. It must not be shown as a drop-in recommendation.

      excluded
        No meaningful capability relation to this operation/context.
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

    if not isinstance(
        record,
        dict
    ):

        return {
            "category": "unverified",
            "reasons": [
                "No curated capability record is available."
            ]
        }

    selected_strategy = infer_feature_strategy(
        context
    )

    selected_marker = infer_marker(
        context
    )

    selected_sequencing = context.get(
        "sequencing"
    )

    selected_read_type = context.get(
        "read_type"
    )

    operations = {
        normalize_text(
            item
        )
        for item in (
            record.get(
                "operations",
                []
            )
            or
            []
        )
    }

    requested_operation = normalize_text(
        operation
    )

    operation_profile = (
        (
            record.get(
                "operation_profiles",
                {}
            )
            or
            {}
        ).get(
            operation,
            {}
        )
        or
        {}
    )

    operation_match = (
        requested_operation
        in operations
    )

    # ASV, classical OTU and PCR-aware MOTU methods are different
    # feature-generation strategies, but they are scientifically
    # relevant alternatives at the same decision point. Keep them
    # visible as RELATED rather than pretending they are equivalent.
    feature_generation_operations = {
        "asv_inference",
        "otu_clustering",
        "pcr_aware_denoising"
    }

    peer_feature_generation_match = (
        requested_operation
        in
        feature_generation_operations
        and
        bool(
            operations
            &
            feature_generation_operations
        )
    )

    if (
        not operation_match
        and
        not peer_feature_generation_match
    ):

        return {
            "category": "excluded",
            "reasons": [
                "The curated resource record does not support this BioFlow operation."
            ]
        }

    reasons = []

    if (
        peer_feature_generation_match
        and
        not operation_match
    ):

        reasons.append(
            "This resource addresses the same amplicon feature-generation decision, "
            "but with a different inference/clustering strategy."
        )

    feature_strategies = {
        normalize_text(
            item
        )
        for item in (
            operation_profile.get(
                "feature_strategies",
                record.get(
                    "feature_strategies",
                    []
                )
            )
            or
            []
        )
    }

    strategy_match = True

    if (
        selected_strategy
        and
        feature_strategies
        and
        selected_strategy
        not in feature_strategies
    ):

        strategy_match = False

        readable = "/".join(
            sorted(
                feature_strategies
            )
        )

        reasons.append(
            f"Different feature strategy: this resource is curated for "
            f"{readable}, while the selected workflow is {selected_strategy}."
        )

    marker_match = _contains_any_value(
        record.get(
            "markers"
        ),
        selected_marker
    )

    if not marker_match:

        return {
            "category": "excluded",
            "feature_strategy": selected_strategy,
            "marker": selected_marker,
            "resource_type": record.get(
                "resource_type",
                "resource"
            ),
            "scope": operation_profile.get(
                "scope",
                record.get(
                    "scope",
                    "step"
                )
            ),
            "reasons": [
                f"Marker mismatch: the selected marker is {selected_marker}."
            ]
        }

    sequencing_match = _contains_any_value(
        record.get(
            "sequencing"
        ),
        selected_sequencing
    )

    if not sequencing_match:

        reasons.append(
            "The selected sequencing technology is outside the curated capability record."
        )

    read_type_match = _contains_any_value(
        record.get(
            "read_types"
        ),
        selected_read_type
    )

    if not read_type_match:

        requirements = (
            record.get(
                "requirements",
                []
            )
            or
            []
        )

        if requirements:

            reasons.extend(
                requirements
            )

        else:

            reasons.append(
                "The selected read/input type does not directly match this resource."
            )

    scope = normalize_text(
        operation_profile.get(
            "scope",
            record.get(
                "scope",
                "step"
            )
        )
    )

    if requested_operation == "amplicon_end_to_end":

        scope_is_direct = scope in (
            "end_to_end",
            "framework",
            "composable_workflow",
            "step_and_workflow"
        )

    else:

        scope_is_direct = scope in (
            "step",
            "step_and_workflow"
        )

    if not scope_is_direct:

        if scope == "end_to_end":

            reasons.append(
                "This is an end-to-end workflow/service, not a drop-in replacement for this single step."
            )

        elif scope == "framework":

            reasons.append(
                "This is a framework; the relevant plugin/component should be named for a step-level recommendation."
            )

        elif scope == "multi_step":

            reasons.append(
                "This capability requires a multi-step subworkflow rather than a single drop-in command."
            )

        elif scope == "composable_workflow":

            reasons.append(
                "This is a composable toolkit/workflow and represents a different analysis route."
            )

    if (
        strategy_match
        and
        marker_match
        and
        sequencing_match
        and
        read_type_match
        and
        scope_is_direct
        and
        operation_match
    ):

        category = "compatible"

        reasons.insert(
            0,
            "Curated capability matches the selected operation and workflow strategy."
        )

    else:

        category = "related"

    return {
        "category": category,
        "feature_strategy": selected_strategy,
        "marker": selected_marker,
        "resource_type": record.get(
            "resource_type",
            "resource"
        ),
        "scope": operation_profile.get(
            "scope",
            record.get(
                "scope",
                "step"
            )
        ),
        "reasons": reasons
    }


# ==================================================
# CATALOGUE CANDIDATES
# ==================================================

def capability_catalog_candidates(
    operation,
    context=None
):
    """
    Return all curated capability-catalogue resources that support
    the requested operation.

    Both direct-compatible and scientifically related resources are
    returned. The UI decides which section to display them in.
    """

    catalogue = load_resource_capabilities()

    candidates = []

    for resource_id, record in catalogue.items():

        evaluation = evaluate_capability(
            record,
            operation,
            context=context
        )

        if evaluation.get(
            "category"
        ) == "excluded":

            continue

        operation_profile = (
            (
                record.get(
                    "operation_profiles",
                    {}
                )
                or
                {}
            ).get(
                operation,
                {}
            )
            or
            {}
        )

        candidate = {
            "name": (
                operation_profile.get(
                    "display_name"
                )
                or
                record.get(
                    "name"
                )
                or
                resource_id
            ),
            "capability_id": resource_id,
            "description": (
                " ".join(
                    record.get(
                        "notes",
                        []
                    )
                    or
                    []
                )
            ),
            "homepage": (
                (
                    record.get(
                        "evidence_urls",
                        []
                    )
                    or
                    [
                        None
                    ]
                )[
                    0
                ]
            ),
            "biotools_id": None,
            "biotools_url": None,
            "operations": record.get(
                "operations",
                []
            )
            or
            [],
            "topics": [],
            "input_data": [],
            "input_formats": record.get(
                "input_formats",
                []
            )
            or
            [],
            "output_data": [],
            "output_formats": [],
            "publication_count": 0,
            "resource_types": [
                record.get(
                    "resource_type",
                    "resource"
                )
            ],
            "operating_systems": [],
            "languages": [],
            "discovery_sources": [
                "BioFlow capability catalogue"
            ],
            "query_matches": [],
            "source_provenance": [
                {
                    "source": "BioFlow capability catalogue",
                    "query": operation,
                    "url": url
                }
                for url
                in (
                    record.get(
                        "evidence_urls",
                        []
                    )
                    or
                    []
                )
            ],
            "capability_record": record,
            "capability_evaluation": evaluation
        }

        candidates.append(
            candidate
        )

    return candidates


def attach_capability_to_registry_candidate(
    candidate,
    operation,
    context=None
):
    """
    Resolve a structured-registry result against the curated
    capability catalogue.

    Unknown registry candidates remain `unverified`; BioFlow does
    not infer ASV/OTU compatibility from a tool name alone.
    """

    if not isinstance(
        candidate,
        dict
    ):

        return candidate

    result = candidate.copy()

    resource_id, record = resolve_capability_record(
        result.get(
            "name"
        )
    )

    if record is None:

        result[
            "capability_evaluation"
        ] = {
            "category": "unverified",
            "reasons": [
                "Structured registry hit; ASV/OTU/marker capability has not yet been curated."
            ]
        }

        return result

    result[
        "capability_id"
    ] = resource_id

    result[
        "capability_record"
    ] = record

    result[
        "capability_evaluation"
    ] = evaluate_capability(
        record,
        operation,
        context=context
    )

    sources = list(
        result.get(
            "discovery_sources",
            []
        )
        or
        []
    )

    if (
        "BioFlow capability catalogue"
        not in sources
    ):

        sources.append(
            "BioFlow capability catalogue"
        )

    result[
        "discovery_sources"
    ] = sources

    return result
