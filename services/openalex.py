import os
import re
from datetime import date

import requests


BASE_URL = "https://api.openalex.org/works"


# ==================================================
# SETTINGS
# ==================================================

def get_openalex_api_key():
    """
    Optional OpenAlex API key.
    """

    return os.getenv(
        "OPENALEX_API_KEY"
    )


def get_openalex_mailto():
    """
    Optional contact e-mail for polite-pool style requests.
    """

    return os.getenv(
        "OPENALEX_MAILTO"
    )


# ==================================================
# TEXT / ALIASES
# ==================================================

def generate_tool_aliases(
    tool_name
):
    """
    Generate common spelling variants of a tool name.
    """

    if not tool_name:

        return []

    tool_name = str(
        tool_name
    ).strip()

    aliases = [
        tool_name
    ]

    spaced = re.sub(
        r"([A-Za-z])(\d+)$",
        r"\1 \2",
        tool_name
    )

    if spaced not in aliases:

        aliases.append(
            spaced
        )

    compact = re.sub(
        r"\s+",
        "",
        tool_name
    )

    if compact not in aliases:

        aliases.append(
            compact
        )

    unique = []
    seen = set()

    for alias in aliases:

        key = alias.lower()

        if key in seen:
            continue

        seen.add(
            key
        )

        unique.append(
            alias
        )

    return unique


# ==================================================
# ABSTRACT RECONSTRUCTION
# ==================================================

def reconstruct_abstract(
    inverted_index
):
    """
    Convert an OpenAlex abstract inverted index to text.
    """

    if not inverted_index:
        return None

    positions = []

    for word, indexes in inverted_index.items():

        for index in indexes:

            positions.append(
                (
                    index,
                    word
                )
            )

    positions.sort(
        key=lambda item:
        item[0]
    )

    return " ".join(
        word
        for _, word
        in positions
    )


# ==================================================
# RECORD SIMPLIFICATION
# ==================================================

def simplify_work(
    work,
    matched_alias=None,
    search_query=None,
    search_scope=None
):
    """
    Convert an OpenAlex Work object into BioFlow's
    common literature representation.
    """

    authors = []

    for authorship in work.get(
        "authorships",
        []
    ) or []:

        author = (
            authorship.get(
                "author",
                {}
            )
            or
            {}
        )

        name = author.get(
            "display_name"
        )

        if name:
            authors.append(
                name
            )

    authors = authors[
        :8
    ]

    source_name = None

    primary_location = (
        work.get(
            "primary_location"
        )
        or
        {}
    )

    source = (
        primary_location.get(
            "source"
        )
        or
        {}
    )

    if source:

        source_name = source.get(
            "display_name"
        )

    doi = work.get(
        "doi"
    )

    doi_url = None

    if doi:

        if str(
            doi
        ).startswith(
            "https://doi.org/"
        ):

            doi_url = doi

        else:

            doi_url = (
                "https://doi.org/"
                f"{doi}"
            )

    open_access = (
        work.get(
            "open_access",
            {}
        )
        or
        {}
    )

    matched_aliases = []

    if matched_alias:

        matched_aliases.append(
            matched_alias
        )

    search_queries = []

    if search_query:

        search_queries.append(
            search_query
        )

    search_scopes = []

    if search_scope:

        search_scopes.append(
            search_scope
        )

    return {
        "id": work.get(
            "id"
        ),
        "title": (
            work.get(
                "title"
            )
            or
            work.get(
                "display_name"
            )
        ),
        "abstract": reconstruct_abstract(
            work.get(
                "abstract_inverted_index"
            )
        ),
        "year": work.get(
            "publication_year"
        ),
        "publication_date": work.get(
            "publication_date"
        ),
        "authors": authors,
        "source": source_name,
        "doi": doi,
        "doi_url": doi_url,
        "pmid": None,
        "pmcid": None,
        "openalex_url": work.get(
            "id"
        ),
        "cited_by_count": (
            work.get(
                "cited_by_count",
                0
            )
            or
            0
        ),
        "type": work.get(
            "type"
        ),
        "is_open_access": open_access.get(
            "is_oa",
            False
        ),
        "matched_aliases": matched_aliases,
        "search_queries": search_queries,
        "search_scopes": search_scopes,
        "source_providers": [
            "OpenAlex"
        ]
    }


# ==================================================
# LOW-LEVEL SEARCH
# ==================================================

