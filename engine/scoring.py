# ==================================================
# BIOFLOW TOOL SCORING ENGINE v2
# ==================================================
#
# DESIGN PRINCIPLE
# ----------------
# Compatibility and operation matching are eligibility gates.
# They are NOT points.
#
# The previous BioFlow score awarded:
#   compatibility 40 + operation fit 25
# to almost every curated candidate before any scientific
# differentiation happened. This compressed most scores near 100.
#
# v2 keeps ranking transparent:
#
#   scientific suitability   60
#   maintenance              15
#   reproducibility          15
#   community support        10
#   ----------------------------
#   recommendation score    100
#
# Literature evidence is intentionally NOT blended into this score.
# It is an independent evidence-confidence signal and can be used as
# a final tie-breaker after technical validity and scientific fit.
# ==================================================


SCORE_VERSION = "2.0"
RANKING_VERSION = "3.0"


# ==================================================
# UTILITIES
# ==================================================

def normalize(value):
    """
    Normalize text values for safe comparison.
    """

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
    )


def clamp(
    value,
    minimum=0,
    maximum=100
):
    """
    Keep a numeric value inside a fixed range.
    """

    return max(
        minimum,
        min(
            maximum,
            value
        )
    )


# ==================================================
# ELIGIBILITY GATES
# ==================================================

def operation_is_supported(
    tool,
    operation
):
    """
    Return True only when the tool explicitly declares the
    workflow operation.

    Curated BioFlow content is validated separately, so missing
    operation metadata should not silently receive partial points.
    """

    operations = (
        tool.get(
            "operations",
            []
        )
        or
        []
    )

    normalized_operations = {
        normalize(
            value
        )
        for value
        in operations
    }

    return (
        normalize(
            operation
        )
        in normalized_operations
    )


def compatibility_is_supported(
    tool
):
    """
    Runtime compatibility is a gate, not a score component.
    """

    return bool(
        tool.get(
            "compatible",
            False
        )
    )


# ==================================================
# SCIENTIFIC / STRATEGY FIT
# ==================================================

FIT_POINTS = {
    "strong": 60,
    "supported": 50,
    "curated": 50,
    "conditional": 30,
    "weak": 12,
    "incompatible": 0,
    "ineligible": 0
}


FIT_PRIORITY = {
    "strong": 4,
    "supported": 3,
    "curated": 3,
    "conditional": 2,
    "weak": 1,
    "incompatible": 0,
    "ineligible": 0
}


FIT_LABELS = {
    "strong": "Strong fit",
    "supported": "Supported fit",
    "curated": "Curated fit",
    "conditional": "Conditional fit",
    "weak": "Weak fit",
    "incompatible": "Incompatible",
    "ineligible": "Ineligible"
}


def get_scientific_fit_label(
    strategy_fit=None
):
    """
    Resolve one scientific-fit label.

    Missing strategy_fit metadata does NOT mean weak evidence.
    A tool already listed as a curated candidate in workflows.yaml
    is considered a curated/supported fit unless a workflow-specific
    record explicitly upgrades or downgrades it.
    """

    if not isinstance(
        strategy_fit,
        dict
    ):

        return "curated"

    fit = normalize(
        strategy_fit.get(
            "fit"
        )
    )

    if fit in FIT_POINTS:

        return fit

    return "curated"


def score_scientific_fit(
    strategy_fit=None
):
    """
    Scientific suitability contributes up to 60 points.
    """

    label = (
        get_scientific_fit_label(
            strategy_fit
        )
    )

    return FIT_POINTS[
        label
    ]


def scientific_fit_priority(
    value
):
    """
    Ranking priority for scientific fit.

    `value` may be either a strategy-fit dictionary or a
    normalized/string fit label.
    """

    if isinstance(
        value,
        dict
    ):

        label = (
            get_scientific_fit_label(
                value
            )
        )

    else:

        label = normalize(
            value
        )

        if label not in FIT_PRIORITY:

            label = "curated"

    return FIT_PRIORITY[
        label
    ]


def scientific_fit_display_label(
    value
):
    """
    Human-readable scientific-fit label.
    """

    if isinstance(
        value,
        dict
    ):

        label = (
            get_scientific_fit_label(
                value
            )
        )

    else:

        label = normalize(
            value
        )

        if label not in FIT_LABELS:

            label = "curated"

    return FIT_LABELS[
        label
    ]


