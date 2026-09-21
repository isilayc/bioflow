import re

from services.openalex import (
    search_recent_literature as openalex_recent,
    search_foundational_literature as openalex_foundational,
    search_topic_literature as openalex_topic
)

from services.europepmc import (
    search_tool_literature as europepmc_tool,
    search_topic_literature as europepmc_topic
)

from services.pubmed import (
    search_tool_literature as pubmed_tool
)


# ==================================================
# NORMALIZATION / MERGING
# ==================================================

def normalize_doi(
    doi
):

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


def normalize_title(
    title
):

    if not title:
        return ""

    return re.sub(
        r"[^a-z0-9]+",
        "",
        str(
            title
        ).lower()
    )


def paper_key(
    paper
):
    """
    Prefer DOI, then PMID, then normalized title.
    """

    doi = normalize_doi(
        paper.get(
            "doi"
        )
    )

    if doi:

        return (
            "doi",
            doi
        )

    pmid = paper.get(
        "pmid"
    )

    if pmid:

        return (
            "pmid",
            str(
                pmid
            )
        )

    title = normalize_title(
        paper.get(
            "title"
        )
    )

    if title:

        return (
            "title",
            title
        )

    identifier = paper.get(
        "id"
    )

    return (
        "id",
        str(
            identifier
        )
    )


def unique_values(
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


def merge_papers(
    papers
):
    """
    Merge duplicate publications across OpenAlex, Europe PMC
    and PubMed while preserving provenance.
    """

    merged = {}

    for paper in papers or []:

        if not isinstance(
            paper,
            dict
        ):
            continue

        key = paper_key(
            paper
        )

        if key not in merged:

            merged[
                key
            ] = paper.copy()

            continue

        current = merged[
            key
        ]

        for field in [
            "source_providers",
            "matched_aliases",
            "search_queries",
            "search_scopes",
            "publication_types"
        ]:

            current[
                field
            ] = unique_values(
                (
                    current.get(
                        field,
                        []
                    )
                    or
                    []
                )
                +
                (
                    paper.get(
                        field,
                        []
                    )
                    or
                    []
                )
            )

        for field in [
            "title",
            "abstract",
            "year",
            "publication_date",
            "authors",
            "source",
            "doi",
            "doi_url",
            "pmid",
            "pmcid",
            "openalex_url",
            "europepmc_url",
            "pubmed_url",
            "type"
        ]:

            if not current.get(
                field
            ) and paper.get(
                field
            ):

                current[
                    field
                ] = paper[
                    field
                ]

        current[
            "cited_by_count"
        ] = max(
            current.get(
                "cited_by_count",
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
        )

        current[
            "is_open_access"
        ] = bool(
            current.get(
                "is_open_access",
                False
            )
            or
            paper.get(
                "is_open_access",
                False
            )
        )

    return list(
        merged.values()
    )


# ==================================================
# TOOL EVIDENCE
# ==================================================

def search_tool_evidence(
    tool_name,
    operation=None,
    recent_years=5,
    limit=15
):
    """
    Multi-source evidence search for a known tool.

    Search lanes:
      - recent OpenAlex
      - recent Europe PMC
      - recent PubMed
      - all-time influential OpenAlex
      - all-time influential Europe PMC

    This keeps old primary/method papers while also measuring
    whether the tool is still represented in recent literature.
    """

    provider_results = []

    provider_results.append(
        openalex_recent(
            tool_name=tool_name,
            operation=operation,
            years=recent_years,
            limit=10
        )
    )

    provider_results.append(
        europepmc_tool(
            tool_name=tool_name,
            years=recent_years,
            limit=10,
            foundational=False
        )
    )

    provider_results.append(
        pubmed_tool(
            tool_name=tool_name,
            years=recent_years,
            limit=10,
            foundational=False
        )
    )

    provider_results.append(
        openalex_foundational(
            tool_name=tool_name,
            operation=operation,
            limit=8
        )
    )

    provider_results.append(
        europepmc_tool(
            tool_name=tool_name,
            years=None,
            limit=8,
            foundational=True
        )
    )

    all_papers = []
    errors = []
    searches = []

    for result in provider_results:

        provider = result.get(
            "provider"
        )

        scope = result.get(
            "scope"
        )

        searches.append(
            {
                "provider": provider,
                "scope": scope,
                "query": result.get(
                    "query"
                ),
                "error": result.get(
                    "error"
                )
            }
        )

        if result.get(
            "error"
        ):

            errors.append(
                f"{provider}: "
                f"{result['error']}"
            )

        all_papers.extend(
            result.get(
                "results",
                []
            )
            or
            []
        )

    merged = merge_papers(
        all_papers
    )

    merged.sort(
        key=lambda paper: (
            1
            if
            "recent"
            in
            (
                paper.get(
                    "search_scopes",
                    []
                )
                or
                []
            )
            else
            0,
            len(
                paper.get(
                    "source_providers",
                    []
                )
                or
                []
            ),
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
            f"Multi-source evidence search "
            f"for {tool_name}"
        ),
        "operation": operation,
        "tool_name": tool_name,
        "results": merged[
            :limit
        ],
        "total_results": len(
            merged
        ),
        "providers_searched": [
            "OpenAlex",
            "Europe PMC",
            "PubMed"
        ],
        "searches": searches,
        "partial_errors": errors,
        "error": (
            "All literature providers failed."
            if not merged
            and len(
                errors
            )
            ==
            len(
                provider_results
            )
            else
            None
        )
    }


# ==================================================
# DISCOVERY LITERATURE
# ==================================================

def search_discovery_literature(
    query_terms,
    years=8,
    max_queries=3,
    per_source_limit=8
):
    """
    Search broad method/comparison literature for candidate
    resources that may not be registered in bio.tools.

    Europe PMC and OpenAlex are used here because Europe PMC
    already covers PubMed records and also offers broader
    full-text-oriented retrieval. PubMed is retained as a
    separate source for candidate verification once a named
    tool is being evaluated.
    """

    queries = unique_values(
        query_terms
    )[
        :max(
            1,
            int(
                max_queries
            )
        )
    ]

    provider_results = []
    errors = []

    for query in queries:

        openalex_result = (
            openalex_topic(
                query=query,
                years=years,
                limit=per_source_limit
            )
        )

        europepmc_result = (
            europepmc_topic(
                query=query,
                years=years,
                limit=per_source_limit
            )
        )

        provider_results.extend(
            [
                openalex_result,
                europepmc_result
            ]
        )

    all_papers = []

    for result in provider_results:

        if result.get(
            "error"
        ):

            errors.append(
                f"{result.get('provider')}: "
                f"{result.get('error')}"
            )

        all_papers.extend(
            result.get(
                "results",
                []
            )
            or
            []
        )

    merged = merge_papers(
        all_papers
    )

    merged.sort(
        key=lambda paper: (
            len(
                paper.get(
                    "source_providers",
                    []
                )
                or
                []
            ),
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
        "queries": queries,
        "results": merged,
        "providers_searched": [
            "OpenAlex",
            "Europe PMC"
        ],
        "partial_errors": errors,
        "error": (
            "All discovery-literature searches failed."
            if not merged
            and errors
            and len(
                errors
            )
            >=
            len(
                provider_results
            )
            else
            None
        )
    }
