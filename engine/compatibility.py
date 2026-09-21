# ==================================================
# BIOFLOW TOOL COMPATIBILITY ENGINE
# ==================================================


def normalize(value):
    """
    Normalize a single text value.
    """

    if value is None:
        return ""

    return str(value).strip().lower()


def normalize_selection(value):
    """
    Convert either a single value or multiple
    selected values into a normalized list.

    Example:

    "Illumina"
        -> ["illumina"]

    ["Illumina", "Oxford Nanopore"]
        -> ["illumina", "oxford nanopore"]
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

        return [
            normalize(item)
            for item in value
            if item is not None
        ]

    return [
        normalize(value)
    ]


def supports_value(
    tool,
    field_name,
    selected_value
):
    """
    Check whether a tool supports the selected
    context value or values.

    In hybrid workflows, all selected technologies
    must be supported by the tool unless the tool
    declares support for Any.
    """

    supported_values = (
        tool.get(
            field_name
        )
    )

    # Missing metadata means no explicit restriction.
    if not supported_values:
        return True

    normalized_supported = [
        normalize(value)
        for value in supported_values
    ]

    if (
        "any"
        in normalized_supported
        or
        "*"
        in normalized_supported
    ):
        return True

    selected_values = (
        normalize_selection(
            selected_value
        )
    )

    if not selected_values:
        return True

    return all(
        value in normalized_supported
        for value in selected_values
    )


def check_tool_compatibility(
    tool,
    sample_type,
    sequencing,
    read_type
):
    """
    Check BioFlow tool compatibility.

    sequencing and read_type can now be either:

    string

    or

    list of strings
    """

    problems = []

    if not supports_value(
        tool,
        "sample_types",
        sample_type
    ):

        problems.append(
            f"Sample type not supported: "
            f"{sample_type}"
        )

    if not supports_value(
        tool,
        "sequencing",
        sequencing
    ):

        problems.append(
            f"Sequencing technology not supported: "
            f"{sequencing}"
        )

    if not supports_value(
        tool,
        "read_types",
        read_type
    ):

        problems.append(
            f"Read type not supported: "
            f"{read_type}"
        )

    return {
        "compatible": (
            len(problems)
            == 0
        ),

        "problems": problems
    }