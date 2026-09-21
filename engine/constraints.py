from pathlib import Path


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

CONSTRAINTS_FILE = (
    DATA_DIR
    / "constraints.yaml"
)


# ==================================================
# SIMPLE MTIME-AWARE CACHE
# ==================================================

_CONSTRAINT_CACHE = {
    "mtime_ns": None,
    "data": None
}


# ==================================================
# YAML LOADING
# ==================================================

def load_constraints():
    """
    Load constraints.yaml.

    The file is only parsed again when its modification
    time changes.
    """

    if not CONSTRAINTS_FILE.exists():

        return {
            "schema_version": 1,
            "tools": {},
            "workflow_constraints": {}
        }

    mtime_ns = (
        CONSTRAINTS_FILE
        .stat()
        .st_mtime_ns
    )

    if (
        _CONSTRAINT_CACHE["data"] is not None
        and
        _CONSTRAINT_CACHE["mtime_ns"] == mtime_ns
    ):

        return (
            _CONSTRAINT_CACHE["data"]
        )

    with open(
        CONSTRAINTS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        data = (
            yaml.safe_load(
                file
            )
            or
            {}
        )

    if not isinstance(
        data,
        dict
    ):

        data = {}

    data.setdefault(
        "schema_version",
        1
    )

    data.setdefault(
        "tools",
        {}
    )

    data.setdefault(
        "workflow_constraints",
        {}
    )

    _CONSTRAINT_CACHE[
        "mtime_ns"
    ] = mtime_ns

    _CONSTRAINT_CACHE[
        "data"
    ] = data

    return data


# ==================================================
# TOOL ACCESS
# ==================================================

def get_tool_constraint_definition(
    tool_id
):
    """
    Return the declarative constraint definition for
    one tool.
    """

    data = (
        load_constraints()
    )

    tools = (
        data.get(
            "tools",
            {}
        )
    )

    definition = (
        tools.get(
            tool_id
        )
    )

    if not isinstance(
        definition,
        dict
    ):

        return None

    return definition


def get_profile_field_definitions(
    tool_id
):
    """
    Return dataset/profile fields requested by a tool.

    These definitions can later be used by Streamlit
    to construct dynamic parameter-input widgets.
    """

    definition = (
        get_tool_constraint_definition(
            tool_id
        )
    )

    if not definition:

        return {}

    fields = (
        definition.get(
            "fields",
            {}
        )
    )

    if not isinstance(
        fields,
        dict
    ):

        return {}

    return fields


def get_workflow_constraint_definition(
    workflow_id
):
    """
    Return the declarative constraint definition for
    one workflow strategy.
    """

    data = (
        load_constraints()
    )

    workflows = (
        data.get(
            "workflow_constraints",
            {}
        )
    )

    definition = (
        workflows.get(
            workflow_id
        )
    )

    if not isinstance(
        definition,
        dict
    ):

        return None

    return definition


def get_workflow_profile_field_definitions(
    workflow_id
):
    """
    Return dataset/profile fields requested by a
    workflow-level constraint definition.
    """

    definition = (
        get_workflow_constraint_definition(
            workflow_id
        )
    )

    if not definition:

        return {}

    fields = (
        definition.get(
            "fields",
            {}
        )
    )

    if not isinstance(
        fields,
        dict
    ):

        return {}

    return fields


# ==================================================
# UTILITIES
# ==================================================

def as_list(
    value
):
    """
    Convert scalar/list-like values into a list.
    """

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


def _condition_matches(
    profile,
    conditions
):
    """
    Evaluate a simple declarative 'when' block.

    Example:

    when:
      read_type: Paired-end

    List values are also supported:

    when:
      sequencing:
        - Illumina
        - PacBio
    """

    if not conditions:

        return True

    if not isinstance(
        conditions,
        dict
    ):

        return True

    for (
        field,
        expected
    ) in conditions.items():

        actual = (
            profile.get(
                field
            )
        )

        expected_values = (
            as_list(
                expected
            )
        )

        if actual not in expected_values:

            return False

    return True


def _to_number(
    value
):
    """
    Convert a value to float when possible.
    """

    if isinstance(
        value,
        bool
    ):

        return None

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return None


def _missing_result(
    rule,
    missing_fields
):
    """
    Build a standard result for missing profile data.
    """

    message = (
        rule.get(
            "missing_message"
        )
        or
        (
            "Additional dataset information is "
            "required to evaluate this constraint."
        )
    )

    return {
        "id": (
            rule.get(
                "id"
            )
        ),

        "kind": (
            rule.get(
                "kind"
            )
        ),

        "status": "needs_input",

        "message": message,

        "missing_fields": (
            missing_fields
        ),

        "observed": None,

        "expected": None
    }


def _pass_result(
    rule,
    observed=None,
    expected=None
):
    """
    Build a standard passing rule result.
    """

    message = (
        rule.get(
            "pass_message"
        )
        or
        "Constraint satisfied."
    )

    return {
        "id": (
            rule.get(
                "id"
            )
        ),

        "kind": (
            rule.get(
                "kind"
            )
        ),

        "status": "pass",

        "message": message,

        "missing_fields": [],

        "observed": observed,

        "expected": expected
    }


def _fail_result(
    rule,
    observed=None,
    expected=None
):
    """
    Build a standard failed rule result.

    severity:
      warning -> warning
      block   -> block
    """

    severity = (
        rule.get(
            "severity",
            "warning"
        )
    )

    if severity not in (
        "warning",
        "block"
    ):

        severity = "warning"

    message = (
        rule.get(
            "fail_message"
        )
        or
        "Constraint was not satisfied."
    )

    return {
        "id": (
            rule.get(
                "id"
            )
        ),

        "kind": (
            rule.get(
                "kind"
            )
        ),

        "status": severity,

        "message": message,

        "missing_fields": [],

        "observed": observed,

        "expected": expected
    }


# ==================================================
# RULE EVALUATION
# ==================================================

def evaluate_rule(
    rule,
    profile
):
    """
    Evaluate one declarative constraint rule.

    Supported kinds:

      required
      equals
      numeric_min
      numeric_max
      one_of
      value_mapping
      sum_minus_min
    """

    if not isinstance(
        rule,
        dict
    ):

        return None

    if not _condition_matches(
        profile,
        rule.get(
            "when"
        )
    ):

        return {
            "id": (
                rule.get(
                    "id"
                )
            ),

            "kind": (
                rule.get(
                    "kind"
                )
            ),

            "status": "not_applicable",

            "message": (
                "Constraint does not apply "
                "to the current dataset context."
            ),

            "missing_fields": [],

            "observed": None,

            "expected": None
        }

    kind = (
        rule.get(
            "kind"
        )
    )

    # ----------------------------------------------
    # REQUIRED
    # ----------------------------------------------

    if kind == "required":

        fields = (
            as_list(
                rule.get(
                    "fields"
                )
            )
        )

        if not fields:

            field = (
                rule.get(
                    "field"
                )
            )

            if field:

                fields = [
                    field
                ]

        missing = [
            field
            for field in fields
            if (
                field not in profile
                or
                profile.get(
                    field
                ) is None
                or
                profile.get(
                    field
                ) == ""
            )
        ]

        if missing:

            return (
                _missing_result(
                    rule,
                    missing
                )
            )

        return (
            _pass_result(
                rule
            )
        )

    # ----------------------------------------------
    # EQUALS
    # ----------------------------------------------

    if kind == "equals":

        field = (
            rule.get(
                "field"
            )
        )

        if (
            field not in profile
            or
            profile.get(
                field
            ) is None
        ):

            return (
                _missing_result(
                    rule,
                    [
                        field
                    ]
                )
            )

        actual = (
            profile.get(
                field
            )
        )

        expected = (
            rule.get(
                "expected"
            )
        )

        if actual == expected:

            return (
                _pass_result(
                    rule,
                    observed=actual,
                    expected=expected
                )
            )

        return (
            _fail_result(
                rule,
                observed=actual,
                expected=expected
            )
        )

    # ----------------------------------------------
    # NUMERIC MINIMUM
    # ----------------------------------------------

    if kind == "numeric_min":

        field = (
            rule.get(
                "field"
            )
        )

        if (
            field not in profile
            or
            profile.get(
                field
            ) is None
        ):

            return (
                _missing_result(
                    rule,
                    [
                        field
                    ]
                )
            )

        actual = (
            _to_number(
                profile.get(
                    field
                )
            )
        )

        minimum = (
            _to_number(
                rule.get(
                    "min_value"
                )
            )
        )

        if (
            actual is None
            or
            minimum is None
        ):

            return (
                _fail_result(
                    rule,
                    observed=(
                        profile.get(
                            field
                        )
                    ),
                    expected=(
                        rule.get(
                            "min_value"
                        )
                    )
                )
            )

        if actual >= minimum:

            return (
                _pass_result(
                    rule,
                    observed=actual,
                    expected=minimum
                )
            )

        return (
            _fail_result(
                rule,
                observed=actual,
                expected=minimum
            )
        )

    # ----------------------------------------------
    # NUMERIC MAXIMUM
    # ----------------------------------------------

    if kind == "numeric_max":

        field = (
            rule.get(
                "field"
            )
        )

        if (
            field not in profile
            or
            profile.get(
                field
            ) is None
        ):

            return (
                _missing_result(
                    rule,
                    [
                        field
                    ]
                )
            )

        actual = (
            _to_number(
                profile.get(
                    field
                )
            )
        )

        maximum = (
            _to_number(
                rule.get(
                    "max_value"
                )
            )
        )

        if (
            actual is None
            or
            maximum is None
        ):

            return (
                _fail_result(
                    rule,
                    observed=(
                        profile.get(
                            field
                        )
                    ),
                    expected=(
                        rule.get(
                            "max_value"
                        )
                    )
                )
            )

        if actual <= maximum:

            return (
                _pass_result(
                    rule,
                    observed=actual,
                    expected=maximum
                )
            )

        return (
            _fail_result(
                rule,
                observed=actual,
                expected=maximum
            )
        )

    # ----------------------------------------------
    # ONE OF
    # ----------------------------------------------

    if kind == "one_of":

        field = (
            rule.get(
                "field"
            )
        )

        if (
            field not in profile
            or
            profile.get(
                field
            ) is None
        ):

            return (
                _missing_result(
                    rule,
                    [
                        field
                    ]
                )
            )

        actual = (
            profile.get(
                field
            )
        )

        allowed = (
            as_list(
                rule.get(
                    "allowed"
                )
            )
        )

        if actual in allowed:

            return (
                _pass_result(
                    rule,
                    observed=actual,
                    expected=allowed
                )
            )

        return (
            _fail_result(
                rule,
                observed=actual,
                expected=allowed
            )
        )

    # ----------------------------------------------
    # VALUE MAPPING
    # ----------------------------------------------

    if kind == "value_mapping":

        source_field = (
            rule.get(
                "source_field"
            )
        )

        target_field = (
            rule.get(
                "target_field"
            )
        )

        required_fields = [
            field
            for field in (
                source_field,
                target_field
            )
            if field
        ]

        missing = [
            field
            for field in required_fields
            if (
                field not in profile
                or
                profile.get(
                    field
                ) is None
                or
                profile.get(
                    field
                ) == ""
            )
        ]

        if missing:

            return (
                _missing_result(
                    rule,
                    missing
                )
            )

        if (
            not source_field
            or
            not target_field
        ):

            return {
                "id": (
                    rule.get(
                        "id"
                    )
                ),

                "kind": kind,

                "status": "unknown_rule",

                "message": (
                    "value_mapping requires both "
                    "source_field and target_field."
                ),

                "missing_fields": [],

                "observed": None,

                "expected": None
            }

        mapping = (
            rule.get(
                "mapping",
                rule.get(
                    "allowed_pairs",
                    {}
                )
            )
        )

        if not isinstance(
            mapping,
            dict
        ):

            return {
                "id": (
                    rule.get(
                        "id"
                    )
                ),

                "kind": kind,

                "status": "unknown_rule",

                "message": (
                    "value_mapping requires a mapping "
                    "dictionary."
                ),

                "missing_fields": [],

                "observed": None,

                "expected": None
            }

        source_value = (
            profile.get(
                source_field
            )
        )

        target_value = (
            profile.get(
                target_field
            )
        )

        if source_value not in mapping:

            return {
                "id": (
                    rule.get(
                        "id"
                    )
                ),

                "kind": kind,

                "status": "unknown_rule",

                "message": (
                    f"No value mapping is defined for "
                    f"{source_field}={source_value!r}."
                ),

                "missing_fields": [],

                "observed": {
                    source_field: source_value,
                    target_field: target_value
                },

                "expected": None
            }

        allowed_targets = (
            as_list(
                mapping.get(
                    source_value
                )
            )
        )

        observed = {
            source_field: source_value,
            target_field: target_value
        }

        expected = {
            source_field: source_value,
            "allowed_targets": allowed_targets
        }

        if target_value in allowed_targets:

            return (
                _pass_result(
                    rule,
                    observed=observed,
                    expected=expected
                )
            )

        return (
            _fail_result(
                rule,
                observed=observed,
                expected=expected
            )
        )

    # ----------------------------------------------
    # SUM MINUS FIELD >= MINIMUM
    # ----------------------------------------------

    if kind == "sum_minus_min":

        fields = (
            as_list(
                rule.get(
                    "fields"
                )
            )
        )

        subtract_field = (
            rule.get(
                "subtract_field"
            )
        )

        required_fields = (
            fields
            +
            (
                [
                    subtract_field
                ]
                if subtract_field
                else
                []
            )
        )

        missing = [
            field
            for field in required_fields
            if (
                field not in profile
                or
                profile.get(
                    field
                ) is None
            )
        ]

        if missing:

            return (
                _missing_result(
                    rule,
                    missing
                )
            )

        numeric_values = [
            _to_number(
                profile.get(
                    field
                )
            )
            for field in fields
        ]

        subtract_value = (
            _to_number(
                profile.get(
                    subtract_field
                )
            )
        )

        minimum = (
            _to_number(
                rule.get(
                    "min_value"
                )
            )
        )

        if (
            any(
                value is None
                for value in numeric_values
            )
            or
            subtract_value is None
            or
            minimum is None
        ):

            return (
                _fail_result(
                    rule
                )
            )

        observed = (
            sum(
                numeric_values
            )
            -
            subtract_value
        )

        if observed >= minimum:

            return (
                _pass_result(
                    rule,
                    observed=observed,
                    expected=minimum
                )
            )

        return (
            _fail_result(
                rule,
                observed=observed,
                expected=minimum
            )
        )

    # ----------------------------------------------
    # UNKNOWN RULE TYPE
    # ----------------------------------------------

    return {
        "id": (
            rule.get(
                "id"
            )
        ),

        "kind": kind,

        "status": "unknown_rule",

        "message": (
            f"Unsupported constraint rule type: "
            f"{kind}"
        ),

        "missing_fields": [],

        "observed": None,

        "expected": None
    }


# ==================================================
# CONSTRAINT DEFINITION EVALUATION
# ==================================================

def _evaluate_constraint_definition(
    subject_id,
    definition,
    profile,
    subject_type
):
    """
    Evaluate all rules in one tool- or workflow-level
    constraint definition.
    """

    if definition is None:

        return {
            f"{subject_type}_id": subject_id,
            "subject_type": subject_type,
            "status": "not_defined",
            "checks": [],
            "counts": {
                "pass": 0,
                "warning": 0,
                "block": 0,
                "needs_input": 0,
                "unknown_rule": 0
            },
            "fields": {}
        }

    rules = (
        definition.get(
            "rules",
            []
        )
    )

    checks = []

    for rule in rules:

        result = (
            evaluate_rule(
                rule,
                profile
            )
        )

        if result is not None:

            checks.append(
                result
            )

    counts = {
        "pass": 0,
        "warning": 0,
        "block": 0,
        "needs_input": 0,
        "unknown_rule": 0
    }

    for check in checks:

        status = (
            check.get(
                "status"
            )
        )

        if status in counts:

            counts[
                status
            ] += 1

    if counts["block"] > 0:

        overall_status = "block"

    elif counts["warning"] > 0:

        overall_status = "warning"

    elif counts["needs_input"] > 0:

        overall_status = "needs_input"

    elif counts["unknown_rule"] > 0:

        overall_status = "warning"

    else:

        overall_status = "pass"

    fields = (
        definition.get(
            "fields",
            {}
        )
    )

    if not isinstance(
        fields,
        dict
    ):

        fields = {}

    return {
        f"{subject_type}_id": subject_id,
        "subject_type": subject_type,
        "status": overall_status,
        "checks": checks,
        "counts": counts,
        "fields": fields
    }


# ==================================================
# TOOL CONSTRAINT EVALUATION
# ==================================================

def evaluate_tool_constraints(
    tool_id,
    profile
):
    """
    Evaluate all known dataset/parameter constraints
    for one tool.
    """

    definition = (
        get_tool_constraint_definition(
            tool_id
        )
    )

    return (
        _evaluate_constraint_definition(
            subject_id=tool_id,
            definition=definition,
            profile=profile,
            subject_type="tool"
        )
    )


# ==================================================
# WORKFLOW CONSTRAINT EVALUATION
# ==================================================

def evaluate_workflow_constraints(
    workflow_id,
    profile
):
    """
    Evaluate dataset-level constraints that belong to
    the workflow strategy itself rather than to one tool.

    Examples:
      - number of genomes in a pangenome analysis
      - number of taxa in phylogenomics
      - biological replicate structure
      - co-assembly sample count
    """

    definition = (
        get_workflow_constraint_definition(
            workflow_id
        )
    )

    return (
        _evaluate_constraint_definition(
            subject_id=workflow_id,
            definition=definition,
            profile=profile,
            subject_type="workflow"
        )
    )


# ==================================================
# TERMINAL REPORT
# ==================================================

def print_constraint_report(
    report
):
    """
    Print a human-readable terminal report.
    """

    print()
    print(
        "=" * 70
    )

    subject_id = (
        report.get(
            "tool_id"
        )
        or
        report.get(
            "workflow_id"
        )
    )

    print(
        f"Constraint evaluation: "
        f"{subject_id}"
    )

    print(
        "=" * 70
    )

    print(
        f"Overall status: "
        f"{report.get('status')}"
    )

    print()

    symbols = {
        "pass": "[PASS]",
        "warning": "[WARN]",
        "block": "[BLOCK]",
        "needs_input": "[INPUT]",
        "not_applicable": "[SKIP]",
        "unknown_rule": "[UNKNOWN]"
    }

    for check in report.get(
        "checks",
        []
    ):

        status = (
            check.get(
                "status"
            )
        )

        symbol = (
            symbols.get(
                status,
                "[?]"
            )
        )

        print(
            f"{symbol} "
            f"{check.get('id')}"
        )

        message = (
            check.get(
                "message"
            )
        )

        if message:

            print(
                f"    {message}"
            )

        if check.get(
            "observed"
        ) is not None:

            print(
                f"    observed: "
                f"{check.get('observed')}"
            )

        if check.get(
            "expected"
        ) is not None:

            print(
                f"    expected: "
                f"{check.get('expected')}"
            )

        for field in check.get(
            "missing_fields",
            []
        ):

            print(
                f"    missing input: "
                f"{field}"
            )

    print()