# ==================================================
# MAINTENANCE
# ==================================================

def score_maintenance(
    tool
):
    """
    Maintenance contributes up to 15 points.

    Unknown status is deliberately below active/moderate,
    but not treated as equivalent to abandonment.
    """

    status = normalize(
        tool.get(
            "maintenance",
            "unknown"
        )
    )

    values = {
        "active": 15,
        "moderate": 10,
        "legacy": 2,
        "unknown": 6
    }

    return values.get(
        status,
        6
    )


# ==================================================
# REPRODUCIBILITY / DEPLOYMENT
# ==================================================

def score_reproducibility(
    tool
):
    """
    Reproducibility/deployment contributes up to 15 points.

    Signals:
      container  5
      bioconda   4
      galaxy     3
      nf-core    3

    These signals are intentionally modest. They describe
    reproducible/accessibile deployment routes, not biological accuracy.
    """

    score = 0

    if tool.get(
        "container",
        False
    ):

        score += 5

    if tool.get(
        "bioconda",
        False
    ):

        score += 4

    if tool.get(
        "galaxy",
        False
    ):

        score += 3

    if tool.get(
        "nfcore",
        False
    ):

        score += 3

    return clamp(
        score,
        0,
        15
    )


# ==================================================
# COMMUNITY SUPPORT
# ==================================================

def score_community(
    tool
):
    """
    Community support contributes up to 10 points.

    This remains a low-weight curated signal so popularity
    cannot dominate workflow-specific scientific suitability.
    """

    level = normalize(
        tool.get(
            "community",
            "unknown"
        )
    )

    values = {
        "very_high": 10,
        "high": 8,
        "moderate": 6,
        "low": 3,
        "unknown": 5
    }

    return values.get(
        level,
        5
    )


# ==================================================
# RECOMMENDATION SCORE
# ==================================================

def calculate_tool_score(
    tool,
    operation,
    strategy_fit=None
):
    """
    Calculate BioFlow recommendation score v2.

    Eligibility gates:
      - runtime dataset compatibility
      - explicit operation support
      - strategy fit must not be "incompatible"

    Scored dimensions:
      scientific suitability   60
      maintenance              15
      reproducibility          15
      community                10
      ----------------------------
      total                   100

    Important:
      Literature evidence is NOT blended into this score.
      Operational feasibility is NOT blended into this score.
      Dependency validity is NOT blended into this score.

    Those layers are evaluated separately so a highly cited or
    easy-to-install tool cannot numerically hide a scientific mismatch.
    """

    compatibility_gate = (
        compatibility_is_supported(
            tool
        )
    )

    operation_gate = (
        operation_is_supported(
            tool,
            operation
        )
    )

    fit_label = (
        get_scientific_fit_label(
            strategy_fit
        )
    )

    strategy_gate = (
        fit_label
        !=
        "incompatible"
    )

    eligible = (
        compatibility_gate
        and
        operation_gate
        and
        strategy_gate
    )

    if eligible:

        scientific_fit = (
            score_scientific_fit(
                strategy_fit
            )
        )

        maintenance = (
            score_maintenance(
                tool
            )
        )

        reproducibility = (
            score_reproducibility(
                tool
            )
        )

        community = (
            score_community(
                tool
            )
        )

        total = (
            scientific_fit
            +
            maintenance
            +
            reproducibility
            +
            community
        )

    else:

        scientific_fit = 0
        maintenance = 0
        reproducibility = 0
        community = 0
        total = 0

        if not strategy_gate:

            fit_label = (
                "incompatible"
            )

        else:

            fit_label = (
                "ineligible"
            )

    strategy_adjusted = (
        isinstance(
            strategy_fit,
            dict
        )
        and
        bool(
            strategy_fit.get(
                "fit"
            )
        )
    )

    return {
        "version": SCORE_VERSION,
        "total": clamp(
            total,
            0,
            100
        ),
        "eligible": eligible,
        "compatibility_gate": compatibility_gate,
        "operation_gate": operation_gate,
        "strategy_gate": strategy_gate,
        "scientific_fit": scientific_fit,
        "scientific_fit_max": 60,
        "scientific_fit_label": fit_label,
        "scientific_fit_display": (
            scientific_fit_display_label(
                fit_label
            )
        ),
        "scientific_fit_priority": (
            scientific_fit_priority(
                fit_label
            )
        ),
        "maintenance": maintenance,
        "maintenance_max": 15,
        "reproducibility": reproducibility,
        "reproducibility_max": 15,
        "community": community,
        "community_max": 10,

        # Backward-compatible fields used by older UI code.
        # They are gates now, not point contributions.
        "compatibility": (
            1
            if compatibility_gate
            else
            0
        ),
        "workflow_fit": (
            1
            if operation_gate
            else
            0
        ),
        "base_total": clamp(
            total,
            0,
            100
        ),
        "strategy_fit": (
            scientific_fit
            if strategy_adjusted
            else
            None
        ),
        "strategy_fit_label": (
            strategy_fit.get(
                "fit"
            )
            if isinstance(
                strategy_fit,
                dict
            )
            else
            None
        ),
        "strategy_adjusted": strategy_adjusted
    }


