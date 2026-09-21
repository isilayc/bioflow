from pathlib import Path

import yaml

from engine.compatibility import (
    check_tool_compatibility
)

from engine.scoring import (
    calculate_tool_score,
    scientific_fit_priority,
    operational_hard_gate_priority
)

from engine.feasibility import (
    evaluate_operational_feasibility,
    operational_status_priority
)


# ==================================================
# PATHS
# ==================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DATA_DIR = (
    BASE_DIR
    / "data"
)


# ==================================================
# YAML LOADING
# ==================================================

# Streamlit reruns app.py after most UI interactions, but imported
# modules remain loaded. Keeping parsed YAML data here avoids reparsing
# the same files on every dropdown change. The cache is automatically
# invalidated when a YAML file changes on disk.
_YAML_CACHE = {}


def _yaml_file_signature(filepath):
    """Return a lightweight signature that changes when the file changes."""

    stat = filepath.stat()

    return (
        stat.st_mtime_ns,
        stat.st_size
    )


def clear_yaml_cache():
    """Clear BioFlow's in-process YAML cache manually if ever needed."""

    _YAML_CACHE.clear()


def load_yaml(filename):
    """
    Load a YAML file from the BioFlow data directory.

    Parsed data is cached by filename + file modification signature,
    so editing the YAML automatically refreshes the cached value.
    """

    filepath = (
        DATA_DIR
        / filename
    )

    signature = (
        _yaml_file_signature(
            filepath
        )
    )

    cached = (
        _YAML_CACHE.get(
            filename
        )
    )

    if (
        cached
        and
        cached.get(
            "signature"
        )
        ==
        signature
    ):

        return cached[
            "data"
        ]

    with open(
        filepath,
        "r",
        encoding="utf-8"
    ) as file:

        data = yaml.safe_load(
            file
        )

    if data is None:
        data = {}

    _YAML_CACHE[
        filename
    ] = {
        "signature": signature,
        "data": data
    }

    return data


def load_tools():
    """
    Load tools.yaml.
    """

    return load_yaml(
        "tools.yaml"
    )


def load_workflows():
    """
    Load workflows.yaml.
    """

    return load_yaml(
        "workflows.yaml"
    )


def load_optional_yaml(filename):
    """
    Load an optional YAML file from the BioFlow data
    directory.

    Missing optional metadata must not break the core
    recommender.
    """

    filepath = (
        DATA_DIR
        / filename
    )

    if not filepath.exists():

        return {}

    return load_yaml(
        filename
    )


def load_strategy_fit():
    """
    Load optional strategy-specific tool-fit metadata.
    """

    return load_optional_yaml(
        "strategy_fit.yaml"
    )


# ==================================================
# UTILITIES
# ==================================================

def unique_preserve_order(values):
    """
    Remove duplicate values while preserving order.
    """

    result = []
    seen = set()

    for value in values:

        if value is None:
            continue

        key = str(value)

        if key not in seen:

            seen.add(
                key
            )

            result.append(
                value
            )

    return result


def format_context_value(value):
    """
    Convert a workflow context value into a
    human-readable string.

    Examples:

    "Illumina"
        -> "Illumina"

    ["Illumina", "Oxford Nanopore"]
        -> "Illumina + Oxford Nanopore"

    ["Paired-end", "Long reads"]
        -> "Paired-end + Long reads"
    """

    if isinstance(
        value,
        (
            list,
            tuple,
            set
        )
    ):

        return " + ".join(
            str(item)
            for item in value
        )

    if value is None:
        return ""

    return str(value)


def format_context(context):
    """
    Convert workflow context values into UI-safe strings while
    preserving BioFlow's scientific strategy metadata.

    Earlier versions returned only sample_type/sequencing/read_type/goal.
    That silently discarded keys such as feature_strategy and marker,
    which is why the Research panel showed "NOT SPECIFIED" even though
    those values were present in workflows.yaml.
    """

    if not isinstance(
        context,
        dict
    ):

        return {}

    formatted = {}

    for key, value in context.items():

        if isinstance(
            value,
            (
                list,
                tuple,
                set
            )
        ):

            formatted[
                key
            ] = [
                format_context_value(
                    item
                )
                for item
                in value
            ]

        elif isinstance(
            value,
            dict
        ):

            formatted[
                key
            ] = value.copy()

        else:

            formatted[
                key
            ] = (
                format_context_value(
                    value
                )
            )

    for required_key in [
        "sample_type",
        "sequencing",
        "read_type",
        "goal"
    ]:

        formatted.setdefault(
            required_key,
            ""
        )

    return formatted


