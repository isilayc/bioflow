from pathlib import Path
import os
import platform

import streamlit as st

from engine.recommender import (
    build_workflow,
    get_sample_types,
    get_sequencing_options,
    get_read_type_options,
    get_goal_options,
    get_workflow_strategies
)

from engine.exporter import (
    workflow_to_json,
    workflow_to_markdown,
    export_filename
)

from engine.evidence import (
    classify_papers,
    rank_evidence,
    score_literature_evidence,
    evidence_rank_signal
)

from engine.scoring import (
    scientific_fit_priority,
    operational_hard_gate_priority,
    constraint_hard_gate_priority,
    constraint_soft_priority
)

from engine.research import (
    run_systematic_discovery
)

from engine.catalog import (
    get_global_coverage
)

from engine.dependencies import (
    validate_workflow,
    get_artifact_label,
    load_workflows
)

from engine.constraints import (
    get_tool_constraint_definition,
    get_profile_field_definitions,
    get_workflow_constraint_definition,
    get_workflow_profile_field_definitions,
    evaluate_tool_constraints,
    evaluate_workflow_constraints
)

from engine.fallbacks import (
    resolve_step_recovery
)

from engine.feasibility import (
    evaluate_operational_feasibility,
    operational_status_priority
)

from engine.references import (
    get_scope_options,
    get_default_scope,
    get_scope_label,
    get_reference_guidance
)

from services.biotools import (
    get_biotools_info
)

from services.literature import (
    search_tool_evidence
)



# ==================================================
# MARKER-SPECIFIC REFERENCE GUIDANCE
# ==================================================

def show_reference_guidance(
    goal,
    workflow_id,
    scope_id
):
    """
    Display marker- and route-specific reference/database guidance.

    Database choice is deliberately separated from tool identity:
    the same analysis ecosystem can require different references
    for 18S versus ITS, and for different biological scopes.
    """

    guidance = get_reference_guidance(
        goal,
        workflow_id,
        scope_id
    )

    if not guidance:
        return

    status = guidance.get(
        "status",
        "supported"
    )

    status_labels = {
        "preferred": "âœ… Preferred fit",
        "supported": "âœ“ Supported",
        "conditional": "âš ï¸ Conditional"
    }

    with st.expander(
        "ğŸ§¬ Reference / database guidance",
        expanded=True
    ):

        st.write(
            "**Taxonomic scope:**",
            guidance.get(
                "scope_label",
                scope_id
            )
        )

        st.write(
            "**Route status for this scope:**",
            status_labels.get(
                status,
                status
            )
        )

        preferred = guidance.get(
            "preferred_database"
        )

        if preferred:

            st.write(
                "**Preferred reference:**",
                preferred
            )

        route_recommendation = guidance.get(
            "route_recommendation"
        )

        if route_recommendation:

            st.write(
                "**For this route:**",
                route_recommendation
            )

        alternatives = (
            guidance.get(
                "alternatives",
                []
            )
            or
            []
        )

        if alternatives:

            st.write(
                "**Alternatives:**"
            )

            for item in alternatives:

                st.write(
                    f"- {item}"
                )

        important = (
            guidance.get(
                "important",
                []
            )
            or
            []
        )

        if important:

            st.write(
                "**Important:**"
            )

            for item in important:

                st.write(
                    f"- {item}"
                )

        avoid = (
            guidance.get(
                "avoid",
                []
            )
            or
            []
        )

        if avoid:

            st.write(
                "**Avoid:**"
            )

            for item in avoid:

                st.write(
                    f"- {item}"
                )


def show_step_recovery_guidance(
    workflow,
    step,
    tools,
    step_dependency_report,
    constraint_lookup,
    operational_lookup,
    compute_profile
):
    """Show one compact, actionable recovery path after a tool is blocked."""

    if step.get("mode", "sequential") == "parallel":
        return

    ready_tools = []
    blocked_tools = []
    constraint_blocked_ids = []
    technical_blocked = False
    operational_blocked = False

    for tool in tools:
        tool_id = tool.get("id")
        if not tool_id:
            continue

        technical_status = get_tool_dependency_status(
            step_dependency_report,
            tool_id
        ).get("status")

        constraint_status = constraint_lookup.get(
            tool_id,
            {}
        ).get("status", "not_defined")

        operational_status = operational_lookup.get(
            tool_id,
            {}
        ).get("status", "not_evaluated")

        is_technical_block = technical_status == "blocked"
        is_constraint_block = constraint_status == "block"
        is_operational_block = (
            compute_profile.get("enabled", False)
            and operational_status == "blocked"
        )

        if is_technical_block or is_constraint_block or is_operational_block:
            blocked_tools.append(tool)
            technical_blocked = technical_blocked or is_technical_block
            operational_blocked = operational_blocked or is_operational_block
            if is_constraint_block:
                constraint_blocked_ids.append(tool_id)
        elif technical_status == "runnable":
            ready_tools.append(tool)

    if not blocked_tools:
        return

    if ready_tools:
        names = ", ".join(
            tool.get("name", tool.get("id", "tool"))
            for tool in ready_tools
        )
        st.success(
            f"âœ… **Recommended next action:** continue with **{names}**. "
            "The blocked candidate remains visible for transparency but is not "
            "treated as runnable."
        )
        return

    st.error(
        "â›” **No ready candidate remains for this step.** "
        "OmicsRoute will not substitute an unrelated method."
    )

    recovery = (
        resolve_step_recovery(
            workflow,
            step,
            constraint_blocked_ids
        )
        if constraint_blocked_ids
        else {"strategies": [], "remediations": []}
    )

    strategies = recovery.get("strategies", [])
    remediations = recovery.get("remediations", [])

    if strategies:
        st.warning(
            "â¡ï¸ **Recommended next action:** switch to another validated workflow "
            "strategy for the same analysis goal."
        )

        for strategy in strategies:
            label = strategy.get("name") or "Alternative workflow strategy"
            st.write(f"- **{label}**")
            if strategy.get("description"):
                st.caption(strategy.get("description"))

        st.caption(
            "Select the alternative from the Workflow strategy control above and "
            "click Build workflow again. OmicsRoute does not change scientific methods silently."
        )

    if remediations or technical_blocked or operational_blocked:
        with st.expander("Keep the current strategy: fix its requirements"):
            seen_messages = set()

            for item in remediations:
                message = item.get("message", "")
                if not message or message in seen_messages:
                    continue
                seen_messages.add(message)
                st.write(f"- {message}")
                if item.get("fallback_note"):
                    st.caption(item.get("fallback_note"))

            if technical_blocked:
                st.write(
                    "- Restore the missing upstream artifact required by this step."
                )

            if operational_blocked:
                st.write(
                    "- Use a compute environment that satisfies the declared resource "
                    "requirements, or choose a compatible route."
                )

    if not strategies and not remediations and not technical_blocked and not operational_blocked:
        st.info(
            "**Recommended next action:** no equivalent curated fallback is represented "
            "in the current OmicsRoute catalog. Resolve the blocked requirement before continuing."
        )


def get_workflow_required_inputs(
    workflow,
    dependency_validation=None
):
    """Return explicit inputs, or infer them from the validated artifact path."""

    explicit_inputs = (
        workflow.get(
            "external_inputs",
            []
        )
        or
        []
    )

    if explicit_inputs:
        source = explicit_inputs
    else:
        source = (
            (dependency_validation or {}).get(
                "initial_artifacts",
                []
            )
            or
            []
        )

    required_inputs = []
    seen = set()

    for artifact_id in source:
        if not artifact_id:
            continue

        artifact_id = str(
            artifact_id
        )

        if artifact_id in seen:
            continue

        seen.add(
            artifact_id
        )
        required_inputs.append(
            artifact_id
        )

    return required_inputs


def show_workflow_overview_and_export(
    workflow,
    dependency_validation=None
):
    """Show the workflow overview while preserving the legacy validator marker."""

    steps = [
        step
        for step in (workflow.get("steps", []) or [])
        if isinstance(step, dict)
    ]

    tool_ids = set()
    for step in steps:
        tools = step.get("tools") or []
        if isinstance(tools, list) and tools:
            for tool in tools:
                if isinstance(tool, dict) and tool.get("id"):
                    tool_ids.add(str(tool.get("id")))
        else:
            candidates = step.get("candidates") or []
            if not isinstance(candidates, list):
                candidates = [candidates]
            tool_ids.update(str(item) for item in candidates if item)

    required_inputs = get_workflow_required_inputs(
        workflow,
        dependency_validation
    )

    st.markdown("### Workflow overview")
    col_steps, col_tools, col_inputs = st.columns(3)

    with col_steps:
        st.metric("Steps", len(steps))

    with col_tools:
        st.metric("Tool options", len(tool_ids))

    with col_inputs:
        st.metric("Required inputs", len(required_inputs))

    context = workflow.get("context", {}) or {}
    context_parts = []

    for key in ("sample_type", "sequencing", "read_type", "goal"):
        value = context.get(key)
        if value:
            context_parts.append(str(value))

    if context_parts:
        st.caption(" â†’ ".join(context_parts))


def show_workflow_export(
    workflow,
    dependency_validation=None
):
    """Render the final review and export action."""

    st.markdown("## Review & export")
    st.caption(
        "You have reached the end of the recommended workflow. "
        "Review the route above, then export the current OmicsRoute recommendation "
        "for methods notes, sharing, or later reuse."
    )

    context = workflow.get("context", {}) or {}
    context_parts = []

    for key in ("sample_type", "sequencing", "read_type", "goal"):
        value = context.get(key)
        if value:
            context_parts.append(str(value))

    if context_parts:
        st.info("Selected route: " + " â†’ ".join(context_parts))

    markdown_data = workflow_to_markdown(workflow)
    json_data = workflow_to_json(workflow)

    export_col_md, export_col_json = st.columns(2)

    with export_col_md:
        st.download_button(
            "Download workflow as Markdown",
            data=markdown_data,
            file_name=export_filename(workflow, "md"),
            mime="text/markdown",
            use_container_width=True,
        )

    with export_col_json:
        st.download_button(
            "Download workflow as JSON",
            data=json_data,
            file_name=export_filename(workflow, "json"),
            mime="application/json",
            use_container_width=True,
        )

    st.caption(
        "Dataset-specific suitability decisions should be interpreted together "
        "with the checks and tool documentation shown above."
    )




# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="OmicsRoute | Workflow Builder",
    page_icon="ğŸ§¬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>
    .stMainBlockContainer {
        padding-top: 2.1rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    .omicsroute-hero {
        border: 1px solid rgba(128, 128, 128, 0.24);
        border-radius: 18px;
        padding: 1.25rem 1.5rem 1.15rem 1.5rem;
        margin: 0.25rem 0 1rem 0;
        background:
            linear-gradient(
                135deg,
                rgba(90, 120, 255, 0.09),
                rgba(120, 220, 190, 0.07)
            );
    }

    .omicsroute-eyebrow {
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        opacity: 0.68;
        margin-bottom: 0.45rem;
    }

    .omicsroute-hero h1 {
        font-size: clamp(1.75rem, 3.2vw, 2.65rem);
        line-height: 1.04;
        margin: 0 0 0.7rem 0;
        padding: 0;
    }

    .omicsroute-hero p {
        font-size: 1.04rem;
        line-height: 1.58;
        max-width: 900px;
        opacity: 0.82;
        margin: 0;
    }

    .omicsroute-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.48rem;
        margin-top: 1rem;
    }

    .omicsroute-chip {
        border: 1px solid rgba(128, 128, 128, 0.28);
        border-radius: 999px;
        padding: 0.28rem 0.68rem;
        font-size: 0.78rem;
        font-weight: 600;
        background: rgba(255, 255, 255, 0.04);
    }

    .omicsroute-step {
        border: 1px solid rgba(128, 128, 128, 0.20);
        border-radius: 13px;
        padding: 0.8rem 0.9rem;
        min-height: 92px;
    }

    .omicsroute-step-number {
        font-size: 0.72rem;
        font-weight: 700;
        opacity: 0.60;
        margin-bottom: 0.18rem;
    }

    .omicsroute-step-title {
        font-size: 0.92rem;
        font-weight: 700;
        margin-bottom: 0.12rem;
    }

    .omicsroute-step-text {
        font-size: 0.79rem;
        line-height: 1.35;
        opacity: 0.70;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================
# SESSION STATE
# ==================================================

if "workflow" not in st.session_state:

    st.session_state.workflow = None


if "coverage_audit_loaded" not in st.session_state:

    st.session_state.coverage_audit_loaded = False


# ==================================================
# CACHE / PERFORMANCE
# ==================================================

APP_DIR = (
    Path(__file__)
    .resolve()
    .parent
)

DATA_DIR = (
    APP_DIR
    / "data"
)


def get_file_signature(filenames):
    """
    Return a stable signature for a group of OmicsRoute YAML files.

    Cached calculations automatically refresh when any relevant YAML
    file is edited, while ordinary Streamlit reruns reuse prior results.
    """

    signature = []

    for filename in filenames:

        filepath = (
            DATA_DIR
            / filename
        )

        if filepath.exists():

            stat = filepath.stat()

            signature.append(
                (
                    filename,
                    stat.st_mtime_ns,
                    stat.st_size
                )
            )

        else:

            signature.append(
                (
                    filename,
                    None,
                    None
                )
            )

    return tuple(
        signature
    )


def get_dependency_signature():

    return get_file_signature(
        (
            "workflows.yaml",
            "tool_io.yaml",
            "artifacts.yaml",
            "tools.yaml"
        )
    )


def get_catalog_signature():

    return get_file_signature(
        (
            "analysis_goals.yaml",
            "workflows.yaml"
        )
    )


@st.cache_data(
    show_spinner=False
)
def cached_validate_workflow(
    workflow_id,
    dependency_signature
):
    """Cache dependency validation until dependency YAML changes."""

    return validate_workflow(
        workflow_id
    )


@st.cache_data(
    show_spinner=False
)
def cached_global_coverage(
    catalog_signature
):
    """Cache catalogue parsing until catalogue YAML changes."""

    return get_global_coverage()


# ==================================================
# EXTERNAL SERVICE CACHE
# ==================================================

@st.cache_data(
    ttl=86400,
    show_spinner=False
)
def cached_biotools_info(
    tool_name
):

    return get_biotools_info(
        tool_name
    )


@st.cache_data(
    ttl=86400,
    show_spinner=False
)
def cached_literature_search(
    tool_name,
    operation
):
    """
    Multi-source tool evidence:
    OpenAlex + Europe PMC + PubMed, with both
    recent and foundational literature lanes.
    """

    return search_tool_evidence(
        tool_name=tool_name,
        operation=operation,
        recent_years=5,
        limit=15
    )


@st.cache_data(
    ttl=86400,
    show_spinner=False
)
def cached_systematic_discovery(
    operation,
    sample_type,
    sequencing,
    read_type,
    goal,
    feature_strategy,
    marker,
    curated_tool_names,
    search_depth
):
    """
    Capability-aware Research Engine v3.

    Candidate generation uses the curated capability catalogue plus
    structured bio.tools searches. Literature is used separately for
    evidence verification after a named resource is identified.
    """

    context = {
        "sample_type": sample_type,
        "sequencing": sequencing,
        "read_type": read_type,
        "goal": goal,
        "feature_strategy": feature_strategy,
        "marker": marker
    }

    curated_tools = [
        {
            "name": name
        }
        for name
        in curated_tool_names
    ]

    if search_depth == "Deep":

        registry_per_query = 35
        registry_max_total = 200

    else:

        registry_per_query = 15
        registry_max_total = 100

    return run_systematic_discovery(
        operation=operation,
        context=context,
        curated_tools=curated_tools,
        registry_per_query=registry_per_query,
        registry_max_total=registry_max_total
    )


# ==================================================
# DEPENDENCY / COVERAGE UTILITIES
# ==================================================

def format_dependency_context_value(
    value
):
    """
    Convert workflow context values into the same
    human-readable form used by the OmicsRoute UI.
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


def get_family_sample_type(
    family
):
    """
    Resolve a catalogue family's sample type.

    catalog.py may expose it directly on the family
    or inside goal context records. This helper keeps
    the UI tolerant of either representation.
    """

    direct = (
        family.get(
            "sample_type"
        )
    )

    if direct:

        return (
            format_dependency_context_value(
                direct
            )
        )

    family_context = (
        family.get(
            "context",
            {}
        )
    )

    if family_context.get(
        "sample_type"
    ):

        return (
            format_dependency_context_value(
                family_context.get(
                    "sample_type"
                )
            )
        )

    for goal in family.get(
        "goals",
        []
    ):

        for context in goal.get(
            "contexts",
            []
        ):

            sample_type = (
                context.get(
                    "sample_type"
                )
            )

            if sample_type:

                return (
                    format_dependency_context_value(
                        sample_type
                    )
                )

    return ""


def context_matches_catalog_context(
    workflow_context,
    catalog_context
):
    """
    Compare the context fields that are present in a
    catalogue context record.

    Missing catalogue fields are treated as wildcards.
    """

    for field_name in (
        "sample_type",
        "sequencing",
        "read_type",
        "goal"
    ):

        expected = (
            catalog_context.get(
                field_name
            )
        )

        if expected in (
            None,
            ""
        ):

            continue

        actual = (
            workflow_context.get(
                field_name
            )
        )

        if (
            format_dependency_context_value(
                actual
            )
            !=
            format_dependency_context_value(
                expected
            )
        ):

            return False

    return True


def find_goal_workflows(
    family,
    goal,
    workflows
):
    """
    Find workflows that implement one catalogue goal.

    Matching is primarily based on sample type + goal.
    Existing catalogue contexts are used as an
    additional constraint when available.
    """

    if not goal.get(
        "supported",
        False
    ):

        return []

    goal_label = (
        goal.get(
            "label",
            ""
        )
    )

    family_sample_type = (
        get_family_sample_type(
            family
        )
    )

    catalog_contexts = (
        goal.get(
            "contexts",
            []
        )
    )

    # If catalog.py already exposes workflow IDs,
    # use them directly.
    direct_ids = []

    for context in catalog_contexts:

        workflow_id = (
            context.get(
                "workflow_id"
            )
            or
            context.get(
                "id"
            )
        )

        if (
            workflow_id
            and
            workflow_id in workflows
        ):

            direct_ids.append(
                workflow_id
            )

    if direct_ids:

        return list(
            dict.fromkeys(
                direct_ids
            )
        )

    matches = []

    for (
        workflow_id,
        workflow
    ) in workflows.items():

        workflow_context = (
            workflow.get(
                "context",
                {}
            )
        )

        if (
            format_dependency_context_value(
                workflow_context.get(
                    "goal"
                )
            )
            !=
            goal_label
        ):

            continue

        if family_sample_type:

            workflow_sample_type = (
                format_dependency_context_value(
                    workflow_context.get(
                        "sample_type"
                    )
                )
            )

            if (
                workflow_sample_type
                !=
                family_sample_type
            ):

                continue

        if catalog_contexts:

            if not any(
                context_matches_catalog_context(
                    workflow_context,
                    catalog_context
                )
                for catalog_context
                in catalog_contexts
            ):

                continue

        matches.append(
            workflow_id
        )

    return matches


def build_dependency_coverage(
    coverage
):
    """
    Overlay dependency validation on the existing
    catalogue coverage.

    Goal status:
      valid   -> at least one executable workflow
      broken  -> implemented, but no executable path
      planned -> no workflow implemented yet
    """

    workflows = (
        load_workflows()
    )

    reports = {}

    # The complete audit is already cached by cached_dependency_coverage().
    # Avoid creating a separate Streamlit cache entry for every workflow.
    for workflow_id in workflows:

        reports[
            workflow_id
        ] = (
            validate_workflow(
                workflow_id
            )
        )

    family_results = []

    validated_total = 0
    broken_total = 0
    planned_total = 0

    for family in coverage.get(
        "families",
        []
    ):

        family_goals = []

        family_validated = 0
        family_broken = 0
        family_planned = 0

        for goal in family.get(
            "goals",
            []
        ):

            goal_copy = (
                goal.copy()
            )

            if not goal.get(
                "supported",
                False
            ):

                goal_copy[
                    "dependency_status"
                ] = "planned"

                goal_copy[
                    "workflow_reports"
                ] = []

                family_planned += 1
                planned_total += 1

            else:

                matching_ids = (
                    find_goal_workflows(
                        family,
                        goal,
                        workflows
                    )
                )

                matching_reports = [
                    reports[
                        workflow_id
                    ]
                    for workflow_id
                    in matching_ids
                    if workflow_id in reports
                ]

                goal_copy[
                    "workflow_reports"
                ] = (
                    matching_reports
                )

                if any(
                    report.get(
                        "valid",
                        False
                    )
                    for report
                    in matching_reports
                ):

                    goal_copy[
                        "dependency_status"
                    ] = "valid"

                    family_validated += 1
                    validated_total += 1

                else:

                    goal_copy[
                        "dependency_status"
                    ] = "broken"

                    family_broken += 1
                    broken_total += 1

            family_goals.append(
                goal_copy
            )

        family_copy = (
            family.copy()
        )

        family_copy[
            "goals"
        ] = family_goals

        family_copy[
            "validated_count"
        ] = family_validated

        family_copy[
            "broken_count"
        ] = family_broken

        family_copy[
            "planned_count"
        ] = family_planned

        family_results.append(
            family_copy
        )

    total = (
        coverage.get(
            "total",
            0
        )
    )

    percentage = (
        round(
            (
                validated_total
                /
                total
                *
                100
            ),
            1
        )
        if total
        else 0
    )

    return {
        "total": total,
        "implemented": (
            coverage.get(
                "supported",
                0
            )
        ),
        "validated": validated_total,
        "broken": broken_total,
        "planned": planned_total,
        "percentage": percentage,
        "families": family_results,
        "reports": reports
    }



@st.cache_data(
    show_spinner=False
)
def cached_dependency_coverage(
    catalog_signature,
    dependency_signature
):
    """Cache the complete dependency-aware coverage audit."""

    raw_coverage = (
        cached_global_coverage(
            catalog_signature
        )
    )

    return build_dependency_coverage(
        raw_coverage
    )

def show_analysis_coverage():

    with st.expander(
        "ğŸ—ºï¸ OmicsRoute analysis coverage"
    ):

        st.caption(
            "The full dependency audit is calculated only when requested "
            "and then cached. The first run validates the complete workflow "
            "catalogue; later loads are reused until catalogue files change."
        )

        if st.button(
            "Run / refresh dependency coverage audit",
            key="run_dependency_coverage_audit"
        ):

            st.session_state.coverage_audit_loaded = True

        if not st.session_state.coverage_audit_loaded:

            st.info(
                "Coverage validation is currently paused for performance. "
                "Click the button above whenever you want the full audit."
            )

            return

        catalog_signature = (
            get_catalog_signature()
        )

        dependency_signature = (
            get_dependency_signature()
        )

        with st.spinner(
            "Checking dependency-valid workflow coverage..."
        ):

            coverage = (
                cached_dependency_coverage(
                    catalog_signature,
                    dependency_signature
                )
            )

        st.write(
            "A goal is counted as validated only when at least one "
            "implemented workflow has an end-to-end artifact path "
            "according to tool_io.yaml."
        )

        col1, col2, col3, col4 = (
            st.columns(4)
        )

        with col1:

            st.metric(
                "Dependency-valid goals",
                coverage[
                    "validated"
                ]
            )

        with col2:

            st.metric(
                "Broken / incomplete",
                coverage[
                    "broken"
                ]
            )

        with col3:

            st.metric(
                "Planned goals",
                coverage[
                    "planned"
                ]
            )

        with col4:

            st.metric(
                "Validated coverage",
                f"{coverage['percentage']}%"
            )

        if coverage[
            "total"
        ] > 0:

            st.progress(
                coverage[
                    "validated"
                ]
                /
                coverage[
                    "total"
                ]
            )

        st.caption(
            "âœ… Dependency-valid = an executable artifact path exists. "
            "âš ï¸ Broken / incomplete = a workflow exists but required "
            "artifacts cannot be reached or I/O metadata is incomplete. "
            "â³ Planned = no workflow exists yet."
        )

        st.divider()

        for family in coverage[
            "families"
        ]:

            family_label = (
                family[
                    "label"
                ]
            )

            validated_count = (
                family.get(
                    "validated_count",
                    0
                )
            )

            broken_count = (
                family.get(
                    "broken_count",
                    0
                )
            )

            total_count = (
                family[
                    "total_count"
                ]
            )

            family_heading = (
                f"{family_label} "
                f"â€” {validated_count}/{total_count} "
                f"dependency-valid"
            )

            if broken_count:

                family_heading += (
                    f" â€¢ {broken_count} incomplete"
                )

            with st.expander(
                family_heading
            ):

                if family.get(
                    "description"
                ):

                    st.write(
                        family[
                            "description"
                        ]
                    )

                for goal in family[
                    "goals"
                ]:

                    status = (
                        goal.get(
                            "dependency_status",
                            "planned"
                        )
                    )

                    if status == "valid":

                        st.write(
                            f"âœ… **{goal['label']}**"
                        )

                    elif status == "broken":

                        st.write(
                            f"âš ï¸ **{goal['label']}**"
                        )

                    else:

                        priority = (
                            goal.get(
                                "priority",
                                "core"
                            )
                        )

                        st.write(
                            f"â³ {goal['label']} "
                            f"_{priority}_"
                        )

                        continue

                    workflow_reports = (
                        goal.get(
                            "workflow_reports",
                            []
                        )
                    )

                    if not workflow_reports:

                        st.caption(
                            "â†³ Workflow exists in the catalogue, but "
                            "dependency validation could not map it to "
                            "a workflow ID."
                        )

                        continue

                    for report in workflow_reports:

                        workflow_status = (
                            "âœ…"
                            if report.get(
                                "valid",
                                False
                            )
                            else
                            "âš ï¸"
                        )

                        st.caption(
                            f"â†³ {workflow_status} "
                            f"{report.get('workflow_name', report.get('workflow_id'))}"
                        )


# ==================================================
# WORKFLOW DEPENDENCY DISPLAY
# ==================================================

def get_step_dependency_report(
    validation_report,
    step_number
):

    if not validation_report:

        return None

    for step_report in validation_report.get(
        "steps",
        []
    ):

        if (
            step_report.get(
                "step_number"
            )
            ==
            step_number
        ):

            return step_report

    return None


def get_tool_dependency_status(
    step_report,
    tool_id
):
    """
    Return technical dependency status for one
    candidate tool at one workflow step.
    """

    if step_report is None:

        return {
            "status": "not_evaluated",
            "missing": []
        }

    if tool_id in step_report.get(
        "runnable_tools",
        []
    ):

        return {
            "status": "runnable",
            "missing": []
        }

    if tool_id in step_report.get(
        "unknown_tools",
        []
    ):

        return {
            "status": "unknown",
            "missing": []
        }

    for item in step_report.get(
        "blocked_tools",
        []
    ):

        if item.get(
            "tool"
        ) == tool_id:

            return {
                "status": "blocked",
                "missing": item.get(
                    "missing",
                    []
                )
            }

    return {
        "status": "not_evaluated",
        "missing": []
    }


def dependency_status_priority(
    status
):

    return {
        "runnable": 3,
        "unknown": 2,
        "not_evaluated": 1,
        "blocked": 0
    }.get(
        status,
        1
    )


def is_collection_artifact(
    artifact_id
):
    """
    Identify artifacts that represent multiple biological
    samples/files rather than one sample-level object.
    """

    artifact_id = str(
        artifact_id
        or
        ""
    )

    label = (
        get_artifact_label(
            artifact_id
        )
        or
        ""
    )

    return (
        artifact_id.endswith(
            "_collection"
        )
        or
        "collection"
        in label.lower()
    )


def show_workflow_input_requirements(
    workflow,
    dependency_validation=None
):
    """
    Show user-supplied prerequisites before the step-by-step workflow.

    Prefer explicit workflow external_inputs. For older workflows that do not
    declare them, use the initial artifacts resolved by dependency validation.
    """

    required_inputs = get_workflow_required_inputs(
        workflow,
        dependency_validation
    )

    if not required_inputs:
        return

    with st.expander(
        "ğŸ“¥ Required user inputs",
        expanded=False
    ):

        collection_found = False

        for artifact_id in required_inputs:

            label = (
                get_artifact_label(
                    artifact_id
                )
            )

            if is_collection_artifact(
                artifact_id
            ):

                collection_found = True

                st.write(
                    f"- ğŸ§º **{label}** â€” sample collection"
                )

            else:

                st.write(
                    f"- **{label}**"
                )

        if collection_found:

            st.info(
                "A collection input represents multiple "
                "biological/sample-level files. OmicsRoute does "
                "not treat it as one ordinary sample artifact."
            )




def show_workflow_dependency_validation(
    validation_report
):

    if validation_report is None:

        st.warning(
            "Workflow path validation could not be generated."
        )

        return

    if validation_report.get(
        "error"
    ):

        st.error(
            "Workflow path validation error: "
            f"{validation_report['error']}"
        )

        return

    if validation_report.get(
        "valid",
        False
    ):

        st.success(
            "âœ… Workflow path is technically complete."
        )

    else:

        st.error(
            "âŒ Workflow path is incomplete. One or more required artifacts "
            "cannot currently reach a downstream step."
        )

    with st.expander(
        "ğŸ”— Technical details"
    ):

        initial_artifacts = (
            validation_report.get(
                "initial_artifacts",
                []
            )
        )

        if initial_artifacts:

            st.write(
                "**Initial / user-supplied artifacts:**"
            )

            for artifact_id in initial_artifacts:

                label = (
                    get_artifact_label(
                        artifact_id
                    )
                )

                if is_collection_artifact(
                    artifact_id
                ):

                    st.write(
                        f"- ğŸ§º {label} (collection)"
                    )

                else:

                    st.write(
                        f"- {label}"
                    )

        st.divider()

        for step_report in validation_report.get(
            "steps",
            []
        ):

            status = (
                step_report.get(
                    "status"
                )
            )

            if status == "ok":

                symbol = "âœ…"

            elif status == "unknown":

                symbol = "âš ï¸"

            else:

                symbol = "âŒ"

            mode = (
                step_report.get(
                    "mode",
                    "sequential"
                )
                or
                "sequential"
            )

            st.markdown(
                f"**{symbol} "
                f"{step_report.get('step_number')}. "
                f"{step_report.get('name')}**"
            )

            runnable_tools = (
                step_report.get(
                    "runnable_tools",
                    []
                )
            )

            if mode == "parallel":

                required = (
                    step_report.get(
                        "min_successful_candidates",
                        step_report.get(
                            "required_successful_candidates",
                            1
                        )
                    )
                    or
                    1
                )

                successful = (
                    step_report.get(
                        "successful_candidate_count",
                        step_report.get(
                            "successful_tools_count",
                            len(runnable_tools)
                        )
                    )
                )

                st.write(
                    "**Execution mode:** parallel branches"
                )

                st.write(
                    f"**Successful branches:** {successful}/"
                    f"{required} required"
                )

                if runnable_tools:

                    st.write(
                        "**Runnable parallel tools:** "
                        +
                        ", ".join(
                            runnable_tools
                        )
                    )

                aggregate_outputs = (
                    step_report.get(
                        "aggregate_produces",
                        []
                    )
                    or
                    []
                )

                if aggregate_outputs:

                    st.write(
                        "**Aggregate output:**"
                    )

                    for artifact_id in aggregate_outputs:

                        st.write(
                            f"- {get_artifact_label(artifact_id)}"
                        )

            elif runnable_tools:

                st.write(
                    "**Runnable candidates:** "
                    +
                    ", ".join(
                        runnable_tools
                    )
                )

            blocked_tools = (
                step_report.get(
                    "blocked_tools",
                    []
                )
            )

            for item in blocked_tools:

                missing_labels = [
                    get_artifact_label(
                        artifact_id
                    )
                    for artifact_id
                    in item.get(
                        "missing",
                        []
                    )
                ]

                if missing_labels:

                    st.write(
                        f"**Blocked: {item.get('tool')}**"
                    )

                    for label in missing_labels:

                        st.write(
                            f"- Missing: {label}"
                        )

            unknown_tools = (
                step_report.get(
                    "unknown_tools",
                    []
                )
            )

            if unknown_tools:

                st.write(
                    "**I/O metadata not defined:** "
                    +
                    ", ".join(
                        unknown_tools
                    )
                )

            st.divider()



# ==================================================
# WORKFLOW-LEVEL DATASET PROFILE / CONSTRAINT DISPLAY
# ==================================================

def _workflow_profile_input_key(
    workflow_id,
    field_id
):
    """
    Build one stable Streamlit widget key per workflow
    dataset-profile field.

    The same field is therefore asked only once even when
    several tools in the workflow use that information.
    """

    return (
        f"dataset_profile_"
        f"{workflow_id}_"
        f"{field_id}"
    )


def _format_constraint_field_label(
    field_id,
    field_definition
):
    """
    Build a readable field label and append the unit
    when one is defined in constraints.yaml.
    """

    label = (
        field_definition.get(
            "label"
        )
        or
        field_id.replace(
            "_",
            " "
        ).title()
    )

    unit = (
        field_definition.get(
            "unit"
        )
    )

    if unit:

        label = (
            f"{label} ({unit})"
        )

    return label


def _get_constraint_step_read_type(
    workflow,
    step
):
    """
    Resolve the read type used when evaluating one tool
    inside one workflow step.
    """

    step_context = (
        step.get(
            "context",
            {}
        )
    )

    workflow_context = (
        workflow.get(
            "context",
            {}
        )
    )

    return (
        step_context.get(
            "read_type"
        )
        or
        workflow_context.get(
            "read_type"
        )
    )


def get_workflow_constraint_tools(
    workflow
):
    """
    Return every workflow tool/step combination that has
    an entry in constraints.yaml.
    """

    entries = []

    for step_number, step in enumerate(
        workflow.get(
            "steps",
            []
        ),
        start=1
    ):

        for tool in step.get(
            "tools",
            []
        ):

            tool_id = (
                tool.get(
                    "id"
                )
            )

            if not tool_id:

                continue

            definition = (
                get_tool_constraint_definition(
                    tool_id
                )
            )

            if not definition:

                continue

            entries.append(
                {
                    "tool_id": tool_id,
                    "tool_name": (
                        tool.get(
                            "name",
                            tool_id
                        )
                    ),
                    "step_number": step_number,
                    "step_name": (
                        step.get(
                            "name",
                            step.get(
                                "operation",
                                "Workflow step"
                            )
                        )
                    ),
                    "read_type": (
                        _get_constraint_step_read_type(
                            workflow,
                            step
                        )
                    )
                }
            )

    return entries


def get_workflow_constraint_fields(
    workflow
):
    """
    Merge dataset-profile fields required by the workflow
    itself and by constrained tools inside that workflow.

    Duplicate field IDs are shown once, so a shared dataset
    property is never requested repeatedly.
    """

    fields = {}
    field_sources = {}
    conflicts = []

    workflow_id = (
        workflow.get(
            "id"
        )
    )

    workflow_fields = (
        get_workflow_profile_field_definitions(
            workflow_id
        )
        if workflow_id
        else
        {}
    )

    for (
        field_id,
        field_definition
    ) in workflow_fields.items():

        if not isinstance(
            field_definition,
            dict
        ):

            continue

        fields[
            field_id
        ] = (
            field_definition.copy()
        )

        field_sources[
            field_id
        ] = [
            "Workflow strategy"
        ]

    entries = (
        get_workflow_constraint_tools(
            workflow
        )
    )

    for entry in entries:

        tool_id = (
            entry[
                "tool_id"
            ]
        )

        tool_name = (
            entry[
                "tool_name"
            ]
        )

        definitions = (
            get_profile_field_definitions(
                tool_id
            )
        )

        for (
            field_id,
            field_definition
        ) in definitions.items():

            if not isinstance(
                field_definition,
                dict
            ):

                continue

            field_sources.setdefault(
                field_id,
                []
            )

            if tool_name not in field_sources[
                field_id
            ]:

                field_sources[
                    field_id
                ].append(
                    tool_name
                )

            if field_id not in fields:

                fields[
                    field_id
                ] = (
                    field_definition.copy()
                )

                continue

            existing = (
                fields[
                    field_id
                ]
            )

            for property_name in (
                "type",
                "unit"
            ):

                existing_value = (
                    existing.get(
                        property_name
                    )
                )

                new_value = (
                    field_definition.get(
                        property_name
                    )
                )

                if (
                    existing_value
                    and
                    new_value
                    and
                    existing_value
                    !=
                    new_value
                ):

                    conflicts.append(
                        {
                            "field_id": field_id,
                            "property": property_name,
                            "first": existing_value,
                            "other": new_value,
                            "tool": tool_name
                        }
                    )

    return (
        fields,
        field_sources,
        conflicts
    )


def _render_workflow_profile_field(
    workflow_id,
    field_id,
    field_definition
):
    """
    Render one shared dataset-profile field inside the
    workflow-level form.
    """

    field_type = (
        field_definition.get(
            "type",
            "string"
        )
    )

    label = (
        _format_constraint_field_label(
            field_id,
            field_definition
        )
    )

    description = (
        field_definition.get(
            "description"
        )
    )

    key = (
        _workflow_profile_input_key(
            workflow_id,
            field_id
        )
    )

    if field_type == "boolean":

        st.selectbox(
            label,
            [
                "Not specified",
                "Yes",
                "No"
            ],
            key=key,
            help=description
        )

        return

    if field_type in (
        "choice",
        "enum"
    ):

        options = (
            field_definition.get(
                "options",
                []
            )
            or
            []
        )

        st.selectbox(
            label,
            [
                "Not specified"
            ]
            +
            list(
                options
            ),
            key=key,
            help=description
        )

        return

    if field_type == "integer":

        st.text_input(
            label,
            key=key,
            help=description,
            placeholder="Enter an integer"
        )

        return

    if field_type == "float":

        st.text_input(
            label,
            key=key,
            help=description,
            placeholder="Enter a number"
        )

        return

    st.text_input(
        label,
        key=key,
        help=description
    )


def _read_workflow_profile_field(
    workflow_id,
    field_id,
    field_definition
):
    """
    Read and normalize one submitted dataset-profile value
    from Streamlit session state.
    """

    key = (
        _workflow_profile_input_key(
            workflow_id,
            field_id
        )
    )

    raw_value = (
        st.session_state.get(
            key
        )
    )

    field_type = (
        field_definition.get(
            "type",
            "string"
        )
    )

    if field_type == "boolean":

        if raw_value == "Yes":

            return True

        if raw_value == "No":

            return False

        return None

    if field_type in (
        "choice",
        "enum"
    ):

        if raw_value in (
            None,
            "",
            "Not specified"
        ):

            return None

        return raw_value

    if field_type == "integer":

        if raw_value in (
            None,
            ""
        ):

            return None

        try:

            return int(
                raw_value
            )

        except (
            TypeError,
            ValueError
        ):

            return None

    if field_type == "float":

        if raw_value in (
            None,
            ""
        ):

            return None

        try:

            return float(
                raw_value
            )

        except (
            TypeError,
            ValueError
        ):

            return None

    if raw_value is None:

        return None

    value = str(
        raw_value
    ).strip()

    if not value:

        return None

    return value


def _get_workflow_dataset_profile(
    workflow,
    field_definitions
):
    """
    Read the currently submitted shared dataset profile.
    """

    workflow_id = (
        workflow.get(
            "id",
            "workflow"
        )
    )

    profile = {}

    for (
        field_id,
        field_definition
    ) in field_definitions.items():

        value = (
            _read_workflow_profile_field(
                workflow_id,
                field_id,
                field_definition
            )
        )

        if value is not None:

            profile[
                field_id
            ] = value

    return profile


def _constraint_status_label(
    status
):
    """
    Return a compact human-readable status label.
    """

    return {
        "pass": "âœ… PASS",
        "warning": "âš ï¸ WARNING",
        "block": "â›” BLOCK",
        "needs_input": "â„¹ï¸ MORE INPUT NEEDED",
        "not_defined": "â– NOT DEFINED"
    }.get(
        status,
        f"âš ï¸ {str(status).upper()}"
    )


def _constraint_status_message(
    status
):
    """
    Return a short explanation for one constraint result.
    """

    return {
        "pass": (
            "All configured dataset-specific checks passed."
        ),
        "warning": (
            "The tool remains usable, but OmicsRoute detected "
            "a dataset-specific warning."
        ),
        "block": (
            "OmicsRoute detected a dataset-specific condition "
            "that blocks or invalidates this configuration."
        ),
        "needs_input": (
            "More dataset information is needed before "
            "OmicsRoute can finish the suitability check."
        ),
        "not_defined": (
            "No dataset-specific constraints are defined "
            "for this tool."
        )
    }.get(
        status,
        "Constraint evaluation completed."
    )


def _show_constraint_observation(
    check
):
    """
    Show useful derived values without exposing internal
    rule-engine terminology.
    """

    rule_id = (
        check.get(
            "id",
            ""
        )
    )

    if (
        rule_id
        ==
        "paired_end_overlap_possible"
        and
        check.get(
            "observed"
        )
        is not None
    ):

        observed = (
            check.get(
                "observed"
            )
        )

        if isinstance(
            observed,
            float
        ) and observed.is_integer():

            observed = int(
                observed
            )

        st.caption(
            f"Calculated theoretical overlap: "
            f"{observed} bp"
        )


def show_workflow_dataset_profile(
    workflow
):
    """
    Render one shared dataset-profile form for the entire
    selected workflow.

    The user enters each dataset property once. All
    constrained tools reuse those values.

    The form prevents a full Streamlit rerun for every
    individual field edit; evaluation occurs when the
    user presses the submit button.
    """

    (
        field_definitions,
        field_sources,
        conflicts
    ) = (
        get_workflow_constraint_fields(
            workflow
        )
    )

    workflow_id = (
        workflow.get(
            "id"
        )
    )

    has_workflow_constraints = bool(
        get_workflow_constraint_definition(
            workflow_id
        )
        if workflow_id
        else
        None
    )

    if (
        not field_definitions
        and
        not has_workflow_constraints
    ):

        return {}

    workflow_id = (
        workflow_id
        or
        "workflow"
    )

    entries = (
        get_workflow_constraint_tools(
            workflow
        )
    )

    with st.expander(
        "ğŸ§ª Dataset profile & suitability",
        expanded=True
    ):

        st.write(
            "Enter dataset-specific information once here. "
            "OmicsRoute will reuse the same profile for every "
            "relevant tool in this workflow."
        )

        constrained_tool_names = []

        for entry in entries:

            tool_name = (
                entry[
                    "tool_name"
                ]
            )

            if tool_name not in constrained_tool_names:

                constrained_tool_names.append(
                    tool_name
                )

        if constrained_tool_names:

            st.caption(
                "Checks currently available for: "
                +
                ", ".join(
                    constrained_tool_names
                )
            )

        if conflicts:

            st.warning(
                "Some tools define the same dataset field "
                "differently. OmicsRoute is using the first "
                "definition and reporting this metadata "
                "conflict for review."
            )

        with st.form(
            key=(
                f"dataset_profile_form_"
                f"{workflow_id}"
            )
        ):

            for (
                field_id,
                field_definition
            ) in field_definitions.items():

                _render_workflow_profile_field(
                    workflow_id,
                    field_id,
                    field_definition
                )

                sources = (
                    field_sources.get(
                        field_id,
                        []
                    )
                )

                if sources:

                    st.caption(
                        "Used by: "
                        +
                        ", ".join(
                            sources
                        )
                    )

            submitted = (
                st.form_submit_button(
                    "Evaluate dataset suitability",
                    type="primary"
                )
            )

        if submitted:

            st.success(
                "Dataset profile updated."
            )

        profile = (
            _get_workflow_dataset_profile(
                workflow,
                field_definitions
            )
        )

        st.divider()

        workflow_profile = (
            profile.copy()
        )

        workflow_context = (
            workflow.get(
                "context",
                {}
            )
        )

        for context_field in (
            "sample_type",
            "sequencing",
            "read_type",
            "goal"
        ):

            if workflow_context.get(
                context_field
            ) is not None:

                workflow_profile[
                    context_field
                ] = (
                    workflow_context.get(
                        context_field
                    )
                )

        workflow_report = (
            evaluate_workflow_constraints(
                workflow_id,
                workflow_profile
            )
        )

        if workflow_report.get(
            "status"
        ) != "not_defined":

            st.write(
                "**Workflow suitability**"
            )

            workflow_status = (
                workflow_report.get(
                    "status"
                )
            )

            workflow_label = (
                _constraint_status_label(
                    workflow_status
                )
            )

            workflow_message = (
                _constraint_status_message(
                    workflow_status
                )
            )

            if workflow_status == "pass":

                st.success(
                    f"{workflow_label} â€” {workflow_message}"
                )

            elif workflow_status == "warning":

                st.warning(
                    f"{workflow_label} â€” {workflow_message}"
                )

            elif workflow_status == "block":

                st.error(
                    f"{workflow_label} â€” {workflow_message}"
                )

            elif workflow_status == "needs_input":

                st.info(
                    f"{workflow_label} â€” {workflow_message}"
                )

            else:

                st.warning(
                    f"{workflow_label} â€” {workflow_message}"
                )

            for check in workflow_report.get(
                "checks",
                []
            ):

                if check.get(
                    "status"
                ) in (
                    "warning",
                    "block",
                    "needs_input",
                    "unknown_rule"
                ):

                    check_message = (
                        check.get(
                            "message"
                        )
                    )

                    if check_message:

                        st.write(
                            f"- {check_message}"
                        )

                    missing_fields = (
                        check.get(
                            "missing_fields",
                            []
                        )
                    )

                    if missing_fields:

                        st.caption(
                            "Still needed: "
                            +
                            ", ".join(
                                field.replace(
                                    "_",
                                    " "
                                )
                                for field
                                in missing_fields
                            )
                        )

            st.divider()

        if entries:

            st.write(
                "**Tool suitability summary**"
            )

        for entry in entries:

            tool_profile = (
                profile.copy()
            )

            workflow_context = (
                workflow.get(
                    "context",
                    {}
                )
            )

            for context_field in (
                "sample_type",
                "sequencing",
                "goal"
            ):

                if workflow_context.get(
                    context_field
                ) is not None:

                    tool_profile[
                        context_field
                    ] = (
                        workflow_context.get(
                            context_field
                        )
                    )

            tool_profile[
                "read_type"
            ] = (
                entry.get(
                    "read_type"
                )
            )

            report = (
                evaluate_tool_constraints(
                    entry[
                        "tool_id"
                    ],
                    tool_profile
                )
            )

            status = (
                report.get(
                    "status"
                )
            )

            label = (
                _constraint_status_label(
                    status
                )
            )

            st.write(
                f"{label} â€” "
                f"**{entry['tool_name']}** "
                f"(step {entry['step_number']}: "
                f"{entry['step_name']})"
            )

        st.caption(
            "Constraint-aware ranking v3 is active. A dataset-specific "
            "BLOCK is a hard ranking gate. A WARNING is a soft ranking "
            "signal used only after scientific-fit tier. Missing input and "
            "tools without constraint definitions remain neutral."
        )

    return (
        _get_workflow_dataset_profile(
            workflow,
            field_definitions
        )
    )


def evaluate_step_tool_constraints(
    workflow,
    step,
    tool,
    dataset_profile
):
    """
    Evaluate one tool against the shared workflow dataset profile.

    This single helper is reused by both the ranking layer and the
    tool-detail display so OmicsRoute cannot rank with one profile while
    displaying another.
    """

    tool_id = (
        tool.get(
            "id"
        )
    )

    if not tool_id:

        return {
            "tool_id": None,
            "status": "not_defined",
            "checks": [],
            "counts": {}
        }

    if not get_tool_constraint_definition(
        tool_id
    ):

        return {
            "tool_id": tool_id,
            "status": "not_defined",
            "checks": [],
            "counts": {}
        }

    profile = dict(
        dataset_profile
        or
        {}
    )

    workflow_context = (
        workflow.get(
            "context",
            {}
        )
    )

    for context_field in (
        "sample_type",
        "sequencing",
        "goal"
    ):

        if workflow_context.get(
            context_field
        ) is not None:

            profile[
                context_field
            ] = (
                workflow_context.get(
                    context_field
                )
            )

    profile[
        "read_type"
    ] = (
        _get_constraint_step_read_type(
            workflow,
            step
        )
    )

    return (
        evaluate_tool_constraints(
            tool_id,
            profile
        )
    )


def show_dataset_constraint_checks(
    workflow,
    step,
    step_number,
    tool,
    dataset_profile
):
    """
    Show the result of dataset-specific constraint checks
    inside one tool card.

    Inputs are not requested here. They come from the
    workflow-level Dataset profile panel.
    """

    tool_id = (
        tool.get(
            "id"
        )
    )

    if not tool_id:

        return

    definition = (
        get_tool_constraint_definition(
            tool_id
        )
    )

    if not definition:

        return

    report = (
        evaluate_step_tool_constraints(
            workflow,
            step,
            tool,
            dataset_profile
        )
    )

    status = (
        report.get(
            "status"
        )
    )

    st.markdown(
        "#### ğŸ§ª Dataset suitability"
    )

    label = (
        _constraint_status_label(
            status
        )
    )

    message = (
        _constraint_status_message(
            status
        )
    )

    if status == "pass":

        st.success(
            f"{label} â€” {message}"
        )

    elif status == "warning":

        st.warning(
            f"{label} â€” {message}"
        )

    elif status == "block":

        st.error(
            f"{label} â€” {message}"
        )

    elif status == "needs_input":

        st.info(
            f"{label} â€” {message}"
        )

    else:

        st.info(
            f"{label} â€” {message}"
        )

    checks = (
        report.get(
            "checks",
            []
        )
    )

    issues = [
        check
        for check in checks
        if check.get(
            "status"
        )
        in (
            "warning",
            "block",
            "needs_input",
            "unknown_rule"
        )
    ]

    passing_observations = [
        check
        for check in checks
        if check.get(
            "status"
        )
        ==
        "pass"
    ]

    for check in issues:

        message = (
            check.get(
                "message"
            )
        )

        if message:

            st.write(
                f"- {message}"
            )

        missing_fields = (
            check.get(
                "missing_fields",
                []
            )
        )

        if missing_fields:

            st.caption(
                "Still needed: "
                +
                ", ".join(
                    field.replace(
                        "_",
                        " "
                    )
                    for field
                    in missing_fields
                )
            )

        _show_constraint_observation(
            check
        )

    for check in passing_observations:

        _show_constraint_observation(
            check
        )

    if status == "needs_input":

        st.caption(
            "Fill or update the shared "
            "'Dataset profile & suitability' panel above."
        )



# ==================================================
# STRATEGY-SPECIFIC FIT DISPLAY
# ==================================================

def _strategy_fit_badge(fit):
    """
    Convert a strategy-fit label into a concise UI badge.
    """

    normalized = (
        str(
            fit
            or
            ""
        )
        .strip()
        .lower()
    )

    return {
        "strong": "ğŸŸ¢ Strong strategy fit",
        "supported": "ğŸ”µ Supported strategy fit",
        "conditional": "ğŸŸ  Conditional strategy fit",
        "weak": "ğŸŸ¡ Weak strategy fit",
        "incompatible": "ğŸ”´ Incompatible strategy fit"
    }.get(
        normalized,
        "âšª Strategy fit not classified"
    )


def show_strategy_fit(tool):
    """
    Show curated workflow-strategy-specific suitability
    information when recommender.py attached a strategy_fit
    record to the tool.

    This explains why the same tool can rank differently
    across distinct workflow strategies without changing
    its global tools.yaml metadata.
    """

    strategy_fit = (
        tool.get(
            "strategy_fit"
        )
    )

    if not isinstance(
        strategy_fit,
        dict
    ):

        return

    fit = (
        strategy_fit.get(
            "fit"
        )
    )

    if not fit:

        return

    st.markdown(
        "#### ğŸ¯ Strategy-specific fit"
    )

    badge = (
        _strategy_fit_badge(
            fit
        )
    )

    normalized = (
        str(
            fit
        )
        .strip()
        .lower()
    )

    if normalized == "strong":

        st.success(
            badge
        )

    elif normalized == "supported":

        st.info(
            badge
        )

    elif normalized == "conditional":

        st.warning(
            badge
        )

    elif normalized == "incompatible":

        st.error(
            badge
        )

    else:

        st.warning(
            badge
        )

    rationale = (
        strategy_fit.get(
            "rationale"
        )
    )

    if rationale:

        st.write(
            rationale
        )

    database_requirement = (
        strategy_fit.get(
            "database_requirement"
        )
    )

    if database_requirement:

        st.markdown(
            "**Database / reference requirement**"
        )

        st.write(
            database_requirement
        )

    score = (
        tool.get(
            "score",
            {}
        )
    )

    if score.get(
        "strategy_adjusted"
    ):

        scientific_points = (
            score.get(
                "scientific_fit",
                0
            )
        )

        st.caption(
            "This explicit workflow-strategy classification controls "
            "the scientific-suitability component of the OmicsRoute "
            f"recommendation score ({scientific_points}/60)."
        )


# ==================================================
# BIO.TOOLS TOOL CARD
# ==================================================

def show_live_biotools_metadata(
    tool_name,
    unique_key
):

    state_key = (
        f"biotools_data_"
        f"{unique_key}"
    )

    if st.button(
        "ğŸŒ Load live bio.tools metadata",
        key=(
            f"load_biotools_"
            f"{unique_key}"
        )
    ):

        with st.spinner(
            f"Retrieving {tool_name} "
            f"from bio.tools..."
        ):

            st.session_state[
                state_key
            ] = (
                cached_biotools_info(
                    tool_name
                )
            )

    if (
        state_key
        not in
        st.session_state
    ):

        return

    live = (
        st.session_state[
            state_key
        ]
    )

    if live is None:

        st.warning(
            "No matching bio.tools "
            "record was found."
        )

        return

    st.markdown(
        "#### Live metadata from bio.tools"
    )

    if live.get(
        "biotools_id"
    ):

        st.write(
            "**bio.tools ID:**",
            live[
                "biotools_id"
            ]
        )

    if live.get(
        "description"
    ):

        st.write(
            "**Description:**",
            live[
                "description"
            ]
        )

    if live.get(
        "operations"
    ):

        st.write(
            "**Registered operations:**"
        )

        for operation in live[
            "operations"
        ]:

            st.write(
                f"- {operation}"
            )

    if live.get(
        "biotools_url"
    ):

        st.markdown(
            f"**bio.tools record:** "
            f"[Open bio.tools page]"
            f"({live['biotools_url']})"
        )


# ==================================================
# SCORE DISPLAY
# ==================================================

def show_score_details(
    tool
):
    """
    Display OmicsRoute scoring v2.

    Compatibility and operation matching are gates, not points.
    Literature evidence and operational feasibility remain separate
    layers so they cannot hide a scientific mismatch.
    """

    score = (
        tool[
            "score"
        ]
    )

    st.metric(
        "OmicsRoute recommendation score",
        f"{score['total']}/100"
    )

    st.progress(
        score[
            "total"
        ] / 100
    )

    fit_label = (
        score.get(
            "scientific_fit_display",
            "Curated fit"
        )
    )

    st.write(
        "**Scientific suitability:**",
        f"{fit_label} â€” "
        f"{score.get('scientific_fit', 0)}/"
        f"{score.get('scientific_fit_max', 60)}"
    )

    col1, col2 = (
        st.columns(2)
    )

    with col1:

        st.write(
            "**Maintenance:**",
            f"{score['maintenance']}/"
            f"{score.get('maintenance_max', 15)}"
        )

        st.write(
            "**Community support:**",
            f"{score['community']}/"
            f"{score.get('community_max', 10)}"
        )

    with col2:

        st.write(
            "**Reproducibility / deployment:**",
            f"{score['reproducibility']}/"
            f"{score.get('reproducibility_max', 15)}"
        )

    gate_col1, gate_col2 = (
        st.columns(2)
    )

    with gate_col1:

        if score.get(
            "compatibility_gate",
            False
        ):

            st.success(
                "âœ“ Dataset compatibility gate"
            )

        else:

            st.error(
                "âœ— Dataset compatibility gate"
            )

    with gate_col2:

        if score.get(
            "operation_gate",
            False
        ):

            st.success(
                "âœ“ Operation-support gate"
            )

        else:

            st.error(
                "âœ— Operation-support gate"
            )

    st.caption(
        "Scoring v2: scientific suitability 60%, maintenance 15%, "
        "reproducibility/deployment 15%, community support 10%. "
        "Dataset compatibility and operation matching are eligibility "
        "gates rather than automatic points. Literature evidence and "
        "compute feasibility are displayed separately."
    )


# ==================================================
# INDIVIDUAL LITERATURE
# ==================================================

def show_recent_literature(
    tool_name,
    operation,
    unique_key
):
    """
    Show multi-source scientific evidence for one tool.

    Despite the historical function name, Research Engine v2
    now searches both recent literature and older foundational
    papers.
    """

    state_key = (
        f"literature_data_"
        f"{unique_key}"
    )

    search_operation = (
        operation
        .replace(
            "_",
            " "
        )
        .strip()
    )

    if st.button(
        "ğŸ“š Search literature evidence",
        key=(
            f"literature_button_"
            f"{unique_key}"
        )
    ):

        with st.spinner(
            f"Searching OpenAlex, Europe PMC and "
            f"PubMed for {tool_name}..."
        ):

            result = (
                cached_literature_search(
                    tool_name,
                    search_operation
                )
            )

            if not result.get(
                "error"
            ):

                papers = (
                    classify_papers(
                        result.get(
                            "results",
                            []
                        ),
                        tool_name,
                        operation=operation
                    )
                )

                papers = (
                    rank_evidence(
                        papers
                    )
                )

                result[
                    "results"
                ] = papers

            st.session_state[
                state_key
            ] = result

    if (
        state_key
        not in
        st.session_state
    ):

        return

    literature = (
        st.session_state[
            state_key
        ]
    )

    if literature.get(
        "error"
    ):

        st.error(
            literature[
                "error"
            ]
        )

        return

    results = (
        literature.get(
            "results",
            []
        )
        or
        []
    )

    st.markdown(
        "#### ğŸ“š Scientific evidence"
    )

    providers = (
        literature.get(
            "providers_searched",
            []
        )
        or
        []
    )

    if providers:

        st.caption(
            "Sources searched: "
            +
            " â€¢ ".join(
                providers
            )
            +
            ". Recent and foundational searches are combined."
        )

    partial_errors = (
        literature.get(
            "partial_errors",
            []
        )
        or
        []
    )

    if partial_errors:

        with st.expander(
            "âš ï¸ Partial literature-source warnings"
        ):

            for error in partial_errors:

                st.write(
                    f"- {error}"
                )

    if not results:

        st.warning(
            "No publications were recovered from the available "
            "literature sources."
        )

        return

    evidence_summary = (
        score_literature_evidence(
            results
        )
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Literature support",
            f"{evidence_summary['total']}/100"
        )

    with col2:

        st.metric(
            "Literature providers",
            evidence_summary.get(
                "provider_count",
                0
            )
        )

    with col3:

        st.metric(
            "Recent evidence",
            evidence_summary.get(
                "recent_count",
                0
            )
        )

    with col4:

        st.metric(
            "Foundational hits",
            evidence_summary.get(
                "foundational_count",
                0
            )
        )

    st.caption(
        "Literature support combines study type, recent use, "
        "provider confirmation and citation signal. It measures "
        "how well the named tool is represented in the retrieved "
        "literature; it is not treated as a direct measure of "
        "scientific superiority and does not change the OmicsRoute "
        "recommendation score."
    )

    if len(
        results
    ) > 5:

        paper_panel = (
            st.container(
                height=650,
                border=True
            )
        )

    else:

        paper_panel = (
            st.container()
        )

    with paper_panel:

        for index, paper in enumerate(
            results,
            start=1
        ):

            title = (
                paper.get(
                    "title"
                )
                or
                "Untitled publication"
            )

            label = (
                paper.get(
                    "evidence_label",
                    "General evidence"
                )
            )

            st.markdown(
                f"##### {index}. {title}"
            )

            source_providers = (
                paper.get(
                    "source_providers",
                    []
                )
                or
                []
            )

            search_scopes = (
                paper.get(
                    "search_scopes",
                    []
                )
                or
                []
            )

            st.write(
                f"**Evidence type:** "
                f"{label}"
            )

            if source_providers:

                st.write(
                    "**Verified by:**",
                    ", ".join(
                        source_providers
                    )
                )

            if search_scopes:

                scope_labels = []

                if "recent" in search_scopes:

                    scope_labels.append(
                        "recent search"
                    )

                if "foundational" in search_scopes:

                    scope_labels.append(
                        "foundational search"
                    )

                if scope_labels:

                    st.write(
                        "**Search lane:**",
                        ", ".join(
                            scope_labels
                        )
                    )

            meta1, meta2, meta3 = (
                st.columns(3)
            )

            with meta1:

                st.write(
                    "**Year:**",
                    paper.get(
                        "year"
                    )
                    or
                    "Unknown"
                )

            with meta2:

                st.write(
                    "**Journal/source:**",
                    paper.get(
                        "source"
                    )
                    or
                    "Unknown"
                )

            with meta3:

                st.write(
                    "**Citation signal:**",
                    paper.get(
                        "cited_by_count",
                        0
                    )
                    or
                    0
                )

            abstract = (
                paper.get(
                    "abstract"
                )
            )

            if abstract:

                with st.expander(
                    f"Abstract â€” paper {index}"
                ):

                    st.write(
                        abstract
                    )

            links = []

            if paper.get(
                "doi_url"
            ):

                links.append(
                    f"[DOI]"
                    f"({paper['doi_url']})"
                )

            if paper.get(
                "pubmed_url"
            ):

                links.append(
                    f"[PubMed]"
                    f"({paper['pubmed_url']})"
                )

            if paper.get(
                "europepmc_url"
            ):

                links.append(
                    f"[Europe PMC]"
                    f"({paper['europepmc_url']})"
                )

            if paper.get(
                "openalex_url"
            ):

                links.append(
                    f"[OpenAlex]"
                    f"({paper['openalex_url']})"
                )

            if links:

                st.markdown(
                    " | ".join(
                        links
                    )
                )

            st.divider()


# ==================================================
# STEP EVIDENCE
# ==================================================

def evaluate_step_tools(
    workflow_id,
    step_number,
    operation,
    tools
):
    """
    Evaluate literature support for every candidate tool.

    Scoring v2 deliberately does NOT blend this signal into the
    OmicsRoute recommendation score. A failed external search is stored
    as "not evaluated", not as zero evidence.
    """

    state_key = (
        f"step_evidence_v2_"
        f"{workflow_id}_"
        f"{step_number}"
    )

    if st.button(
        "ğŸ“š Evaluate literature evidence for all tools",
        key=(
            f"evaluate_all_v2_"
            f"{workflow_id}_"
            f"{step_number}"
        )
    ):

        evaluations = {}

        progress = st.progress(
            0
        )

        total_tools = len(
            tools
        )

        search_operation = (
            operation
            .replace(
                "_",
                " "
            )
            .strip()
        )

        for index, tool in enumerate(
            tools,
            start=1
        ):

            result = (
                cached_literature_search(
                    tool[
                        "name"
                    ],
                    search_operation
                )
            )

            evidence_available = (
                not result.get(
                    "error"
                )
            )

            if not evidence_available:

                evidence_summary = {
                    "total": None,
                    "benchmark_count": 0,
                    "method_count": 0,
                    "review_count": 0,
                    "application_count": 0,
                    "relevant_count": 0
                }

            else:

                papers = (
                    classify_papers(
                        result.get(
                            "results",
                            []
                        ),
                        tool[
                            "name"
                        ],
                        operation=operation
                    )
                )

                papers = (
                    rank_evidence(
                        papers
                    )
                )

                result[
                    "results"
                ] = papers

                evidence_summary = (
                    score_literature_evidence(
                        papers
                    )
                )

            base_score = (
                tool[
                    "score"
                ][
                    "total"
                ]
            )

            literature_score = (
                evidence_summary.get(
                    "total"
                )
            )

            evaluations[
                tool[
                    "id"
                ]
            ] = {
                "recommendation_score": base_score,
                "base_score": base_score,
                "literature_score": literature_score,
                "evidence_available": evidence_available,
                "evidence_rank_signal": (
                    evidence_rank_signal(
                        literature_score,
                        available=evidence_available
                    )
                ),
                "evidence": evidence_summary,

                # Backward-compatible field. In scoring v2 literature
                # no longer rewrites the OmicsRoute recommendation score.
                "final_score": base_score
            }

            individual_key = (
                f"literature_data_"
                f"{workflow_id}_"
                f"{step_number}_"
                f"{tool['id']}"
            )

            st.session_state[
                individual_key
            ] = result

            if total_tools:

                progress.progress(
                    index
                    /
                    total_tools
                )

        progress.empty()

        st.session_state[
            state_key
        ] = evaluations

    return (
        st.session_state.get(
            state_key
        )
    )


# ==================================================
# OPERATIONAL FEASIBILITY
# ==================================================

def show_compute_environment_profile():
    """
    Optional local/HPC compute profile.

    Operational feasibility is kept separate from scientific
    suitability. When enabled, it can influence display ranking
    after technical dependency status, but it never silently
    changes the scientific OmicsRoute score.
    """

    with st.expander(
        "ğŸ’» Compute environment & operational feasibility",
        expanded=False
    ):

        enabled = st.checkbox(
            "Use my compute environment when ranking tools",
            value=False,
            key="operational_profile_enabled"
        )

        st.caption(
            "This checks practical execution issues such as operating "
            "system, RAM, CPU, free disk, database footprint and "
            "available fallback routes. Scientific suitability remains "
            "a separate score."
        )

        if not enabled:

            st.info(
                "Operational re-ranking is off. OmicsRoute will keep the "
                "current scientific/technical ranking."
            )

            return {
                "enabled": False
            }

        detected = (
            platform.system()
            .strip()
            .lower()
        )

        if detected.startswith(
            "win"
        ):

            default_os = (
                "Windows"
            )

        elif detected.startswith(
            "darwin"
        ):

            default_os = (
                "macOS"
            )

        else:

            default_os = (
                "Linux"
            )

        os_options = [
            "Windows",
            "Linux",
            "macOS"
        ]

        default_index = (
            os_options.index(
                default_os
            )
            if default_os
            in os_options
            else
            0
        )

        col1, col2, col3 = (
            st.columns(3)
        )

        with col1:

            operating_system = (
                st.selectbox(
                    "Target operating system",
                    os_options,
                    index=default_index,
                    key="operational_os"
                )
            )

            ram_gb = (
                st.number_input(
                    "RAM (GB)",
                    min_value=1,
                    max_value=4096,
                    value=16,
                    step=1,
                    key="operational_ram_gb"
                )
            )

            cpu_cores = (
                st.number_input(
                    "CPU cores",
                    min_value=1,
                    max_value=512,
                    value=max(
                        1,
                        min(
                            os.cpu_count()
                            or
                            8,
                            64
                        )
                    ),
                    step=1,
                    key="operational_cpu_cores"
                )
            )

        with col2:

            free_disk_gb = (
                st.number_input(
                    "Free disk space (GB)",
                    min_value=1,
                    max_value=100000,
                    value=100,
                    step=10,
                    key="operational_free_disk_gb"
                )
            )

            dataset_scale = (
                st.selectbox(
                    "Approximate dataset scale",
                    [
                        "Small",
                        "Moderate",
                        "Large"
                    ],
                    index=1,
                    key="operational_dataset_scale"
                )
            )

            internet = (
                st.selectbox(
                    "Internet / download capacity",
                    [
                        "Normal",
                        "Limited",
                        "Fast"
                    ],
                    index=0,
                    key="operational_internet"
                )
            )

        with col3:

            gpu_available = (
                st.checkbox(
                    "Compatible GPU available",
                    value=False,
                    key="operational_gpu"
                )
            )

            if (
                operating_system
                ==
                "Windows"
            ):

                wsl_available = (
                    st.checkbox(
                        "WSL available",
                        value=False,
                        key="operational_wsl"
                    )
                )

            else:

                wsl_available = False

            container_available = (
                st.checkbox(
                    "Docker / containers available",
                    value=False,
                    key="operational_container"
                )
            )

            hpc_available = (
                st.checkbox(
                    "HPC / remote Linux / cloud compute available",
                    value=False,
                    key="operational_hpc"
                )
            )

            large_database_ok = (
                st.checkbox(
                    "Very large reference databases are practical for me",
                    value=False,
                    key="operational_large_database"
                )
            )

            web_services_allowed = (
                st.checkbox(
                    "Online analysis services are allowed",
                    value=True,
                    key="operational_web_services"
                )
            )

        st.caption(
            "Resource warnings based on qualitative demand labels are "
            "heuristics, not universal vendor minimums. OmicsRoute only "
            "uses hard blocking when a requirement is explicit."
        )

        return {
            "enabled": True,
            "operating_system": operating_system,
            "ram_gb": ram_gb,
            "cpu_cores": cpu_cores,
            "free_disk_gb": free_disk_gb,
            "dataset_scale": dataset_scale,
            "internet": internet,
            "gpu_available": gpu_available,
            "wsl_available": wsl_available,
            "container_available": container_available,
            "hpc_available": hpc_available,
            "large_database_ok": large_database_ok,
            "web_services_allowed": web_services_allowed
        }


def show_operational_feasibility(
    result
):
    """
    Render one tool's operational-feasibility assessment.
    """

    if not isinstance(
        result,
        dict
    ):

        return

    status = (
        result.get(
            "status",
            "unknown"
        )
    )

    if status == "not_evaluated":

        return

    st.markdown(
        "#### ğŸ’» Operational feasibility"
    )

    if status == "good":

        st.success(
            "âœ“ Good operational fit for the selected compute profile."
        )

    elif status == "warning":

        st.warning(
            "âš  Potential operational friction for the selected compute profile."
        )

    elif status == "blocked":

        st.error(
            "â›” Operationally blocked for the selected compute profile."
        )

    else:

        st.info(
            "Operational feasibility is currently unknown because this "
            "tool has not yet received curated resource metadata."
        )

    for blocker in result.get(
        "blockers",
        []
    ):

        st.write(
            f"- â›” {blocker}"
        )

    for warning in result.get(
        "warnings",
        []
    ):

        st.write(
            f"- âš ï¸ {warning}"
        )

    for reason in result.get(
        "reasons",
        []
    ):

        st.write(
            f"- {reason}"
        )

    details = (
        result.get(
            "details",
            {}
        )
        or
        {}
    )

    compute = (
        details.get(
            "compute",
            {}
        )
        or
        {}
    )

    database = (
        details.get(
            "database",
            {}
        )
        or
        {}
    )

    labels = []

    if compute.get(
        "memory_demand"
    ):

        labels.append(
            "RAM: "
            f"{compute['memory_demand']}"
        )

    if compute.get(
        "cpu_demand"
    ):

        labels.append(
            "CPU: "
            f"{compute['cpu_demand']}"
        )

    if compute.get(
        "disk_demand"
    ):

        labels.append(
            "Disk: "
            f"{compute['disk_demand']}"
        )

    if database.get(
        "required",
        False
    ):

        footprint = (
            database.get(
                "footprint",
                "database-dependent"
            )
        )

        labels.append(
            "Database: "
            f"{footprint}"
        )

    if labels:

        st.caption(
            " â€¢ ".join(
                labels
            )
        )

    notes = (
        details.get(
            "notes",
            []
        )
        or
        []
    )

    if notes:

        st.write(
            "**Operational notes:**"
        )

        for note in notes:

            st.write(
                f"- {note}"
            )


# ==================================================
# DISCOVERY
# ==================================================

def show_tool_discovery(
    workflow_id,
    step_number,
    operation,
    curated_tools,
    context=None
):
    """
    Capability-aware discovery display.

    Direct alternatives, related-but-different workflows, and unknown
    registry leads are intentionally kept in separate sections.
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

    state_key = (
        f"discovery_v4_"
        f"{workflow_id}_"
        f"{step_number}"
    )

    curated_tool_names = tuple(
        sorted(
            {
                str(
                    tool.get(
                        "name",
                        ""
                    )
                ).strip()
                for tool
                in curated_tools
                if tool.get(
                    "name"
                )
            }
        )
    )

    search_depth = (
        st.selectbox(
            "Discovery search depth",
            [
                "Standard",
                "Deep"
            ],
            index=0,
            key=(
                f"discovery_depth_v4_"
                f"{workflow_id}_"
                f"{step_number}"
            )
        )
    )

    st.caption(
        "Deep searches a larger part of the structured bio.tools "
        "registry. It does not mine arbitrary words from papers."
    )

    if st.button(
        "ğŸ” Research additional alternatives",
        key=(
            f"discover_tools_v4_"
            f"{workflow_id}_"
            f"{step_number}"
        )
    ):

        with st.spinner(
            "Checking OmicsRoute capability records and bio.tools..."
        ):

            result = (
                cached_systematic_discovery(
                    operation,
                    str(
                        context.get(
                            "sample_type",
                            ""
                        )
                    ),
                    str(
                        context.get(
                            "sequencing",
                            ""
                        )
                    ),
                    str(
                        context.get(
                            "read_type",
                            ""
                        )
                    ),
                    str(
                        context.get(
                            "goal",
                            ""
                        )
                    ),
                    str(
                        context.get(
                            "feature_strategy",
                            ""
                        )
                    ),
                    str(
                        context.get(
                            "marker",
                            ""
                        )
                    ),
                    curated_tool_names,
                    search_depth
                )
            )

            st.session_state[
                state_key
            ] = result

    if state_key not in st.session_state:

        return

    result = st.session_state[
        state_key
    ]

    st.markdown(
        "### Research results"
    )

    selected_strategy = (
        context.get(
            "feature_strategy"
        )
        or
        "not specified"
    )

    marker = (
        context.get(
            "marker"
        )
        or
        "generic"
    )

    st.caption(
        f"Selected feature strategy: {str(selected_strategy).upper()} "
        f"â€¢ marker: {marker} â€¢ operation: {operation}"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Verified direct alternatives",
            result.get(
                "compatible_count",
                0
            )
        )

    with c2:

        st.metric(
            "Related routes",
            result.get(
                "related_count",
                0
            )
        )

    with c3:

        st.metric(
            "Unverified registry leads",
            result.get(
                "unverified_count",
                0
            )
        )

    with c4:

        st.metric(
            "bio.tools hits",
            result.get(
                "registry_candidate_count",
                0
            )
        )

    if result.get(
        "error"
    ):

        st.error(
            result[
                "error"
            ]
        )

    partial_errors = (
        result.get(
            "partial_errors",
            []
        )
        or
        []
    )

    if partial_errors:

        with st.expander(
            "âš ï¸ Registry warnings"
        ):

            for error in partial_errors:

                st.write(
                    f"- {error}"
                )

    structured_terms = (
        result.get(
            "structured_operation_terms",
            []
        )
        or
        []
    )

    query_family = (
        result.get(
            "query_family",
            []
        )
        or
        []
    )

    with st.expander(
        "Search strategy"
    ):

        if structured_terms:

            st.write(
                "**Structured bio.tools operation filters:**"
            )

            for term in structured_terms:

                st.write(
                    f"- {term}"
                )

        if query_family:

            st.write(
                "**Supplementary registry queries:**"
            )

            for query in query_family:

                st.write(
                    f"- {query}"
                )

    # --------------------------------------------------
    # VERIFIED DIRECT ALTERNATIVES
    # --------------------------------------------------

    compatible = (
        result.get(
            "compatible_results",
            []
        )
        or
        []
    )

    st.markdown(
        "#### âœ… Verified direct alternatives"
    )

    st.caption(
        "These match the selected operation, ASV/OTU strategy, "
        "marker/context and step scope according to OmicsRoute's curated "
        "capability records."
    )

    if not compatible:

        st.info(
            "No additional verified direct alternatives remain after "
            "removing the tools already shown in the curated ranking."
        )

    for candidate in compatible:

        evaluation = (
            candidate.get(
                "capability_evaluation",
                {}
            )
            or
            {}
        )

        with st.expander(
            f"âœ… {candidate.get('name', 'Unnamed resource')}"
        ):

            for reason in evaluation.get(
                "reasons",
                []
            ):

                st.write(
                    f"- {reason}"
                )

            if candidate.get(
                "description"
            ):

                st.write(
                    candidate[
                        "description"
                    ]
                )

            capability_record = (
                candidate.get(
                    "capability_record",
                    {}
                )
                or
                {}
            )

            components = (
                capability_record.get(
                    "components",
                    {}
                )
                or
                {}
            )

            if operation in components:

                st.write(
                    "**Relevant component:**",
                    components[
                        operation
                    ]
                )

            evidence_urls = (
                capability_record.get(
                    "evidence_urls",
                    []
                )
                or
                []
            )

            if evidence_urls:

                st.write(
                    "**Capability sources:**"
                )

                for url in evidence_urls:

                    st.markdown(
                        f"- {url}"
                    )

            if candidate.get(
                "biotools_url"
            ):

                st.markdown(
                    f"[bio.tools record]"
                    f"({candidate['biotools_url']})"
                )

    # --------------------------------------------------
    # RELATED, BUT NOT DROP-IN
    # --------------------------------------------------

    related = (
        result.get(
            "related_results",
            []
        )
        or
        []
    )

    st.markdown(
        "#### ğŸ§­ Related, but not a drop-in replacement"
    )

    st.caption(
        "These are scientifically relevant alternatives, but they use "
        "another feature strategy, represent an end-to-end service/framework, "
        "or need a different input route. OmicsRoute does not mix them into the "
        "direct tool ranking."
    )

    if not related:

        st.info(
            "No curated related routes were found for this step."
        )

    for candidate in related:

        evaluation = (
            candidate.get(
                "capability_evaluation",
                {}
            )
            or
            {}
        )

        capability_record = (
            candidate.get(
                "capability_record",
                {}
            )
            or
            {}
        )

        resource_type = (
            capability_record.get(
                "resource_type"
            )
            or
            evaluation.get(
                "resource_type"
            )
            or
            "resource"
        )

        with st.expander(
            f"ğŸ§­ {candidate.get('name', 'Unnamed resource')} "
            f"â€” {resource_type}"
        ):

            st.write(
                "**Why it is not in the direct ranking:**"
            )

            for reason in evaluation.get(
                "reasons",
                []
            ):

                st.write(
                    f"- {reason}"
                )

            notes = (
                capability_record.get(
                    "notes",
                    []
                )
                or
                []
            )

            if notes:

                st.write(
                    "**What it can do:**"
                )

                for note in notes:

                    st.write(
                        f"- {note}"
                    )

            components = (
                capability_record.get(
                    "components",
                    {}
                )
                or
                {}
            )

            if components:

                st.write(
                    "**Relevant named components:**"
                )

                for component_operation, component_name in components.items():

                    st.write(
                        f"- {component_operation}: {component_name}"
                    )

            evidence_urls = (
                capability_record.get(
                    "evidence_urls",
                    []
                )
                or
                []
            )

            if evidence_urls:

                st.write(
                    "**Capability sources:**"
                )

                for url in evidence_urls:

                    st.markdown(
                        f"- {url}"
                    )

            if candidate.get(
                "biotools_url"
            ):

                st.markdown(
                    f"[bio.tools record]"
                    f"({candidate['biotools_url']})"
                )

    # --------------------------------------------------
    # UNVERIFIED STRUCTURED REGISTRY LEADS
    # --------------------------------------------------

    unverified = (
        result.get(
            "unverified_results",
            []
        )
        or
        []
    )

    st.markdown(
        "#### ğŸ—‚ï¸ Unverified bio.tools leads"
    )

    st.caption(
        "These were found in the structured registry, but OmicsRoute has "
        "not yet curated their ASV/OTU/marker capability. They are leads "
        "for review, not recommendations."
    )

    if not unverified:

        st.info(
            "No additional unverified registry leads were recovered."
        )

        return

    filter_text = (
        st.text_input(
            "Filter registry leads",
            value="",
            placeholder="Tool name, operation or topic...",
            key=(
                f"registry_filter_v4_"
                f"{workflow_id}_"
                f"{step_number}"
            )
        )
        .strip()
        .lower()
    )

    visible = []

    for candidate in unverified:

        searchable = " ".join(
            [
                str(
                    candidate.get(
                        "name",
                        ""
                    )
                ),
                str(
                    candidate.get(
                        "description",
                        ""
                    )
                ),
                " ".join(
                    candidate.get(
                        "operations",
                        []
                    )
                    or
                    []
                ),
                " ".join(
                    candidate.get(
                        "topics",
                        []
                    )
                    or
                    []
                )
            ]
        ).lower()

        if (
            not filter_text
            or
            filter_text
            in searchable
        ):

            visible.append(
                candidate
            )

    st.caption(
        f"Showing {len(visible)} of {len(unverified)} "
        "unverified registry leads."
    )

    panel = (
        st.container(
            height=600,
            border=True
        )
        if len(
            visible
        )
        >
        5
        else
        st.container()
    )

    with panel:

        for candidate in visible:

            screening = (
                candidate.get(
                    "discovery_score",
                    {}
                )
                or
                {}
            )

            score = screening.get(
                "total",
                0
            )

            with st.expander(
                f"ğŸ—‚ï¸ {candidate.get('name', 'Unnamed resource')} "
                f"â€” registry screening {score}/100"
            ):

                st.warning(
                    "Capability not yet curated: do not interpret this "
                    "registry screening score as ASV/OTU compatibility."
                )

                if candidate.get(
                    "description"
                ):

                    st.write(
                        candidate[
                            "description"
                        ]
                    )

                if candidate.get(
                    "operations"
                ):

                    st.write(
                        "**Registered operations:**",
                        ", ".join(
                            candidate[
                                "operations"
                            ]
                        )
                    )

                if candidate.get(
                    "topics"
                ):

                    st.write(
                        "**Registered topics:**",
                        ", ".join(
                            candidate[
                                "topics"
                            ]
                        )
                    )

                if candidate.get(
                    "biotools_url"
                ):

                    st.markdown(
                        f"[Open bio.tools record]"
                        f"({candidate['biotools_url']})"
                    )


# ==================================================
# HEADER
# ==================================================

st.markdown(
    """
    <div class="omicsroute-hero">
        <div class="omicsroute-eyebrow">BIOFLOW â€¢ WEB RELEASE CANDIDATE</div>
        <h1>Build evidence-aware bioinformatics workflows</h1>
        <p>
            Build a context-specific analysis route from sample type,
            sequencing setup, biological objective, dataset constraints,
            technical dependencies, and operational feasibility.
        </p>
        <div class="omicsroute-chips">
            <span class="omicsroute-chip">Scientific fit</span>
            <span class="omicsroute-chip">Constraint-aware</span>
            <span class="omicsroute-chip">Dependency-validated</span>
            <span class="omicsroute-chip">Fallback-aware</span>
            <span class="omicsroute-chip">Exportable</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

link_col, note_col = st.columns(
    [1, 3],
    vertical_alignment="center"
)

with link_col:
    st.link_button(
        "View source on GitHub â†—",
        "https://github.com/isilayc/omicsroute"
    )

with note_col:
    st.caption(
        "OmicsRoute recommends analysis workflows and tools; it does not execute "
        "the underlying bioinformatics software."
    )

st.markdown("#### How OmicsRoute works")

quick_1, quick_2, quick_3, quick_4 = st.columns(4)

with quick_1:
    st.markdown(
        """
        <div class="omicsroute-step">
            <div class="omicsroute-step-number">STEP 1</div>
            <div class="omicsroute-step-title">Describe the analysis</div>
            <div class="omicsroute-step-text">
                Select sample type, sequencing setup and analysis goal.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with quick_2:
    st.markdown(
        """
        <div class="omicsroute-step">
            <div class="omicsroute-step-number">STEP 2</div>
            <div class="omicsroute-step-title">Choose the route</div>
            <div class="omicsroute-step-text">
                Compare curated workflow strategies for the selected context.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with quick_3:
    st.markdown(
        """
        <div class="omicsroute-step">
            <div class="omicsroute-step-number">STEP 3</div>
            <div class="omicsroute-step-title">Check suitability</div>
            <div class="omicsroute-step-text">
                Evaluate dataset constraints, dependencies and compute fit.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with quick_4:
    st.markdown(
        """
        <div class="omicsroute-step">
            <div class="omicsroute-step-number">STEP 4</div>
            <div class="omicsroute-step-title">Review &amp; export</div>
            <div class="omicsroute-step-text">
                Review the recommended route, then download it as Markdown or JSON.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with st.expander(
    "ğŸ“š Catalogue coverage & validation",
    expanded=False
):
    show_analysis_coverage()

with st.expander(
    "â„¹ï¸ About OmicsRoute & methodology",
    expanded=False
):
    about_tab, method_tab, limits_tab = st.tabs(
        [
            "About",
            "Methodology",
            "Interpretation"
        ]
    )

    with about_tab:
        st.markdown("### OmicsRoute v1.1.0")
        st.write(
            "OmicsRoute is a bioinformatics workflow planning and decision-support "
            "system. It builds context-specific analysis routes from the sample "
            "type, sequencing setup, biological objective, technical dependencies, "
            "dataset constraints, and operational context."
        )
        st.write(
            "OmicsRoute recommends workflows and candidate tools; it does not execute "
            "the underlying bioinformatics software."
        )
        st.caption(
            "Public web release: v1.1.0 â€¢ "
            "Source: https://github.com/isilayc/omicsroute"
        )

    with method_tab:
        st.markdown("### How recommendations are formed")
        st.markdown(
            """
            **1. Workflow context**  
            OmicsRoute first narrows the catalogue using sample type, sequencing
            technology, read type, analysis goal, and route-specific context.

            **2. Scientific fit**  
            Candidate tools are evaluated within the selected workflow step and
            biological strategy. Scientific suitability is kept separate from
            implementation constraints.

            **3. Technical dependency validation**  
            The engine checks whether the artifacts required by a downstream
            step can be produced by the upstream workflow. Tools with missing
            prerequisite artifacts remain visible but are not treated as ready.

            **4. Dataset and operational constraints**  
            Dataset-specific rules can return PASS, WARNING, BLOCK, or request
            additional input. Compute feasibility is evaluated separately when
            a compute profile is supplied.

            **5. Evidence and fallback logic**  
            Literature and registry evidence can refine otherwise comparable
            candidates, but it does not override hard technical or dataset
            blocks. If a route is blocked, OmicsRoute distinguishes direct
            alternatives, alternative workflow strategies, and remediation
            when no equivalent substitute is represented.
            """
        )

    with limits_tab:
        st.markdown("### How to interpret OmicsRoute")
        st.write(
            "OmicsRoute is research software and should be used as decision support, "
            "not as a substitute for the documentation and assumptions of the "
            "underlying bioinformatics tools."
        )
        st.write(
            "Recommendation scores are OmicsRoute support scores within the curated "
            "catalogue; they are not universal measures of tool quality."
        )
        st.write(
            "The current benchmark is an internal curated benchmark used for "
            "regression and recommendation validation. It is not an independent "
            "external gold-standard benchmark."
        )
        st.write(
            "Users should interpret each recommendation together with dataset "
            "characteristics, reference-database requirements, compute resources, "
            "and the intended biological question."
        )

st.divider()

st.markdown("## Build a workflow")
st.caption(
    "Start with the biological and sequencing context. OmicsRoute will narrow "
    "the available strategies as you go."
)


# ==================================================
# INPUTS
# ==================================================

sample_options = (
    get_sample_types()
)

if not sample_options:

    st.error(
        "No workflows available."
    )

    st.stop()


sample = st.selectbox(
    "Sample type",
    sample_options
)


sequencing_options = (
    get_sequencing_options(
        sample
    )
)

if not sequencing_options:

    st.error(
        "No sequencing technologies "
        "are available for this sample type."
    )

    st.stop()


sequencing = st.selectbox(
    "Sequencing technology",
    sequencing_options
)


read_type_options = (
    get_read_type_options(
        sample,
        sequencing
    )
)

if not read_type_options:

    st.error(
        "No read types are available "
        "for this combination."
    )

    st.stop()


read_type = st.selectbox(
    "Read type",
    read_type_options
)


goal_options = (
    get_goal_options(
        sample,
        sequencing,
        read_type
    )
)

if not goal_options:

    st.error(
        "No analysis goals are available "
        "for this combination."
    )

    st.stop()


goal = st.selectbox(
    "Analysis goal",
    goal_options
)


reference_scope_id = None

reference_scope_options = (
    get_scope_options(
        goal
    )
)

if (
    sample
    ==
    "Amplicon"
    and
    reference_scope_options
):

    reference_scope_lookup = {
        item[
            "id"
        ]: item[
            "label"
        ]
        for item
        in reference_scope_options
    }

    reference_scope_ids = list(
        reference_scope_lookup.keys()
    )

    default_scope = (
        get_default_scope(
            goal
        )
    )

    default_scope_index = (
        reference_scope_ids.index(
            default_scope
        )
        if default_scope
        in reference_scope_ids
        else
        0
    )

    reference_scope_id = st.selectbox(
        get_scope_label(
            goal
        ),
        reference_scope_ids,
        index=default_scope_index,
        format_func=lambda scope_id: (
            reference_scope_lookup[
                scope_id
            ]
        )
    )


workflow_strategies = (
    get_workflow_strategies(
        sample,
        sequencing,
        read_type,
        goal
    )
)

if not workflow_strategies:

    st.error(
        "No workflow strategy could be resolved "
        "for the selected context."
    )

    st.stop()


strategy_lookup = {
    strategy[
        "id"
    ]: strategy
    for strategy
    in workflow_strategies
}

strategy_ids = list(
    strategy_lookup.keys()
)

if len(strategy_ids) > 1:

    if sample == "Amplicon":

        st.markdown(
            "### Analysis route"
        )

        if goal == "Alpha diversity":

            st.caption(
                "Alpha diversity is treated as a downstream module from an existing "
                "amplicon feature table. Choose whether the biological question needs "
                "a non-phylogenetic metric or an explicit phylogenetic metric."
            )

            strategy_label = (
                "Alpha-diversity metric family"
            )

        elif goal == "Beta diversity":

            st.caption(
                "Beta diversity is treated as a downstream module from an existing "
                "amplicon feature table. Choose non-phylogenetic community dissimilarity "
                "or phylogenetic UniFrac according to the biological question."
            )

            strategy_label = (
                "Beta-diversity metric family"
            )

        elif goal == "Differential abundance":

            st.caption(
                "Differential abundance starts from an existing microbial feature-count "
                "table plus sample metadata. Choose the study-design class so OmicsRoute can "
                "rank statistical methods by their actual modelling capabilities. There is "
                "no universal gold-standard microbiome DA method, so method assumptions and "
                "robustness across alternatives remain important."
            )

            strategy_label = (
                "Differential-abundance study design"
            )

        else:

            st.caption(
                "Amplicon analysis is not a single ASV-vs-OTU switch. "
                "OmicsRoute treats complete ecosystems and workflows as separate "
                "routes when their preprocessing, feature-generation and taxonomy "
                "logic differ. Choose the route you actually want to run."
            )

            strategy_label = (
                "Amplicon analysis route"
            )

    else:

        st.caption(
            "More than one end-to-end strategy is available for this goal."
        )

        strategy_label = (
            "Workflow strategy"
        )

    selected_strategy_id = st.selectbox(
        strategy_label,
        strategy_ids,
        format_func=lambda workflow_id: (
            strategy_lookup[
                workflow_id
            ][
                "name"
            ]
        )
    )

    selected_strategy_description = (
        strategy_lookup[
            selected_strategy_id
        ].get(
            "description",
            ""
        )
    )

    if selected_strategy_description:

        st.caption(
            selected_strategy_description
        )

else:

    selected_strategy_id = (
        strategy_ids[0]
    )


if reference_scope_id:

    show_reference_guidance(
        goal,
        selected_strategy_id,
        reference_scope_id
    )


compute_profile = (
    show_compute_environment_profile()
)


st.caption(
    f"Selected context: "
    f"{sample} â†’ "
    f"{sequencing} â†’ "
    f"{read_type} â†’ "
    f"{goal}"
)


# ==================================================
# BUILD
# ==================================================

if st.button(
    "Build workflow",
    type="primary"
):

    built_workflow = (
        build_workflow(
            sample,
            sequencing,
            read_type,
            goal,
            workflow_id=selected_strategy_id,
            compute_profile=compute_profile
        )
    )

    if (
        built_workflow
        is not None
        and
        reference_scope_id
    ):

        built_workflow.setdefault(
            "context",
            {}
        )[
            "reference_scope"
        ] = reference_scope_id

    st.session_state.workflow = (
        built_workflow
    )


# ==================================================
# DISPLAY
# ==================================================

workflow = (
    st.session_state.workflow
)


if workflow is None:

    st.info(
        "Select your dataset characteristics "
        "and click 'Build workflow'."
    )

else:

    current_context = (
        workflow.get(
            "context",
            {}
        )
    )

    selected_context = {
        "sample_type": sample,
        "sequencing": sequencing,
        "read_type": read_type,
        "goal": goal
    }

    if reference_scope_id:

        selected_context[
            "reference_scope"
        ] = reference_scope_id

    selection_changed = (
        any(
            current_context.get(
                field_name
            )
            !=
            field_value
            for field_name, field_value
            in selected_context.items()
        )
        or
        workflow.get(
            "id"
        )
        != selected_strategy_id
    )

    if selection_changed:

        st.warning(
            "Your selections or workflow strategy have changed. "
            "Click 'Build workflow' again to update the recommendation."
        )

    st.divider()

    st.header(
        "Recommended workflow"
    )

    st.caption(
        workflow[
            "name"
        ]
    )

    if len(workflow_strategies) > 1:

        st.write(
            "**Selected strategy:** "
            f"{workflow['name']}"
        )

    if workflow.get(
        "description"
    ):

        st.write(
            workflow[
                "description"
            ]
        )

    dependency_validation = (
        cached_validate_workflow(
            workflow[
                "id"
            ],
            get_dependency_signature()
        )
    )

    show_workflow_overview_and_export(
        workflow,
        dependency_validation
    )

    show_workflow_input_requirements(
        workflow,
        dependency_validation
    )

    show_workflow_dependency_validation(
        dependency_validation
    )

    dataset_profile = (
        show_workflow_dataset_profile(
            workflow
        )
    )

    dependency_step_reports = {
        step_report.get(
            "step_number"
        ): step_report
        for step_report
        in dependency_validation.get(
            "steps",
            []
        )
    }

    for number, step in enumerate(
        workflow[
            "steps"
        ],
        start=1
    ):

        st.subheader(
            f"{number}. "
            f"{step['name']}"
        )

        st.write(
            step[
                "description"
            ]
        )

        step_mode = (
            step.get(
                "mode",
                "sequential"
            )
            or
            "sequential"
        )

        tools = (
            step.get(
                "tools",
                []
            )
        )

        step_dependency_report = (
            dependency_step_reports.get(
                number
            )
        )

        if step_mode == "parallel":

            min_required = (
                step.get(
                    "min_successful_candidates",
                    1
                )
                or
                1
            )

            aggregate_outputs = (
                step.get(
                    "aggregate_produces",
                    []
                )
                or
                []
            )

            tool_names = [
                tool.get(
                    "name",
                    tool.get(
                        "id",
                        "tool"
                    )
                )
                for tool in tools
            ]

            st.info(
                "ğŸ”€ **Run multiple tools here â€” do not choose only one.** "
                "Each tool receives the same upstream data and produces "
                "an independent result. OmicsRoute needs at least "
                f"**{min_required}** successful tool results before the "
                "workflow can continue."
            )

            if tool_names:

                st.write(
                    "**Run independently:** "
                    +
                    " â€¢ ".join(
                        tool_names
                    )
                )

            if aggregate_outputs:

                st.caption(
                    "These independent results are then passed forward as: "
                    +
                    ", ".join(
                        get_artifact_label(
                            artifact_id
                        )
                        for artifact_id
                        in aggregate_outputs
                    )
                )

        if not tools:

            st.error(
                "No candidate tools found."
            )

            continue

        operational_lookup = {
            tool[
                "id"
            ]: (
                evaluate_operational_feasibility(
                    tool,
                    compute_profile,
                    operation=step[
                        "operation"
                    ]
                )
            )
            for tool
            in tools
        }

        # --------------------------------------------------
        # CURATED RECOMMENDATIONS FIRST
        # --------------------------------------------------
        #
        # Research discovery used to render in a side column before
        # the curated ranking. Once discovery returned many results,
        # Streamlit pushed the actual OmicsRoute recommendations below
        # the discovery panel, making it look as if no tool had been
        # recommended. Curated recommendations now always render first.
        #
        evidence_results = (
            evaluate_step_tools(
                workflow[
                    "id"
                ],
                number,
                step[
                    "operation"
                ],
                tools
            )
        )

        # Scoring v2 keeps the curated recommendation score stable.
        # Literature is a separate evidence signal and can only break
        # otherwise equivalent rankings.
        score_lookup = {
            tool[
                "id"
            ]: (
                tool[
                    "score"
                ][
                    "total"
                ]
            )
            for tool in tools
        }

        evidence_lookup = {
            tool[
                "id"
            ]: (
                (
                    evidence_results.get(
                        tool[
                            "id"
                        ],
                        {}
                    ).get(
                        "evidence_rank_signal",
                        -1
                    )
                )
                if evidence_results
                else
                -1
            )
            for tool in tools
        }

        constraint_lookup = {
            tool[
                "id"
            ]: (
                evaluate_step_tool_constraints(
                    workflow,
                    step,
                    tool,
                    dataset_profile
                )
            )
            for tool in tools
        }

        if step_mode == "parallel":

            st.markdown(
                "### Tools to run in parallel"
            )

            st.caption(
                "Parallel branches are not ranked against one another. "
                "Technical prerequisites and dataset-specific BLOCK conditions "
                "still determine whether a branch is ready to run."
            )

            display_tools = list(
                tools
            )

            runnable_branch_count = sum(
                1
                for tool in display_tools
                if (
                    get_tool_dependency_status(
                        step_dependency_report,
                        tool[
                            "id"
                        ]
                    )[
                        "status"
                    ]
                    == "runnable"
                    and
                    constraint_lookup[
                        tool[
                            "id"
                        ]
                    ].get(
                        "status"
                    )
                    != "block"
                )
            )

            col_a, col_b = st.columns(2)

            with col_a:

                st.metric(
                    "Tools ready to run",
                    runnable_branch_count
                )

            with col_b:

                st.metric(
                    "Successful results needed",
                    step.get(
                        "min_successful_candidates",
                        1
                    )
                )

            for branch_number, tool in enumerate(
                display_tools,
                start=1
            ):

                technical = (
                    get_tool_dependency_status(
                        step_dependency_report,
                        tool[
                            "id"
                        ]
                    )
                )

                technical_status = (
                    technical[
                        "status"
                    ]
                )

                constraint_status = (
                    constraint_lookup[
                        tool[
                            "id"
                        ]
                    ].get(
                        "status",
                        "not_defined"
                    )
                )

                if technical_status == "blocked":

                    st.error(
                        f"â›” {tool['name']} â€” cannot run because an input is missing"
                    )

                elif constraint_status == "block":

                    st.error(
                        f"â›” {tool['name']} â€” dataset-specific constraint blocks this branch"
                    )

                elif technical_status == "unknown":

                    st.warning(
                        f"âš ï¸ {tool['name']} â€” I/O metadata is incomplete"
                    )

                elif constraint_status == "warning":

                    st.warning(
                        f"âš ï¸ {tool['name']} â€” ready with a dataset-specific warning"
                    )

                elif technical_status == "runnable":

                    st.success(
                        f"âœ… {tool['name']} â€” ready to run"
                    )

                else:

                    st.write(
                        f"**â– {tool['name']} â€” not evaluated**"
                    )

        else:

            st.markdown(
                "### Tool ranking"
            )

            if compute_profile.get(
                "enabled",
                False
            ):

                st.caption(
                    "Eligibility gates are applied before ranking. Open a tool card "
                    "for compute, prerequisite and dataset-specific details."
                )

            has_strategy_fit = any(
                isinstance(
                    tool.get(
                        "strategy_fit"
                    ),
                    dict
                )
                and
                tool.get(
                    "strategy_fit",
                    {}
                ).get(
                    "fit"
                )
                for tool in tools
            )

            if evidence_results:

                st.caption(
                    "Eligible tools are ordered by scientific fit, dataset warnings, "
                    "OmicsRoute support score and literature evidence tie-breakers."
                )

            elif has_strategy_fit:

                st.caption(
                    "Blocked tools stay visible for transparency; eligible tools are "
                    "ordered by scientific fit, dataset warnings and OmicsRoute support score."
                )

            else:

                st.caption(
                    "Blocked tools stay visible for transparency; eligible tools are "
                    "ordered by scientific suitability, warnings and OmicsRoute support score."
                )

            def _ranking_signature(
                tool
            ):

                return (
                    dependency_status_priority(
                        get_tool_dependency_status(
                            step_dependency_report,
                            tool[
                                "id"
                            ]
                        )[
                            "status"
                        ]
                    ),

                    operational_hard_gate_priority(
                        operational_lookup[
                            tool[
                                "id"
                            ]
                        ][
                            "status"
                        ],
                        enabled=compute_profile.get(
                            "enabled",
                            False
                        )
                    ),

                    constraint_hard_gate_priority(
                        constraint_lookup[
                            tool[
                                "id"
                            ]
                        ].get(
                            "status",
                            "not_defined"
                        )
                    ),

                    scientific_fit_priority(
                        tool.get(
                            "score",
                            {}
                        ).get(
                            "scientific_fit_label",
                            "curated"
                        )
                    ),

                    constraint_soft_priority(
                        constraint_lookup[
                            tool[
                                "id"
                            ]
                        ].get(
                            "status",
                            "not_defined"
                        )
                    ),

                    operational_status_priority(
                        operational_lookup[
                            tool[
                                "id"
                            ]
                        ][
                            "status"
                        ]
                    )
                    if compute_profile.get(
                        "enabled",
                        False
                    )
                    else
                    0,

                    score_lookup[
                        tool[
                            "id"
                        ]
                    ],

                    evidence_lookup[
                        tool[
                            "id"
                        ]
                    ]
                )

            display_tools = sorted(
                tools,
                key=_ranking_signature,
                reverse=True
            )

            # Equal rank signatures receive the same displayed rank.
            # OmicsRoute therefore does not invent a winner by alphabetical
            # order when the available evidence cannot distinguish tools.
            rank_lookup = {}

            previous_signature = None
            current_rank = 0

            for position, ranked_tool in enumerate(
                display_tools,
                start=1
            ):

                signature = (
                    _ranking_signature(
                        ranked_tool
                    )
                )

                if (
                    previous_signature
                    is None
                    or
                    signature
                    !=
                    previous_signature
                ):

                    current_rank = position
                    previous_signature = signature

                rank_lookup[
                    ranked_tool[
                        "id"
                    ]
                ] = current_rank

            for tool in display_tools:

                rank = (
                    rank_lookup[
                        tool[
                            "id"
                        ]
                    ]
                )

                displayed_score = (
                    score_lookup[
                        tool[
                            "id"
                        ]
                    ]
                )

                technical = (
                    get_tool_dependency_status(
                        step_dependency_report,
                        tool[
                            "id"
                        ]
                    )
                )

                technical_status = (
                    technical[
                        "status"
                    ]
                )

                operational = (
                    operational_lookup[
                        tool[
                            "id"
                        ]
                    ]
                )

                operational_status = (
                    operational.get(
                        "status",
                        "not_evaluated"
                    )
                )

                constraint_status = (
                    constraint_lookup[
                        tool[
                            "id"
                        ]
                    ].get(
                        "status",
                        "not_defined"
                    )
                )

                if technical_status == "runnable":

                    status_symbol = "âœ…"

                elif technical_status == "blocked":

                    status_symbol = "â›”"

                elif technical_status == "unknown":

                    status_symbol = "âš ï¸"

                else:

                    status_symbol = "â–"

                fit_display = (
                    tool.get(
                        "score",
                        {}
                    ).get(
                        "scientific_fit_display",
                        "Curated fit"
                    )
                )

                fit_suffix = (
                    f" â€¢ {fit_display}"
                )

                constraint_suffix = ""

                if constraint_status == "block":

                    constraint_suffix = (
                        " â€¢ dataset constraint: BLOCK"
                    )

                elif constraint_status == "warning":

                    constraint_suffix = (
                        " â€¢ dataset constraint: warning"
                    )

                elif constraint_status == "needs_input":

                    constraint_suffix = (
                        " â€¢ dataset constraint: needs input"
                    )

                operational_suffix = ""

                if compute_profile.get(
                    "enabled",
                    False
                ):

                    if operational_status == "good":

                        operational_suffix = (
                            " â€¢ operational fit: good"
                        )

                    elif operational_status == "warning":

                        operational_suffix = (
                            " â€¢ operational warning"
                        )

                    elif operational_status == "blocked":

                        operational_suffix = (
                            " â€¢ operationally blocked"
                        )

                    elif operational_status == "unknown":

                        operational_suffix = (
                            " â€¢ operational data incomplete"
                        )

                if technical_status == "blocked":

                    st.error(
                        f"{status_symbol} {rank}. "
                        f"{tool['name']} "
                        f"â€” {displayed_score}/100 "
                        f"(missing prerequisite artifact)"
                        f"{fit_suffix}"
                        f"{constraint_suffix}"
                        f"{operational_suffix}"
                    )

                elif (
                    compute_profile.get(
                        "enabled",
                        False
                    )
                    and
                    operational_status
                    ==
                    "blocked"
                ):

                    st.error(
                        f"â›” {rank}. "
                        f"{tool['name']} "
                        f"â€” {displayed_score}/100"
                        f"{fit_suffix}"
                        f"{constraint_suffix}"
                        f"{operational_suffix}"
                    )

                elif constraint_status == "block":

                    st.error(
                        f"â›” {rank}. "
                        f"{tool['name']} "
                        f"â€” {displayed_score}/100"
                        f"{fit_suffix}"
                        f"{constraint_suffix}"
                        f"{operational_suffix}"
                    )

                elif technical_status == "unknown":

                    st.warning(
                        f"{status_symbol} {rank}. "
                        f"{tool['name']} "
                        f"â€” {displayed_score}/100 "
                        f"(I/O metadata incomplete)"
                        f"{fit_suffix}"
                        f"{constraint_suffix}"
                        f"{operational_suffix}"
                    )

                elif constraint_status == "warning":

                    st.warning(
                        f"{'ğŸ¥‡ ' if rank == 1 else ''}"
                        f"{status_symbol} {rank}. "
                        f"{tool['name']} "
                        f"â€” {displayed_score}/100"
                        f"{fit_suffix}"
                        f"{constraint_suffix}"
                        f"{operational_suffix}"
                    )

                elif (
                    compute_profile.get(
                        "enabled",
                        False
                    )
                    and
                    operational_status
                    in (
                        "warning",
                        "unknown"
                    )
                ):

                    st.warning(
                        f"{'ğŸ¥‡ ' if rank == 1 else ''}"
                        f"{status_symbol} {rank}. "
                        f"{tool['name']} "
                        f"â€” {displayed_score}/100"
                        f"{fit_suffix}"
                        f"{constraint_suffix}"
                        f"{operational_suffix}"
                    )

                elif (
                    rank == 1
                    and
                    technical_status
                    ==
                    "runnable"
                ):

                    st.success(
                        f"ğŸ¥‡ {status_symbol} {rank}. "
                        f"{tool['name']} "
                        f"â€” {displayed_score}/100"
                        f"{fit_suffix}"
                        f"{constraint_suffix}"
                        f"{operational_suffix}"
                    )

                else:

                    st.write(
                        f"**{status_symbol} {rank}. "
                        f"{tool['name']} "
                        f"â€” {displayed_score}/100"
                        f"{fit_suffix}"
                        f"{constraint_suffix}"
                        f"{operational_suffix}**"
                    )


        show_step_recovery_guidance(
            workflow,
            step,
            display_tools,
            step_dependency_report,
            constraint_lookup,
            operational_lookup,
            compute_profile
        )
        for position, tool in enumerate(
            display_tools,
            start=1
        ):

            unique_key = (
                f"{workflow['id']}_"
                f"{number}_"
                f"{tool['id']}"
            )

            if step_mode == "parallel":

                expander_label = (
                    f"Parallel tool {position} â€” "
                    f"{tool['name']}"
                )

            else:

                expander_label = (
                    f"{position}. "
                    f"{tool['name']}"
                )

            with st.expander(
                expander_label
            ):

                if step_mode == "parallel":

                    st.metric(
                        "OmicsRoute support score",
                        f"{score_lookup[tool['id']]}/100"
                    )

                    st.caption(
                        "This score describes support for the tool; it does not "
                        "mean OmicsRoute is choosing this tool instead of the other "
                        "parallel tools."
                    )

                technical = (
                    get_tool_dependency_status(
                        step_dependency_report,
                        tool[
                            "id"
                        ]
                    )
                )

                technical_status = (
                    technical[
                        "status"
                    ]
                )

                if technical_status == "runnable":

                    if step_mode == "parallel":

                        st.success(
                            "âœ“ This parallel branch has all "
                            "technical prerequisites available"
                        )

                    else:

                        st.success(
                            "âœ“ Technical prerequisites are "
                            "available at this workflow step"
                        )

                elif technical_status == "blocked":

                    st.error(
                        "âœ— Technical prerequisite artifact is missing"
                    )

                    for artifact_id in technical.get(
                        "missing",
                        []
                    ):

                        st.write(
                            f"- Missing: "
                            f"{get_artifact_label(artifact_id)}"
                        )

                elif technical_status == "unknown":

                    st.warning(
                        "âš  Tool I/O dependency metadata is not defined "
                        "yet, so technical executability cannot be confirmed."
                    )

                else:

                    st.info(
                        "Technical status was not evaluated because an "
                        "earlier workflow dependency blocked validation."
                    )

                if tool[
                    "compatible"
                ]:

                    st.success(
                        "âœ“ Compatible with the current dataset"
                    )

                else:

                    st.error(
                        "âš  Compatibility problem"
                    )

                    for problem in tool.get(
                        "compatibility_problems",
                        []
                    ):

                        st.write(
                            f"- {problem}"
                        )

                show_strategy_fit(
                    tool
                )

                show_operational_feasibility(
                    operational_lookup[
                        tool[
                            "id"
                        ]
                    ]
                )

                show_dataset_constraint_checks(
                    workflow,
                    step,
                    number,
                    tool,
                    dataset_profile
                )

                if evidence_results:

                    evaluation = (
                        evidence_results.get(
                            tool[
                                "id"
                            ]
                        )
                    )

                    if evaluation:

                        col1, col2 = (
                            st.columns(2)
                        )

                        with col1:

                            st.metric(
                                "Recommendation score",
                                evaluation[
                                    "recommendation_score"
                                ]
                            )

                        with col2:

                            if evaluation.get(
                                "evidence_available",
                                False
                            ):

                                st.metric(
                                    "Literature support",
                                    evaluation.get(
                                        "literature_score",
                                        0
                                    )
                                )

                            else:

                                st.metric(
                                    "Literature support",
                                    "Not evaluated"
                                )

                        st.caption(
                            "The literature-support signal is shown separately "
                            "and does not numerically rewrite the OmicsRoute "
                            "recommendation score."
                        )

                show_score_details(
                    tool
                )

                st.divider()

                if tool.get(
                    "description"
                ):

                    st.write(
                        tool[
                            "description"
                        ]
                    )

                if tool.get(
                    "input"
                ):

                    st.write(
                        "**Input:**",
                        ", ".join(
                            tool[
                                "input"
                            ]
                        )
                    )

                if tool.get(
                    "output"
                ):

                    st.write(
                        "**Output:**",
                        ", ".join(
                            tool[
                                "output"
                            ]
                        )
                    )

                if tool.get(
                    "official_docs"
                ):

                    st.markdown(
                        f"**Official documentation:** "
                        f"[Open documentation]"
                        f"({tool['official_docs']})"
                    )

                if tool.get(
                    "repository"
                ):

                    st.markdown(
                        f"**Repository:** "
                        f"[Open repository]"
                        f"({tool['repository']})"
                    )

                st.divider()

                show_live_biotools_metadata(
                    tool[
                        "name"
                    ],
                    unique_key
                )

                st.divider()

                show_recent_literature(
                    tool[
                        "name"
                    ],
                    step[
                        "operation"
                    ],
                    unique_key
                )

        if number < len(
            workflow[
                "steps"
            ]
        ):

            st.markdown(
                "## â†“"
            )


    # ==================================================
    # OPTIONAL WORKFLOW-LEVEL RESEARCH
    # ==================================================
    #
    # Discovery is deliberately separated from the normal curated
    # recommendation flow. The user chooses one workflow step to
    # investigate, so Standard/Deep controls appear only once.
    #
    st.divider()

    with st.expander(
        "ğŸ” Advanced registry search for uncurated alternatives (optional)",
        expanded=False
    ):

        st.caption(
            "Core amplicon routes are curated above. Use this only when you want OmicsRoute to search beyond the "
            "curated recommendations above. Select one workflow step; "
            "discovery results do not automatically enter the official ranking."
        )

        research_step_options = list(
            range(
                len(
                    workflow[
                        "steps"
                    ]
                )
            )
        )

        selected_research_step_index = (
            st.selectbox(
                "Workflow step to research",
                research_step_options,
                format_func=lambda index: (
                    f"{index + 1}. "
                    f"{workflow['steps'][index]['name']}"
                ),
                key=(
                    f"research_step_selector_"
                    f"{workflow['id']}"
                )
            )
        )

        selected_research_step = (
            workflow[
                "steps"
            ][
                selected_research_step_index
            ]
        )

        selected_research_tools = (
            selected_research_step.get(
                "tools",
                []
            )
            or
            []
        )

        if selected_research_tools:

            show_tool_discovery(
                workflow[
                    "id"
                ],
                (
                    selected_research_step_index
                    +
                    1
                ),
                selected_research_step[
                    "operation"
                ],
                selected_research_tools,
                context=(
                    {
                        **(
                            workflow.get(
                                "context",
                                {}
                            )
                            or
                            {}
                        ),
                        **(
                            selected_research_step.get(
                                "context",
                                {}
                            )
                            or
                            {}
                        )
                    }
                )
            )

        else:

            st.info(
                "No curated candidate tools are attached to this step, "
                "so research comparison is not available here yet."
            )

    st.divider()

    show_workflow_export(
        workflow,
        dependency_validation
    )


# ==================================================
# PRODUCT FOOTER
# ==================================================

st.divider()

footer_left, footer_right = st.columns(
    [3, 1],
    vertical_alignment="center"
)

with footer_left:
    st.caption(
        "OmicsRoute â€¢ Research software release candidate. "
        "Use recommendations together with dataset requirements, reference "
        "database requirements, and the documentation of the underlying tools."
    )

with footer_right:
    st.caption(
        "[GitHub](https://github.com/isilayc/omicsroute) Â· "
        "[Live app](https://bioflow1.streamlit.app)"
    )


