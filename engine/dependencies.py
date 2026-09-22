from pathlib import Path
from functools import lru_cache

import yaml


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
# YAML
# ==================================================

# DEPENDENCY_PERFORMANCE_V1
def _data_file_signature(filename):
    filepath = DATA_DIR / filename
    stat = filepath.stat()
    return (stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=32)
def _load_yaml_cached(filename, modified_ns, file_size):
    filepath = DATA_DIR / filename
    with open(filepath, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if data is None:
        return {}
    return data


def load_yaml(filename):
    modified_ns, file_size = _data_file_signature(filename)
    return _load_yaml_cached(filename, modified_ns, file_size)


def load_artifacts():

    return load_yaml(
        "artifacts.yaml"
    )


def load_tool_io():

    return load_yaml(
        "tool_io.yaml"
    )


def load_workflows():

    return load_yaml(
        "workflows.yaml"
    )


# ==================================================
# GENERAL UTILITIES
# ==================================================

def as_list(value):

    if value is None:
        return []

    if isinstance(
        value,
        (
            list,
            tuple,
            set
        )
    ):

        return list(
            value
        )

    return [
        value
    ]


def unique_preserve_order(values):

    result = []
    seen = set()

    for value in values:

        if value is None:
            continue

        key = str(
            value
        )

        if key not in seen:

            seen.add(
                key
            )

            result.append(
                value
            )

    return result


# ==================================================
# ARTIFACT UTILITIES
# ==================================================

def get_artifact_label(
    artifact_id
):

    artifacts = (
        load_artifacts()
    )

    record = (
        artifacts.get(
            artifact_id,
            {}
        )
    )

    return record.get(
        "label",
        artifact_id
    )


@lru_cache(maxsize=4096)
def _expand_artifacts_cached(artifact_key, modified_ns, file_size):
    artifacts = load_artifacts()
    expanded = set(artifact_key)
    changed = True
    while changed:
        changed = False
        for artifact_id in list(expanded):
            record = artifacts.get(artifact_id, {})
            for provided in record.get("provides", []):
                if provided not in expanded:
                    expanded.add(provided)
                    changed = True
    return frozenset(expanded)


def expand_artifacts(artifact_ids):
    artifact_key = tuple(sorted(str(item) for item in artifact_ids))
    modified_ns, file_size = _data_file_signature("artifacts.yaml")
    return set(
        _expand_artifacts_cached(
            artifact_key,
            modified_ns,
            file_size
        )
    )


# ==================================================
# INITIAL WORKFLOW INPUTS
# ==================================================

def infer_initial_artifacts(
    workflow
):
    """
    Infer user-provided raw data from workflow context.

    Additional externally supplied resources may be
    explicitly defined through:

    external_inputs:
      - reference_genome_fasta
    """

    context = (
        workflow.get(
            "context",
            {}
        )
    )

    read_types = (
        []
        if workflow.get(
            "infer_read_inputs",
            True
        )
        is False
        else
        as_list(
            context.get(
                "read_type"
            )
        )
    )

    initial = set()

    for read_type in read_types:

        normalized = (
            str(
                read_type
            )
            .strip()
            .lower()
        )

        if normalized == "paired-end":

            initial.add(
                "raw_paired_fastq"
            )

        elif normalized == "single-end":

            initial.add(
                "raw_single_fastq"
            )

        elif normalized == "long reads":

            initial.add(
                "raw_long_fastq"
            )

    external_inputs = []

    external_inputs.extend(
        workflow.get(
            "external_inputs",
            []
        )
    )

    external_inputs.extend(
        context.get(
            "external_inputs",
            []
        )
    )

    initial.update(
        external_inputs
    )

    return initial


# ==================================================
# TOOL ROUTES
# ==================================================

def get_tool_routes(
    tool_id
):

    tool_io = (
        load_tool_io()
    )

    record = (
        tool_io.get(
            tool_id
        )
    )

    if record is None:
        return None

    return record.get(
        "routes",
        []
    )


def route_missing_inputs(
    route,
    available
):

    expanded_available = (
        expand_artifacts(
            available
        )
    )

    required = set(
        route.get(
            "requires",
            []
        )
    )

    return (
        required
        -
        expanded_available
    )


def get_runnable_routes(
    tool_id,
    state
):
    """
    Return all routes for one tool that can execute
    from the supplied artifact state.
    """

    routes = (
        get_tool_routes(
            tool_id
        )
    )

    if routes is None:

        return None

    runnable = []

    for route in routes:

        missing = (
            route_missing_inputs(
                route,
                state
            )
        )

        if not missing:

            runnable.append(
                route
            )

    return runnable


def get_best_missing_inputs(
    tool_id,
    states
):
    """
    Find the smallest missing-input set across all
    possible states and routes.

    Used only for readable validation reports.
    """

    routes = (
        get_tool_routes(
            tool_id
        )
    )

    if routes is None:

        return None

    best_missing = None

    for state in states:

        for route in routes:

            missing = (
                route_missing_inputs(
                    route,
                    state
                )
            )

            if (
                best_missing is None
                or
                len(
                    missing
                )
                <
                len(
                    best_missing
                )
            ):

                best_missing = set(
                    missing
                )

    return (
        best_missing
        or
        set()
    )


# ==================================================
# STATE UTILITIES
# ==================================================

def state_key(
    state
):

    return tuple(
        sorted(
            state
        )
    )


def deduplicate_states(states):
    """
    Deduplicate and dominance-prune artifact states.

    The current dependency model has positive requirements only and tools
    only add artifacts. If state A is a subset of state B, B can satisfy
    every downstream route that A can satisfy, so A is redundant.
    """
    unique = {}
    for state in states:
        normalized = set(state)
        unique[state_key(normalized)] = normalized

    ordered = sorted(
        unique.values(),
        key=len,
        reverse=True
    )

    maximal = []
    for state in ordered:
        if any(state.issubset(kept) for kept in maximal):
            continue
        maximal.append(state)

    return maximal


# ==================================================
# WORKFLOW UTILITIES
# ==================================================

def get_workflow(
    workflow_id
):

    workflows = (
        load_workflows()
    )

    return workflows.get(
        workflow_id
    )


def get_step_candidates(
    step
):
    """
    Support both the current candidates format and
    legacy preferred/alternatives workflow entries.
    """

    candidates = (
        step.get(
            "candidates"
        )
    )

    if candidates:

        return unique_preserve_order(
            candidates
        )

    legacy = []

    preferred = (
        step.get(
            "preferred"
        )
    )

    if preferred:

        legacy.append(
            preferred
        )

    legacy.extend(
        step.get(
            "alternatives",
            []
        )
    )

    return unique_preserve_order(
        legacy
    )


# ==================================================
# SEQUENTIAL STEP
# ==================================================

def evaluate_sequential_step(
    states,
    candidates
):
    """
    Standard BioFlow step.

    Candidate tools are alternatives.

    If FastQC and fastp are candidates, either route
    can keep the workflow executable.
    """

    runnable_tools = []

    blocked_tools = []

    unknown_tools = []

    next_states = []

    for tool_id in candidates:

        routes = (
            get_tool_routes(
                tool_id
            )
        )

        if routes is None:

            unknown_tools.append(
                tool_id
            )

            continue

        tool_runnable = False

        for state in states:

            runnable_routes = (
                get_runnable_routes(
                    tool_id,
                    state
                )
            )

            for route in runnable_routes:

                tool_runnable = True

                new_state = set(
                    state
                )

                new_state.update(
                    route.get(
                        "produces",
                        []
                    )
                )

                next_states.append(
                    new_state
                )

        if tool_runnable:

            runnable_tools.append(
                tool_id
            )

        else:

            missing = (
                get_best_missing_inputs(
                    tool_id,
                    states
                )
            )

            blocked_tools.append(
                {
                    "tool": tool_id,
                    "missing": sorted(
                        missing
                    )
                }
            )

    return {
        "success": bool(
            next_states
        ),

        "next_states": (
            deduplicate_states(
                next_states
            )
        ),

        "runnable_tools": (
            runnable_tools
        ),

        "blocked_tools": (
            blocked_tools
        ),

        "unknown_tools": (
            unknown_tools
        ),

        "successful_candidate_count": (
            len(
                runnable_tools
            )
        ),

        "required_candidate_count": 1,

        "aggregate_produces": []
    }


# ==================================================
# PARALLEL STEP
# ==================================================

def evaluate_parallel_step(
    states,
    candidates,
    min_successful_candidates=1,
    aggregate_produces=None
):
    """
    Parallel BioFlow step.

    Unlike sequential candidate selection, multiple
    candidate tools are intentionally executed.

    Example:

        SemiBin2
        MetaBAT2
        MaxBin2
        CONCOCT

    At least N tools may be required.

    Once the minimum requirement is satisfied,
    aggregate_produces can create an artifact such as:

        multiple_mag_bin_sets
    """

    if aggregate_produces is None:

        aggregate_produces = []

    runnable_tools_global = set()

    blocked_tools_map = {}

    unknown_tools = []

    next_states = []

    # --------------------------------------------------
    # Evaluate each possible incoming pipeline state.
    # --------------------------------------------------

    for state in states:

        successful_tools = []

        produced_by_parallel_step = set()

        for tool_id in candidates:

            routes = (
                get_tool_routes(
                    tool_id
                )
            )

            if routes is None:

                if tool_id not in unknown_tools:

                    unknown_tools.append(
                        tool_id
                    )

                continue

            runnable_routes = (
                get_runnable_routes(
                    tool_id,
                    state
                )
            )

            if runnable_routes:

                successful_tools.append(
                    tool_id
                )

                runnable_tools_global.add(
                    tool_id
                )

                # A candidate may technically have
                # multiple executable routes.
                # For a parallel aggregation step,
                # union all outputs that can be produced.
                for route in runnable_routes:

                    produced_by_parallel_step.update(
                        route.get(
                            "produces",
                            []
                        )
                    )

            else:

                missing = (
                    get_best_missing_inputs(
                        tool_id,
                        [
                            state
                        ]
                    )
                )

                existing = (
                    blocked_tools_map.get(
                        tool_id
                    )
                )

                if (
                    existing is None
                    or
                    len(
                        missing
                    )
                    <
                    len(
                        existing
                    )
                ):

                    blocked_tools_map[
                        tool_id
                    ] = set(
                        missing
                    )

        # --------------------------------------------------
        # Minimum number of successful parallel branches.
        # --------------------------------------------------

        if (
            len(
                successful_tools
            )
            >=
            min_successful_candidates
        ):

            new_state = set(
                state
            )

            new_state.update(
                produced_by_parallel_step
            )

            # Only create aggregate artifacts when the
            # declared minimum branch requirement succeeds.
            new_state.update(
                aggregate_produces
            )

            next_states.append(
                new_state
            )

    # --------------------------------------------------
    # Build readable blocked-tool report.
    # --------------------------------------------------

    blocked_tools = []

    for tool_id in candidates:

        if (
            tool_id
            not in
            runnable_tools_global
            and
            tool_id
            not in
            unknown_tools
        ):

            missing = (
                blocked_tools_map.get(
                    tool_id,
                    set()
                )
            )

            blocked_tools.append(
                {
                    "tool": (
                        tool_id
                    ),

                    "missing": (
                        sorted(
                            missing
                        )
                    )
                }
            )

    return {
        "success": bool(
            next_states
        ),

        "next_states": (
            deduplicate_states(
                next_states
            )
        ),

        "runnable_tools": (
            [
                tool_id
                for tool_id in candidates
                if tool_id in runnable_tools_global
            ]
        ),

        "blocked_tools": (
            blocked_tools
        ),

        "unknown_tools": (
            unknown_tools
        ),

        "successful_candidate_count": (
            len(
                runnable_tools_global
            )
        ),

        "required_candidate_count": (
            min_successful_candidates
        ),

        "aggregate_produces": (
            list(
                aggregate_produces
            )
        )
    }


# ==================================================
# WORKFLOW VALIDATION
# ==================================================

def validate_workflow(
    workflow_id,
    workflow_override=None
):
    """
    Validate whether an end-to-end executable artifact
    path exists through a BioFlow workflow.

    Supported modes:

    Standard step:
        candidates are alternatives.

    Parallel step:
        multiple candidate tools are executed and a
        minimum number of successful branches can be
        required.
    """

    workflow = (
        workflow_override
        if isinstance(
            workflow_override,
            dict
        )
        else
        get_workflow(
            workflow_id
        )
    )

    if workflow is None:

        return {
            "workflow_id": workflow_id,
            "valid": False,
            "error": "Workflow not found.",
            "steps": []
        }

    initial = (
        infer_initial_artifacts(
            workflow
        )
    )

    states = [
        set(
            initial
        )
    ]

    step_reports = []

    pipeline_blocked = False

    for step_number, step in enumerate(
        workflow.get(
            "steps",
            []
        ),
        start=1
    ):

        operation = (
            step.get(
                "operation"
            )
        )

        step_name = (
            step.get(
                "name",
                operation
                or
                "Unnamed step"
            )
        )

        candidates = (
            get_step_candidates(
                step
            )
        )

        mode = (
            str(
                step.get(
                    "mode",
                    "sequential"
                )
            )
            .strip()
            .lower()
        )

        # --------------------------------------------------
        # PARALLEL
        # --------------------------------------------------

        if mode == "parallel":

            minimum = (
                step.get(
                    "min_successful_candidates",
                    1
                )
            )

            try:

                minimum = int(
                    minimum
                )

            except (
                TypeError,
                ValueError
            ):

                minimum = 1

            minimum = max(
                minimum,
                1
            )

            aggregate_produces = (
                step.get(
                    "aggregate_produces",
                    []
                )
            )

            evaluation = (
                evaluate_parallel_step(
                    states=states,
                    candidates=candidates,
                    min_successful_candidates=minimum,
                    aggregate_produces=aggregate_produces
                )
            )

        # --------------------------------------------------
        # STANDARD / SEQUENTIAL
        # --------------------------------------------------

        else:

            evaluation = (
                evaluate_sequential_step(
                    states=states,
                    candidates=candidates
                )
            )

        # --------------------------------------------------
        # SUCCESS
        # --------------------------------------------------

        if evaluation[
            "success"
        ]:

            status = "ok"

            states = (
                evaluation[
                    "next_states"
                ]
            )

        # --------------------------------------------------
        # UNKNOWN I/O
        # --------------------------------------------------

        elif evaluation[
            "unknown_tools"
        ]:

            status = "unknown"

            pipeline_blocked = True

        # --------------------------------------------------
        # BLOCKED
        # --------------------------------------------------

        else:

            status = "blocked"

            pipeline_blocked = True

        step_report = {
            "step_number": (
                step_number
            ),

            "name": (
                step_name
            ),

            "operation": (
                operation
            ),

            "mode": (
                mode
            ),

            "status": (
                status
            ),

            "runnable_tools": (
                evaluation[
                    "runnable_tools"
                ]
            ),

            "blocked_tools": (
                evaluation[
                    "blocked_tools"
                ]
            ),

            "unknown_tools": (
                evaluation[
                    "unknown_tools"
                ]
            ),

            "successful_candidate_count": (
                evaluation[
                    "successful_candidate_count"
                ]
            ),

            "required_candidate_count": (
                evaluation[
                    "required_candidate_count"
                ]
            ),

            "aggregate_produces": (
                evaluation[
                    "aggregate_produces"
                ]
            )
        }

        step_reports.append(
            step_report
        )

        if pipeline_blocked:

            break

    # ==================================================
    # FINAL ARTIFACT STATE
    # ==================================================

    final_artifacts = set()

    for state in states:

        final_artifacts.update(
            state
        )

    return {
        "workflow_id": (
            workflow_id
        ),

        "workflow_name": (
            workflow.get(
                "name",
                workflow_id
            )
        ),

        "valid": (
            not pipeline_blocked
        ),

        "initial_artifacts": (
            sorted(
                initial
            )
        ),

        "final_artifacts": (
            sorted(
                final_artifacts
            )
        ),

        "steps": (
            step_reports
        ),

        "error": None
    }


# ==================================================
# TERMINAL REPORT
# ==================================================

def print_validation_report(
    report
):

    if report.get(
        "error"
    ):

        print(
            "ERROR:",
            report[
                "error"
            ]
        )

        return

    print()

    print(
        "=" * 70
    )

    print(
        report.get(
            "workflow_name",
            report.get(
                "workflow_id"
            )
        )
    )

    print(
        "=" * 70
    )

    print()

    print(
        "Initial artifacts:"
    )

    for artifact_id in report.get(
        "initial_artifacts",
        []
    ):

        print(
            "  -",
            get_artifact_label(
                artifact_id
            )
        )

    print()

    for step in report.get(
        "steps",
        []
    ):

        status = (
            step[
                "status"
            ]
        )

        mode = (
            step.get(
                "mode",
                "sequential"
            )
        )

        if status == "ok":

            symbol = "[OK]"

        elif status == "unknown":

            symbol = "[UNKNOWN]"

        else:

            symbol = "[BLOCKED]"

        print(
            f"{symbol} "
            f"{step['step_number']}. "
            f"{step['name']}"
        )

        # --------------------------------------------------
        # Parallel information
        # --------------------------------------------------

        if mode == "parallel":

            successful = (
                step.get(
                    "successful_candidate_count",
                    0
                )
            )

            required = (
                step.get(
                    "required_candidate_count",
                    1
                )
            )

            print(
                "    Mode: parallel"
            )

            print(
                f"    Successful branches: "
                f"{successful}/{required} required"
            )

        # --------------------------------------------------
        # Runnable tools
        # --------------------------------------------------

        if step.get(
            "runnable_tools"
        ):

            if mode == "parallel":

                print(
                    "    Runnable parallel tools:"
                )

            else:

                print(
                    "    Runnable:"
                )

            for tool in step[
                "runnable_tools"
            ]:

                print(
                    f"      - {tool}"
                )

        # --------------------------------------------------
        # Blocked tools
        # --------------------------------------------------

        if step.get(
            "blocked_tools"
        ):

            print(
                "    Blocked:"
            )

            for item in step[
                "blocked_tools"
            ]:

                print(
                    f"      - {item['tool']}"
                )

                for artifact_id in (
                    item[
                        "missing"
                    ]
                ):

                    print(
                        "          missing:",
                        get_artifact_label(
                            artifact_id
                        )
                    )

        # --------------------------------------------------
        # Unknown I/O
        # --------------------------------------------------

        if step.get(
            "unknown_tools"
        ):

            print(
                "    I/O not yet defined:"
            )

            for tool in step[
                "unknown_tools"
            ]:

                print(
                    f"      - {tool}"
                )

        # --------------------------------------------------
        # Aggregate outputs
        # --------------------------------------------------

        if (
            status == "ok"
            and
            mode == "parallel"
            and
            step.get(
                "aggregate_produces"
            )
        ):

            print(
                "    Aggregate output:"
            )

            for artifact_id in step[
                "aggregate_produces"
            ]:

                print(
                    "      -",
                    get_artifact_label(
                        artifact_id
                    )
                )

        print()

    if report[
        "valid"
    ]:

        print(
            "RESULT: EXECUTABLE PATH FOUND"
        )

    else:

        print(
            "RESULT: WORKFLOW IS NOT "
            "END-TO-END EXECUTABLE"
        )

    print()