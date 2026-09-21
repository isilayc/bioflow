import requests


BASE_URL = "https://bio.tools/api/tool/"


# ==================================================
# BASIC UTILITIES
# ==================================================

def unique_values(values):
    """
    Remove duplicate text values while preserving order.
    """

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


def normalize_tool_name(value):
    """
    Normalize a tool/resource name for cross-query deduplication.
    """

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
        .replace(".", "")
    )


def _get_term(value):
    """
    bio.tools frequently stores ontology labels as
    dictionaries with a `term` field.
    """

    if isinstance(
        value,
        dict
    ):

        return (
            value.get(
                "term"
            )
            or
            value.get(
                "label"
            )
            or
            value.get(
                "name"
            )
        )

    if value is None:
        return None

    return str(
        value
    )


# ==================================================
# METADATA EXTRACTION
# ==================================================

def extract_operations(record):
    """
    Extract registered EDAM operation terms.
    """

    operations = []

    for function in record.get(
        "function",
        []
    ) or []:

        for operation in function.get(
            "operation",
            []
        ) or []:

            term = _get_term(
                operation
            )

            if term:
                operations.append(
                    term
                )

    return unique_values(
        operations
    )


def extract_topics(record):
    """
    Extract registered bio.tools / EDAM topics.
    """

    topics = []

    for topic in record.get(
        "topic",
        []
    ) or []:

        term = _get_term(
            topic
        )

        if term:
            topics.append(
                term
            )

    return unique_values(
        topics
    )


def extract_input_metadata(record):
    """
    Extract input data types and input formats.
    """

    input_data = []
    input_formats = []

    for function in record.get(
        "function",
        []
    ) or []:

        for item in function.get(
            "input",
            []
        ) or []:

            data_object = (
                item.get(
                    "data",
                    {}
                )
                or
                {}
            )

            data_term = _get_term(
                data_object
            )

            if data_term:
                input_data.append(
                    data_term
                )

            for format_object in item.get(
                "format",
                []
            ) or []:

                format_term = _get_term(
                    format_object
                )

                if format_term:
                    input_formats.append(
                        format_term
                    )

    return (
        unique_values(
            input_data
        ),
        unique_values(
            input_formats
        )
    )


def extract_output_metadata(record):
    """
    Extract output data types and formats.
    """

    output_data = []
    output_formats = []

    for function in record.get(
        "function",
        []
    ) or []:

        for item in function.get(
            "output",
            []
        ) or []:

            data_object = (
                item.get(
                    "data",
                    {}
                )
                or
                {}
            )

            data_term = _get_term(
                data_object
            )

            if data_term:
                output_data.append(
                    data_term
                )

            for format_object in item.get(
                "format",
                []
            ) or []:

                format_term = _get_term(
                    format_object
                )

                if format_term:
                    output_formats.append(
                        format_term
                    )

    return (
        unique_values(
            output_data
        ),
        unique_values(
            output_formats
        )
    )


def extract_publications(record):
    """
    Preserve publication identifiers registered in bio.tools.
    """

    publications = []

    for publication in record.get(
        "publication",
        []
    ) or []:

        if not isinstance(
            publication,
            dict
        ):
            continue

        publications.append(
            {
                "doi": publication.get(
                    "doi"
                ),
                "pmid": publication.get(
                    "pmid"
                ),
                "pmcid": publication.get(
                    "pmcid"
                ),
                "type": publication.get(
                    "type"
                )
            }
        )

    return publications


def extract_tool_types(record):
    """
    Extract bio.tools resource/application types.

    Depending on registry vintage these may be strings or objects.
    """

    values = []

    for item in record.get(
        "toolType",
        []
    ) or []:

        term = _get_term(
            item
        )

        if term:
            values.append(
                term
            )

    return unique_values(
        values
    )


def extract_operating_systems(record):
    """
    Extract operating-system metadata when present.
    """

    values = []

    for item in record.get(
        "operatingSystem",
        []
    ) or []:

        term = _get_term(
            item
        )

        if term:
            values.append(
                term
            )

    return unique_values(
        values
    )


def extract_languages(record):
    """
    Extract implementation-language metadata when present.
    """

    values = []

    for item in record.get(
        "language",
        []
    ) or []:

        term = _get_term(
            item
        )

        if term:
            values.append(
                term
            )

    return unique_values(
        values
    )