def search_query(
    query,
    from_date=None,
    to_date=None,
    per_page=25,
    sort=None,
    search_scope=None
):
    """
    Search OpenAlex works by free text.

    Date filtering is optional so this function can support
    both recent and foundational/seminal searches.
    """

    params = {
        "search": query,
        "per_page": min(
            max(
                int(
                    per_page
                ),
                1
            ),
            100
        )
    }

    filters = []

    if from_date:

        filters.append(
            "from_publication_date:"
            f"{from_date}"
        )

    if to_date:

        filters.append(
            "to_publication_date:"
            f"{to_date}"
        )

    if filters:

        params[
            "filter"
        ] = ",".join(
            filters
        )

    if sort:

        params[
            "sort"
        ] = sort

    api_key = get_openalex_api_key()

    if api_key:

        params[
            "api_key"
        ] = api_key

    mailto = get_openalex_mailto()

    if mailto:

        params[
            "mailto"
        ] = mailto

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=25
    )

    response.raise_for_status()

    data = response.json()

    works = data.get(
        "results",
        []
    ) or []

    return [
        simplify_work(
            work,
            search_query=query,
            search_scope=search_scope
        )
        for work
        in works
    ]


def search_alias(
    alias,
    from_date,
    to_date,
    per_page=25
):
    """
    Backward-compatible exact-name recent search.
    """

    query = (
        f'"{alias}"'
    )

    works = search_query(
        query=query,
        from_date=from_date,
        to_date=to_date,
        per_page=per_page,
        search_scope="recent"
    )

    for work in works:

        work[
            "matched_aliases"
        ] = [
            alias
        ]

    return works


# ==================================================
# MERGING
# ==================================================

def _normalize_doi(
    doi
):
    """
    Normalize DOI strings for cross-query deduplication.
    """

    if not doi:
        return ""

    value = (
        str(
            doi
        )
        .strip()
        .lower()
    )

    for prefix in [
        "https://doi.org/",
        "http://doi.org/",
        "doi:"
    ]:

        if value.startswith(
            prefix
        ):

            value = value[
                len(
                    prefix
                ):
            ]

    return value


def _paper_key(
    paper
):
    """
    Stable key for merging OpenAlex results.
    """

    doi = _normalize_doi(
        paper.get(
            "doi"
        )
    )

    if doi:

        return (
            "doi",
            doi
        )

    identifier = paper.get(
        "id"
    )

    if identifier:

        return (
            "id",
            str(
                identifier
            )
        )

    title = (
        paper.get(
            "title"
        )
        or
        ""
    )

    return (
        "title",
        re.sub(
            r"\W+",
            "",
            title.lower()
        )
    )