# ==================================================
# RANKING HELPERS
# ==================================================

def operational_hard_gate_priority(
    operational_status,
    enabled=False
):
    """
    Operational `blocked` is a hard practical gate only when
    the user explicitly enables the compute profile.

    Warnings/unknowns are not allowed to outrank scientific fit.
    """

    if not enabled:

        return 1

    status = normalize(
        operational_status
    )

    if status == "blocked":

        return 0

    return 1


def constraint_hard_gate_priority(
    constraint_status
):
    """
    Dataset-specific BLOCK is a hard ranking gate.

    Missing information is deliberately neutral: BioFlow must not
    demote a tool merely because the user has not supplied an optional
    profile value yet.
    """

    status = normalize(
        constraint_status
    )

    if status == "block":

        return 0

    return 1


def constraint_soft_priority(
    constraint_status
):
    """
    Soft dataset-constraint priority used *after* scientific fit.

    warning      -> 0  (soft demotion inside the same fit tier)
    pass         -> 1
    needs_input  -> 1  (neutral, not evidence of a mismatch)
    not_defined  -> 1  (neutral, avoids rewarding constraint coverage)

    A BLOCK is handled separately by constraint_hard_gate_priority().
    """

    status = normalize(
        constraint_status
    )

    if status == "warning":

        return 0

    return 1


def recommendation_sort_key(
    tool,
    operational_status=None,
    operational_enabled=False,
    evidence_score=None,
    constraint_status=None
):
    """
    Ranking key inside an already technically valid workflow step.

    Ranking v3 order:
      1. operational hard block
      2. dataset-specific hard block
      3. scientific fit tier
      4. dataset-specific warning (soft signal)
      5. operational fit (if enabled)
      6. stable BioFlow recommendation score
      7. literature evidence signal (tie-breaker only)

    Missing constraint input and tools without constraint definitions are
    neutral. This prevents incomplete metadata coverage from creating a
    false ranking advantage or penalty.

    This helper deliberately excludes dependency status because
    dependency information is owned by engine.dependencies / app.py.
    """

    score = (
        tool.get(
            "score",
            {}
        )
        or
        {}
    )

    fit_priority = (
        score.get(
            "scientific_fit_priority"
        )
    )

    if fit_priority is None:

        fit_priority = (
            scientific_fit_priority(
                score.get(
                    "scientific_fit_label",
                    "curated"
                )
            )
        )

    operational_priority = 0

    if operational_enabled:

        # Avoid importing feasibility here to keep scoring.py independent.
        # app.py/recommender.py can prepend their own operational status
        # priority if they need the full ordering.
        status = normalize(
            operational_status
        )

        operational_priority = {
            "good": 3,
            "warning": 2,
            "unknown": 1,
            "not_evaluated": 1,
            "blocked": 0
        }.get(
            status,
            1
        )

    if evidence_score is None:

        evidence_value = -1

    else:

        try:

            evidence_value = float(
                evidence_score
            )

        except (
            TypeError,
            ValueError
        ):

            evidence_value = -1

    return (
        operational_hard_gate_priority(
            operational_status,
            enabled=operational_enabled
        ),
        constraint_hard_gate_priority(
            constraint_status
        ),
        fit_priority,
        constraint_soft_priority(
            constraint_status
        ),
        operational_priority,
        score.get(
            "total",
            0
        ),
        evidence_value
    )