def extract_links(record):
    """
    Preserve selected external links for provenance/review.
    """

    links = []

    for item in record.get(
        "link",
        []
    ) or []:

        if isinstance(
            item,
            dict
        ):

            url = item.get(
                "url"
            )

            link_type = item.get(
                "type"
            )

            if url:

                links.append(
                    {
                        "url": url,
                        "type": link_type
                    }
                )

    return links


# ==================================================
# RECORD SIMPLIFICATION
# ==================================================

def simplify_discovery_record(
    record,
    matched_query=None
):
    """
    Simplify a bio.tools result while preserving metadata
    required by BioFlow discovery screening.
    """

    if not record:
        return None

    name = record.get(
        "name"
    )

    if not name:
        return None

    biotools_id = record.get(
        "biotoolsID"
    )

    (
        input_data,
        input_formats
    ) = extract_input_metadata(
        record
    )

    (
        output_data,
        output_formats
    ) = extract_output_metadata(
        record
    )

    publications = extract_publications(
        record
    )

    query_matches = []

    if matched_query:

        query_matches.append(
            matched_query
        )

    return {
        "name": name,
        "biotools_id": biotools_id,
        "description": record.get(
            "description"
        ),
        "homepage": record.get(
            "homepage"
        ),
        "operations": extract_operations(
            record
        ),
        "topics": extract_topics(
            record
        ),
        "input_data": input_data,
        "input_formats": input_formats,
        "output_data": output_data,
        "output_formats": output_formats,
        "publication_count": len(
            publications
        ),
        "publications": publications,
        "resource_types": extract_tool_types(
            record
        ),
        "operating_systems": extract_operating_systems(
            record
        ),
        "languages": extract_languages(
            record
        ),
        "links": extract_links(
            record
        ),
        "biotools_url": (
            f"https://bio.tools/{biotools_id}"
            if biotools_id
            else None
        ),
        "discovery_sources": [
            "bio.tools"
        ],
        "query_matches": query_matches,
        "source_provenance": [
            {
                "source": "bio.tools",
                "query": matched_query,
                "url": (
                    f"https://bio.tools/{biotools_id}"
                    if biotools_id
                    else None
                )
            }
        ]
    }


def simplify_biotools_record(
    record
):
    """
    Convert a full bio.tools record into the fields
    used by BioFlow's curated tool card.
    """

    item = simplify_discovery_record(
        record
    )

    if item is None:
        return None

    return {
        "name": item.get(
            "name"
        ),
        "biotools_id": item.get(
            "biotools_id"
        ),
        "description": item.get(
            "description"
        ),
        "homepage": item.get(
            "homepage"
        ),
        "biotools_url": item.get(
            "biotools_url"
        ),
        "operations": item.get(
            "operations",
            []
        ),
        "topics": item.get(
            "topics",
            []
        ),
        "input_data": item.get(
            "input_data",
            []
        ),
        "input_formats": item.get(
            "input_formats",
            []
        ),
        "output_data": item.get(
            "output_data",
            []
        ),
        "output_formats": item.get(
            "output_formats",
            []
        ),
        "resource_types": item.get(
            "resource_types",
            []
        ),
        "operating_systems": item.get(
            "operating_systems",
            []
        ),
        "languages": item.get(
            "languages",
            []
        ),
        "publications": item.get(
            "publications",
            []
        )
    }


# ==================================================
# BASIC TOOL SEARCH
# ==================================================

def search_biotools(
    tool_name
):
    """
    Search bio.tools for a specific tool/resource by name.
    """

    try:

        response = requests.get(
            BASE_URL,
            params={
                "q": tool_name,
                "format": "json",
                "per_page": 15,
                "sort": "score",
                "ord": "desc"
            },
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "list",
            []
        ) or []

        if not results:
            return None

        requested = normalize_tool_name(
            tool_name
        )

        for record in results:

            if (
                normalize_tool_name(
                    record.get(
                        "name"
                    )
                )
                ==
                requested
            ):

                return record

        return results[0]

    except (
        requests.RequestException,
        ValueError
    ):

        return None


# ==================================================
# SINGLE-QUERY DISCOVERY
# ==================================================