# ==================================================
# DYNAMIC UI OPTIONS
# ==================================================

def get_sample_types():
    """
    Return all sample types currently represented
    in workflows.yaml.
    """

    workflows = (
        load_workflows()
    )

    values = []

    for workflow in workflows.values():

        context = (
            workflow.get(
                "context",
                {}
            )
        )

        value = (
            format_context_value(
                context.get(
                    "sample_type"
                )
            )
        )

        if value:

            values.append(
                value
            )

    return unique_preserve_order(
        values
    )


def get_sequencing_options(
    sample_type
):
    """
    Return sequencing options available for the
    selected sample type.

    Hybrid workflow lists are displayed as:

    Illumina + Oxford Nanopore
    """

    workflows = (
        load_workflows()
    )

    values = []

    for workflow in workflows.values():

        context = (
            workflow.get(
                "context",
                {}
            )
        )

        workflow_sample = (
            format_context_value(
                context.get(
                    "sample_type"
                )
            )
        )

        if workflow_sample == sample_type:

            value = (
                format_context_value(
                    context.get(
                        "sequencing"
                    )
                )
            )

            if value:

                values.append(
                    value
                )

    return unique_preserve_order(
        values
    )


def get_read_type_options(
    sample_type,
    sequencing
):
    """
    Return read types available for the selected
    sample type and sequencing combination.
    """

    workflows = (
        load_workflows()
    )

    values = []

    for workflow in workflows.values():

        context = (
            workflow.get(
                "context",
                {}
            )
        )

        workflow_sample = (
            format_context_value(
                context.get(
                    "sample_type"
                )
            )
        )

        workflow_sequencing = (
            format_context_value(
                context.get(
                    "sequencing"
                )
            )
        )

        if (
            workflow_sample
            == sample_type

            and

            workflow_sequencing
            == sequencing
        ):

            value = (
                format_context_value(
                    context.get(
                        "read_type"
                    )
                )
            )

            if value:

                values.append(
                    value
                )

    return unique_preserve_order(
        values
    )


def get_goal_options(
    sample_type,
    sequencing,
    read_type
):
    """
    Return analysis goals available for the exact
    selected data context.
    """

    workflows = (
        load_workflows()
    )

    values = []

    for workflow in workflows.values():

        context = (
            workflow.get(
                "context",
                {}
            )
        )

        workflow_sample = (
            format_context_value(
                context.get(
                    "sample_type"
                )
            )
        )

        workflow_sequencing = (
            format_context_value(
                context.get(
                    "sequencing"
                )
            )
        )

        workflow_read_type = (
            format_context_value(
                context.get(
                    "read_type"
                )
            )
        )

        if (
            workflow_sample
            == sample_type

            and

            workflow_sequencing
            == sequencing

            and

            workflow_read_type
            == read_type
        ):

            value = (
                format_context_value(
                    context.get(
                        "goal"
                    )
                )
            )

            if value:

                values.append(
                    value
                )

    return unique_preserve_order(
        values
    )


# ==================================================
# FIND WORKFLOW / STRATEGIES
# ==================================================

def workflow_matches_selection(
    workflow,
    sample_type,
    sequencing,
    read_type,
    goal
):
    """
    Return True when a workflow matches the exact
    human-readable UI context.
    """

    context = (
        workflow.get(
            "context",
            {}
        )
    )

    formatted_context = (
        format_context(
            context
        )
    )

    return (
        formatted_context[
            "sample_type"
        ]
        == sample_type

        and

        formatted_context[
            "sequencing"
        ]
        == sequencing

        and

        formatted_context[
            "read_type"
        ]
        == read_type

        and

        formatted_context[
            "goal"
        ]
        == goal
    )