def _merge_paper(
    existing,
    incoming
):
    """
    Merge repeated paper hits from multiple aliases/searches.
    """

    merged = existing.copy()

    for field in [
        "matched_aliases",
        "search_queries",
        "search_scopes",
        "source_providers"
    ]:

        values = (
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

        merged[
            field
        ] = list(
            dict.fromkeys(
                values
            )
        )

    for field in [
        "title",
        "abstract",
        "year",
        "publication_date",
        "source",
        "doi",
        "doi_url",
        "openalex_url",
        "type"
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

    merged[
        "cited_by_count"
    ] = max(
        existing.get(
            "cited_by_count",
            0
        )
        or
        0,
        incoming.get(
            "cited_by_count",
            0
        )
        or
        0
    )

    return merged


# ==================================================
# TOOL-SPECIFIC LITERATURE
# ==================================================

def search_recent_literature(
    tool_name,
    operation=None,
    years=5,
    limit=10
):
    """
    Search recent literature for a known tool.

    Kept for backward compatibility with the existing BioFlow UI.
    """

    aliases = generate_tool_aliases(
        tool_name
    )

    current_date = date.today()

    from_year = (
        current_date.year
        -
        years
    )

    from_date = (
        f"{from_year}-01-01"
    )

    to_date = current_date.isoformat()

    merged = {}
    search_queries = []

    try:

        for alias in aliases:

            query = (
                f'"{alias}"'
            )

            search_queries.append(
                query
            )

            works = search_alias(
                alias,
                from_date,
                to_date,
                per_page=25
            )

            for paper in works:

                key = _paper_key(
                    paper
                )

                if key in merged:

                    merged[
                        key
                    ] = _merge_paper(
                        merged[
                            key
                        ],
                        paper
                    )

                else:

                    merged[
                        key
                    ] = paper

        results = list(
            merged.values()
        )

        results.sort(
            key=lambda paper: (
                paper.get(
                    "year",
                    0
                )
                or
                0,
                paper.get(
                    "cited_by_count",
                    0
                )
                or
                0
            ),
            reverse=True
        )

        return {
            "query": (
                " OR ".join(
                    search_queries
                )
            ),
            "aliases": aliases,
            "operation": operation,
            "total_results": len(
                merged
            ),
            "results": results[
                :limit
            ],
            "error": None,
            "provider": "OpenAlex",
            "scope": "recent"
        }

    except requests.HTTPError as error:

        status_code = (
            error.response.status_code
            if error.response
            is not None
            else None
        )

        if status_code in (
            401,
            403,
            429
        ):

            message = (
                "OpenAlex request was rejected or rate-limited."
            )

        else:

            message = (
                "OpenAlex HTTP error: "
                f"{error}"
            )

        return {
            "query": (
                " OR ".join(
                    search_queries
                )
            ),
            "aliases": aliases,
            "operation": operation,
            "total_results": 0,
            "results": [],
            "error": message,
            "provider": "OpenAlex",
            "scope": "recent"
        }

    except requests.RequestException as error:

        return {
            "query": (
                " OR ".join(
                    search_queries
                )
            ),
            "aliases": aliases,
            "operation": operation,
            "total_results": 0,
            "results": [],
            "error": (
                "OpenAlex connection error: "
                f"{error}"
            ),
            "provider": "OpenAlex",
            "scope": "recent"
        }

    except ValueError as error:

        return {
            "query": (
                " OR ".join(
                    search_queries
                )
            ),
            "aliases": aliases,
            "operation": operation,
            "total_results": 0,
            "results": [],
            "error": (
                "OpenAlex JSON error: "
                f"{error}"
            ),
            "provider": "OpenAlex",
            "scope": "recent"
        }


def search_foundational_literature(
    tool_name,
    operation=None,
    limit=10
):
    """
    Search all publication years for influential/primary
    papers about a known tool.
    """

    aliases = generate_tool_aliases(
        tool_name
    )

    merged = {}
    search_queries = []

    try:

        for alias in aliases:

            query = (
                f'"{alias}"'
            )

            search_queries.append(
                query
            )

            papers = search_query(
                query=query,
                per_page=min(
                    25,
                    max(
                        limit,
                        10
                    )
                ),
                sort="cited_by_count:desc",
                search_scope="foundational"
            )

            for paper in papers:

                paper[
                    "matched_aliases"
                ] = [
                    alias
                ]

                key = _paper_key(
                    paper
                )

                if key in merged:

                    merged[
                        key
                    ] = _merge_paper(
                        merged[
                            key
                        ],
                        paper
                    )

                else:

                    merged[
                        key
                    ] = paper

        results = list(
            merged.values()
        )

        results.sort(
            key=lambda paper: (
                paper.get(
                    "cited_by_count",
                    0
                )
                or
                0,
                paper.get(
                    "year",
                    0
                )
                or
                0
            ),
            reverse=True
        )

        return {
            "query": (
                " OR ".join(
                    search_queries
                )
            ),
            "aliases": aliases,
            "operation": operation,
            "total_results": len(
                merged
            ),
            "results": results[
                :limit
            ],
            "error": None,
            "provider": "OpenAlex",
            "scope": "foundational"
        }

    except (
        requests.RequestException,
        ValueError
    ) as error:

        return {
            "query": (
                " OR ".join(
                    search_queries
                )
            ),
            "aliases": aliases,
            "operation": operation,
            "total_results": 0,
            "results": [],
            "error": (
                "OpenAlex foundational-search error: "
                f"{error}"
            ),
            "provider": "OpenAlex",
            "scope": "foundational"
        }


# ==================================================
# TOPIC / DISCOVERY LITERATURE
# ==================================================

def search_topic_literature(
    query,
    years=8,
    limit=10
):
    """
    Broad topic search used by Research Engine v2 to discover
    candidate tools mentioned in method/comparison literature.
    """

    current_date = date.today()

    from_date = None

    if years is not None:

        from_date = (
            f"{current_date.year - int(years)}-01-01"
        )

    try:

        papers = search_query(
            query=query,
            from_date=from_date,
            to_date=current_date.isoformat(),
            per_page=min(
                max(
                    limit,
                    10
                ),
                50
            ),
            search_scope="discovery"
        )

        return {
            "query": query,
            "results": papers[
                :limit
            ],
            "error": None,
            "provider": "OpenAlex",
            "scope": "discovery"
        }

    except (
        requests.RequestException,
        ValueError
    ) as error:

        return {
            "query": query,
            "results": [],
            "error": (
                "OpenAlex topic-search error: "
                f"{error}"
            ),
            "provider": "OpenAlex",
            "scope": "discovery"
        }