def search_biotools_by_operation(
    search_term,
    limit=20
):
    """
    Backward-compatible single-query discovery.
    """

    try:

        response = requests.get(
            BASE_URL,
            params={
                "q": search_term,
                "format": "json",
                "per_page": min(
                    max(
                        int(limit),
                        1
                    ),
                    100
                ),
                "sort": "score",
                "ord": "desc"
            },
            timeout=25
        )

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "list",
            []
        ) or []

        simplified = []

        for record in results:

            item = simplify_discovery_record(
                record,
                matched_query=search_term
            )

            if item is not None:

                simplified.append(
                    item
                )

        return {
            "query": search_term,
            "queries": [
                search_term
            ],
            "results": simplified,
            "raw_count": data.get(
                "count",
                len(results)
            ),
            "error": None
        }

    except requests.RequestException as error:

        return {
            "query": search_term,
            "queries": [
                search_term
            ],
            "results": [],
            "raw_count": 0,
            "error": (
                "bio.tools connection error: "
                f"{error}"
            )
        }

    except ValueError as error:

        return {
            "query": search_term,
            "queries": [
                search_term
            ],
            "results": [],
            "raw_count": 0,
            "error": (
                "bio.tools JSON error: "
                f"{error}"
            )
        }


# ==================================================
# MULTI-QUERY DISCOVERY
# ==================================================