def find_workflows(
    sample_type,
    sequencing,
    read_type,
    goal
):
    """
    Return every workflow matching one biological goal
    and dataset context.

    Multiple matches are intentional: BioFlow can model
    distinct technical strategies that reach the same
    biological goal, for example alignment-based and
    lightweight RNA-seq differential expression.
    """

    workflows = (
        load_workflows()
    )

    matches = []

    for (
        workflow_id,
        workflow
    ) in workflows.items():

        if workflow_matches_selection(
            workflow,
            sample_type,
            sequencing,
            read_type,
            goal
        ):

            matches.append(
                (
                    workflow_id,
                    workflow
                )
            )

    return matches


def get_workflow_strategies(
    sample_type,
    sequencing,
    read_type,
    goal
):
    """
    Return workflow strategy records for the selected
    dataset context and biological goal.

    The UI uses this to let the user choose between
    genuinely different end-to-end strategies instead
    of treating them as tool-level alternatives.
    """

    matches = (
        find_workflows(
            sample_type,
            sequencing,
            read_type,
            goal
        )
    )

    strategies = []

    for workflow_id, workflow in matches:

        strategies.append(
            {
                "id": workflow_id,
                "name": workflow.get(
                    "name",
                    workflow_id
                ),
                "description": workflow.get(
                    "description",
                    ""
                )
            }
        )

    return strategies


def find_workflow(
    sample_type,
    sequencing,
    read_type,
    goal
):
    """
    Backward-compatible helper returning the first
    workflow matching the selected UI context.

    New UI code should use get_workflow_strategies()
    when multiple strategies may exist.
    """

    matches = (
        find_workflows(
            sample_type,
            sequencing,
            read_type,
            goal
        )
    )

    if not matches:

        return (
            None,
            None
        )

    return matches[0]


# ==================================================
# TOOL ACCESS
# ==================================================

def get_tool(tool_id):
    """
    Retrieve one tool from tools.yaml.
    """

    tools = (
        load_tools()
    )

    return tools.get(
        tool_id
    )


# ==================================================
# STRATEGY-SPECIFIC TOOL FIT
# ==================================================

def get_strategy_fit(
    workflow_id,
    operation,
    tool_id
):
    """
    Return curated strategy-specific metadata for one
    workflow + operation + tool combination.

    Missing metadata returns None so all existing
    workflows keep their original BioFlow scores.
    """

    data = (
        load_strategy_fit()
    )

    workflows = (
        data.get(
            "workflows",
            {}
        )
    )

    if not isinstance(
        workflows,
        dict
    ):

        return None

    workflow_definition = (
        workflows.get(
            workflow_id,
            {}
        )
    )

    if not isinstance(
        workflow_definition,
        dict
    ):

        return None

    operations = (
        workflow_definition.get(
            "operations",
            {}
        )
    )

    if not isinstance(
        operations,
        dict
    ):

        return None

    operation_definition = (
        operations.get(
            operation,
            {}
        )
    )

    if not isinstance(
        operation_definition,
        dict
    ):

        return None

    tool_definition = (
        operation_definition.get(
            tool_id
        )
    )

    if not isinstance(
        tool_definition,
        dict
    ):

        return None

    return (
        tool_definition.copy()
    )


# ==================================================
# STEP CANDIDATES
# ==================================================

def get_step_candidates(step):
    """
    Return candidate tool IDs for a workflow step.

    Current format:

    candidates:
      - tool1
      - tool2

    The old preferred/alternatives format is still
    supported as a fallback so older entries do not
    crash BioFlow.
    """

    candidates = (
        step.get(
            "candidates"
        )
    )

    if candidates:

        return (
            unique_preserve_order(
                candidates
            )
        )

    legacy_candidates = []

    preferred = (
        step.get(
            "preferred"
        )
    )

    if preferred:

        legacy_candidates.append(
            preferred
        )

    legacy_candidates.extend(
        step.get(
            "alternatives",
            []
        )
    )

    return (
        unique_preserve_order(
            legacy_candidates
        )
    )


# ==================================================
# STEP-SPECIFIC CONTEXT
# ==================================================

def get_effective_step_context(
    workflow_context,
    step
):
    """
    Determine the biological/sequencing context
    used for a specific workflow step.

    A step may override workflow-level sequencing
    and read type.

    Example:

    Workflow:
        sequencing:
          - Illumina
          - Oxford Nanopore

        read_type:
          - Paired-end
          - Long reads

    FastQC step:
        context:
          sequencing: Illumina
          read_type: Paired-end

    NanoPlot step:
        context:
          sequencing: Oxford Nanopore
          read_type: Long reads
    """

    step_context = (
        step.get(
            "context",
            {}
        )
    )

    return {
        "sample_type": (
            step_context.get(
                "sample_type",
                workflow_context.get(
                    "sample_type"
                )
            )
        ),

        "sequencing": (
            step_context.get(
                "sequencing",
                workflow_context.get(
                    "sequencing"
                )
            )
        ),

        "read_type": (
            step_context.get(
                "read_type",
                workflow_context.get(
                    "read_type"
                )
            )
        )
    }


# ==================================================
# PREPARE TOOL
# ==================================================

def prepare_tool(
    tool_id,
    sample_type,
    sequencing,
    read_type,
    operation,
    strategy_fit=None,
    compute_profile=None
):
    """
    Load a tool and calculate compatibility,
    BioFlow base score and optional strategy-specific
    suitability score.
    """

    tool = (
        get_tool(
            tool_id
        )
    )

    if tool is None:

        return None

    compatibility = (
        check_tool_compatibility(
            tool,
            sample_type,
            sequencing,
            read_type
        )
    )

    tool = (
        tool.copy()
    )

    tool[
        "id"
    ] = tool_id

    tool[
        "compatible"
    ] = (
        compatibility[
            "compatible"
        ]
    )

    tool[
        "compatibility_problems"
    ] = (
        compatibility[
            "problems"
        ]
    )

    tool[
        "strategy_fit"
    ] = (
        strategy_fit.copy()
        if isinstance(
            strategy_fit,
            dict
        )
        else
        None
    )

    tool[
        "score"
    ] = (
        calculate_tool_score(
            tool,
            operation,
            strategy_fit=(
                strategy_fit
            )
        )
    )

    tool[
        "operational_fit"
    ] = (
        evaluate_operational_feasibility(
            tool,
            compute_profile,
            operation=operation
        )
    )

    return tool


# ==================================================
# BUILD WORKFLOW
# ==================================================