def _merge_discovery_item(
    existing,
    incoming
):
    """
    Merge repeated bio.tools hits returned by different queries.
    """

    merged = existing.copy()

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

        merged[
            field
        ] = unique_values(
            (
                existing.get(
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

    existing_provenance = (
        existing.get(
            "source_provenance",
            []
        )
        or
        []
    )

    incoming_provenance = (
        incoming.get(
            "source_provenance",
            []
        )
        or
        []
    )

    seen_provenance = set()
    provenance = []

    for item in (
        existing_provenance
        +
        incoming_provenance
    ):

        if not isinstance(
            item,
            dict
        ):
            continue

        key = (
            item.get(
                "source"
            ),
            item.get(
                "query"
            ),
            item.get(
                "url"
            )
        )

        if key in seen_provenance:
            continue

        seen_provenance.add(
            key
        )

        provenance.append(
            item
        )

    merged[
        "source_provenance"
    ] = provenance

    merged[
        "publication_count"
    ] = max(
        existing.get(
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

    for field in [
        "description",
        "homepage",
        "biotools_url",
        "biotools_id"
    ]:

        if not merged.get(
            field
        ) and incoming.get(
            field
        ):

            merged[
                field
            ] = incoming[
                field
            ]

    return merged


def search_biotools_queries(
    query_terms,
    per_query=20,
    max_total=100
):
    """
    Search bio.tools with a family of complementary queries.

    This is intentionally different from the original BioFlow
    discovery mode, which relied on one manually mapped query.
    Multiple queries reduce the chance of missing tools,
    frameworks and web applications described with different
    terminology.
    """

    queries = unique_values(
        query_terms
    )

    if not queries:

        return {
            "query": "",
            "queries": [],
            "results": [],
            "raw_count": 0,
            "error": (
                "No discovery queries were generated."
            )
        }

    merged = {}
    errors = []
    raw_count = 0

    for query in queries:

        result = search_biotools_by_operation(
            search_term=query,
            limit=per_query
        )

        if result.get(
            "error"
        ):

            errors.append(
                result[
                    "error"
                ]
            )

            continue

        raw_count += len(
            result.get(
                "results",
                []
            )
        )

        for item in result.get(
            "results",
            []
        ):

            key = (
                item.get(
                    "biotools_id"
                )
                or
                normalize_tool_name(
                    item.get(
                        "name"
                    )
                )
            )

            if not key:
                continue

            if key in merged:

                merged[
                    key
                ] = _merge_discovery_item(
                    merged[
                        key
                    ],
                    item
                )

            else:

                merged[
                    key
                ] = item

    results = list(
        merged.values()
    )

    results.sort(
        key=lambda item: (
            len(
                item.get(
                    "query_matches",
                    []
                )
            ),
            item.get(
                "publication_count",
                0
            )
        ),
        reverse=True
    )

    results = results[
        :max(
            1,
            int(
                max_total
            )
        )
    ]

    error = None

    if not results and errors:

        error = (
            " | ".join(
                unique_values(
                    errors
                )
            )
        )

    return {
        "query": (
            " | ".join(
                queries
            )
        ),
        "queries": queries,
        "results": results,
        "raw_count": raw_count,
        "unique_count": len(
            merged
        ),
        "error": error,
        "partial_errors": unique_values(
            errors
        )
    }


# ==================================================
# PUBLIC TOOL LOOKUP
# ==================================================

def get_biotools_info(
    tool_name
):
    """
    Main single-tool lookup used by BioFlow.
    """

    record = search_biotools(
        tool_name
    )

    return simplify_biotools_record(
        record
    )


# ==================================================
# STRUCTURED DISCOVERY
# ==================================================

def _search_biotools_params(
    params,
    matched_query,
    limit=20
):
    """
    Execute one structured bio.tools query.

    bio.tools supports dedicated fields such as `operation`,
    `function`, `inputDataFormat` and `toolType`. BioFlow uses
    those fields when possible instead of relying only on the
    catch-all `q` parameter.
    """

    request_params = {
        "format": "json",
        "per_page": min(
            max(
                int(
                    limit
                ),
                1
            ),
            100
        )
    }

    request_params.update(
        params
    )

    if request_params.get(
        "q"
    ):

        request_params[
            "sort"
        ] = "score"

        request_params[
            "ord"
        ] = "desc"

    try:

        response = requests.get(
            BASE_URL,
            params=request_params,
            timeout=25
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for record in (
            data.get(
                "list",
                []
            )
            or
            []
        ):

            item = simplify_discovery_record(
                record,
                matched_query=matched_query
            )

            if item is not None:

                results.append(
                    item
                )

        return {
            "query": matched_query,
            "results": results,
            "raw_count": data.get(
                "count",
                len(
                    results
                )
            ),
            "error": None
        }

    except requests.RequestException as error:

        return {
            "query": matched_query,
            "results": [],
            "raw_count": 0,
            "error": (
                "bio.tools connection error: "
                f"{error}"
            )
        }

    except ValueError as error:

        return {
            "query": matched_query,
            "results": [],
            "raw_count": 0,
            "error": (
                "bio.tools JSON error: "
                f"{error}"
            )
        }


def search_biotools_structured(
    operation_terms=None,
    query_terms=None,
    per_query=20,
    max_total=120
):
    """
    Capability-oriented bio.tools discovery.

    Search lanes:
      1. dedicated EDAM-operation field
      2. broad text queries for terminology/framework names

    Results are merged by bio.tools ID/name. The structured
    registry is used to FIND candidates; ASV/OTU compatibility is
    still decided by BioFlow's curated capability layer.
    """

    operation_terms = unique_values(
        operation_terms
        or
        []
    )

    query_terms = unique_values(
        query_terms
        or
        []
    )

    merged = {}
    errors = []
    searches = []

    search_specs = []

    for term in operation_terms:

        search_specs.append(
            (
                {
                    "operation": term
                },
                f"operation:{term}"
            )
        )

    for term in query_terms:

        search_specs.append(
            (
                {
                    "q": term
                },
                f"q:{term}"
            )
        )

    for params, label in search_specs:

        result = _search_biotools_params(
            params=params,
            matched_query=label,
            limit=per_query
        )

        searches.append(
            label
        )

        if result.get(
            "error"
        ):

            errors.append(
                result[
                    "error"
                ]
            )

            continue

        for item in result.get(
            "results",
            []
        ):

            key = (
                item.get(
                    "biotools_id"
                )
                or
                normalize_tool_name(
                    item.get(
                        "name"
                    )
                )
            )

            if not key:
                continue

            if key in merged:

                merged[
                    key
                ] = _merge_discovery_item(
                    merged[
                        key
                    ],
                    item
                )

            else:

                merged[
                    key
                ] = item

    results = list(
        merged.values()
    )

    results.sort(
        key=lambda item: (
            len(
                item.get(
                    "query_matches",
                    []
                )
                or
                []
            ),
            item.get(
                "publication_count",
                0
            )
            or
            0,
            item.get(
                "name",
                ""
            ).lower()
        ),
        reverse=True
    )

    results = results[
        :max(
            1,
            int(
                max_total
            )
        )
    ]

    return {
        "queries": searches,
        "results": results,
        "unique_count": len(
            merged
        ),
        "partial_errors": unique_values(
            errors
        ),
        "error": (
            " | ".join(
                unique_values(
                    errors
                )
            )
            if not results
            and errors
            else
            None
        )
    }