def build_workflow(
    sample_type,
    sequencing,
    read_type,
    goal,
    workflow_id=None,
    compute_profile=None
):
    """
    Build one complete BioFlow workflow.

    workflow_id is optional for backward compatibility.
    When supplied, it selects a specific end-to-end
    strategy among multiple workflows that implement the
    same biological goal.

    Step execution semantics are preserved:
      sequential -> candidate tools are alternatives
      parallel   -> candidate tools are independent
                    co-executed branches
    """

    workflows = (
        load_workflows()
    )

    if workflow_id is not None:

        workflow = (
            workflows.get(
                workflow_id
            )
        )

        if workflow is None:

            return None

        if not workflow_matches_selection(
            workflow,
            sample_type,
            sequencing,
            read_type,
            goal
        ):

            return None

    else:

        (
            workflow_id,
            workflow
        ) = find_workflow(
            sample_type,
            sequencing,
            read_type,
            goal
        )

        if workflow is None:

            return None

    workflow_context = (
        workflow.get(
            "context",
            {}
        )
    )

    external_inputs = (
        workflow.get(
            "external_inputs",
            []
        )
        or
        []
    )

    if isinstance(
        external_inputs,
        str
    ):

        external_inputs = [
            external_inputs
        ]

    result = {
        "id": (
            workflow_id
        ),

        "name": (
            workflow.get(
                "name",
                workflow_id
            )
        ),

        "description": (
            workflow.get(
                "description",
                ""
            )
        ),

        # Streamlit currently works with
        # human-readable strings.
        "context": (
            format_context(
                workflow_context
            )
        ),

        # Preserve machine-readable user prerequisites
        # for explicit display in the UI.
        "external_inputs": (
            unique_preserve_order(
                external_inputs
            )
        ),

        "steps": []
    }

    for step in workflow.get(
        "steps",
        []
    ):

        operation = (
            step.get(
                "operation"
            )
        )

        mode = (
            step.get(
                "mode",
                "sequential"
            )
            or
            "sequential"
        )

        mode = (
            str(mode)
            .strip()
            .lower()
        )

        candidate_ids = (
            get_step_candidates(
                step
            )
        )

        effective_context = (
            get_effective_step_context(
                workflow_context,
                step
            )
        )

        candidate_tools = []

        for tool_id in candidate_ids:

            strategy_fit = (
                get_strategy_fit(
                    workflow_id,
                    operation,
                    tool_id
                )
            )

            tool = (
                prepare_tool(
                    tool_id,
                    effective_context[
                        "sample_type"
                    ],
                    effective_context[
                        "sequencing"
                    ],
                    effective_context[
                        "read_type"
                    ],
                    operation,
                    strategy_fit=(
                        strategy_fit
                    ),
                    compute_profile=(
                        compute_profile
                    )
                )
            )

            if tool is not None:

                candidate_tools.append(
                    tool
                )

        # Sequential candidates are alternatives, so a
        # score-based order is useful. Parallel branches
        # are co-executed and keep their curated YAML order.
        if mode != "parallel":

            if (
                isinstance(
                    compute_profile,
                    dict
                )
                and
                compute_profile.get(
                    "enabled",
                    False
                )
            ):

                candidate_tools.sort(
                    key=lambda item: (
                        operational_hard_gate_priority(
                            item.get(
                                "operational_fit",
                                {}
                            ).get(
                                "status",
                                "unknown"
                            ),
                            enabled=True
                        ),

                        scientific_fit_priority(
                            item.get(
                                "score",
                                {}
                            ).get(
                                "scientific_fit_label",
                                "curated"
                            )
                        ),

                        operational_status_priority(
                            item.get(
                                "operational_fit",
                                {}
                            ).get(
                                "status",
                                "unknown"
                            )
                        ),

                        item.get(
                            "score",
                            {}
                        ).get(
                            "total",
                            0
                        )
                    ),
                    reverse=True
                )

            else:

                candidate_tools.sort(
                    key=lambda item: (
                        scientific_fit_priority(
                            item.get(
                                "score",
                                {}
                            ).get(
                                "scientific_fit_label",
                                "curated"
                            )
                        ),

                        item.get(
                            "score",
                            {}
                        ).get(
                            "total",
                            0
                        )
                    ),
                    reverse=True
                )

        aggregate_produces = (
            step.get(
                "aggregate_produces",
                []
            )
            or
            []
        )

        if isinstance(
            aggregate_produces,
            str
        ):

            aggregate_produces = [
                aggregate_produces
            ]

        min_successful_candidates = (
            step.get(
                "min_successful_candidates",
                1
            )
            or
            1
        )

        try:

            min_successful_candidates = int(
                min_successful_candidates
            )

        except (
            TypeError,
            ValueError
        ):

            min_successful_candidates = 1

        result[
            "steps"
        ].append(
            {
                "operation": (
                    operation
                ),

                "name": (
                    step.get(
                        "name",
                        operation
                        or
                        "Unnamed step"
                    )
                ),

                "description": (
                    step.get(
                        "description",
                        ""
                    )
                ),

                "context": (
                    {
                        **(
                            format_context(
                                workflow_context
                            )
                        ),

                        **(
                            format_context(
                                step.get(
                                    "context",
                                    {}
                                )
                            )
                        ),

                        "sample_type": (
                            format_context_value(
                                effective_context[
                                    "sample_type"
                                ]
                            )
                        ),

                        "sequencing": (
                            format_context_value(
                                effective_context[
                                    "sequencing"
                                ]
                            )
                        ),

                        "read_type": (
                            format_context_value(
                                effective_context[
                                    "read_type"
                                ]
                            )
                        )
                    }
                ),

                "mode": mode,

                "min_successful_candidates": (
                    min_successful_candidates
                ),

                "aggregate_produces": (
                    unique_preserve_order(
                        aggregate_produces
                    )
                ),

                "candidate_ids": (
                    candidate_ids
                ),

                "tools": (
                    candidate_tools
                )
            }
        )

    return result
