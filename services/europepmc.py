from datetime import date
import re

import requests


BASE_URL = (
    "https://www.ebi.ac.uk/"
    "europepmc/webservices/rest/search"
)


# ==================================================
# UTILITIES
# ==================================================

def _normalize_doi(
    doi
):

    if not doi:
        return None

    value = (
        str(
            doi
        )
        .strip()
    )

    if value.lower().startswith(
        "https://doi.org/"
    ):

        return value[
            len(
                "https://doi.org/"
            ):
        ]

    if value.lower().startswith(
        "doi:"
    ):

        return value[
            len(
                "doi:"
            ):
        ]

    return value


def _safe_int(
    value,
    default=0
):

    try:

        return int(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return default


def _doi_url(
    doi
):

    normalized = _normalize_doi(
        doi
    )

    if not normalized:
        return None

    return (
        "https://doi.org/"
        f"{normalized}"
    )


# ==================================================
# RECORD SIMPLIFICATION
# ==================================================

def simplify_record(
    record,
    matched_alias=None,
    search_query=None,
    search_scope=None
):
    """
    Convert a Europe PMC result into BioFlow's common
    literature representation.
    """

    doi = _normalize_doi(
        record.get(
            "doi"
        )
    )

    pmid = (
        record.get(
            "pmid"
        )
        or
        (
            record.get(
                "id"
            )
            if record.get(
                "source"
            )
            ==
            "MED"
            else
            None
        )
    )

    pmcid = record.get(
        "pmcid"
    )

    europepmc_url = None

    source_code = (
        record.get(
            "source"
        )
        or
        ""
    )

    ext_id = (
        record.get(
            "id"
        )
        or
        record.get(
            "pmid"
        )
        or
        pmcid
    )

    if ext_id:

        europepmc_url = (
            "https://europepmc.org/article/"
            f"{source_code}/{ext_id}"
        )

    authors = []

    author_string = (
        record.get(
            "authorString"
        )
        or
        ""
    )

    if author_string:

        authors = [
            item.strip()
            for item in author_string.split(
                ","
            )
            if item.strip()
        ][
            :8
        ]

    return {
        "id": (
            f"europepmc:{source_code}:{ext_id}"
            if ext_id
            else
            None
        ),
        "title": record.get(
            "title"
        ),
        "abstract": record.get(
            "abstractText"
        ),
        "year": _safe_int(
            record.get(
                "pubYear"
            ),
            default=None
        ),
        "publication_date": (
            record.get(
                "firstPublicationDate"
            )
            or
            record.get(
                "firstIndexDate"
            )
        ),
        "authors": authors,
        "source": (
            record.get(
                "journalTitle"
            )
            or
            record.get(
                "journalInfo",
                {}
            ).get(
                "journal",
                {}
            ).get(
                "title"
            )
            if isinstance(
                record.get(
                    "journalInfo"
                ),
                dict
            )
            else
            record.get(
                "journalTitle"
            )
        ),
        "doi": doi,
        "doi_url": _doi_url(
            doi
        ),
        "pmid": pmid,
        "pmcid": pmcid,
        "europepmc_url": europepmc_url,
        "openalex_url": None,
        "pubmed_url": (
            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            if pmid
            else
            None
        ),
        "cited_by_count": _safe_int(
            record.get(
                "citedByCount"
            ),
            default=0
        ),
        "type": (
            record.get(
                "pubType"
            )
            or
            record.get(
                "pubTypeList",
                {}
            )
        ),
        "is_open_access": (
            str(
                record.get(
                    "isOpenAccess",
                    ""
                )
            ).upper()
            ==
            "Y"
        ),
        "matched_aliases": (
            [
                matched_alias
            ]
            if matched_alias
            else
            []
        ),
        "search_queries": (
            [
                search_query
            ]
            if search_query
            else
            []
        ),
        "search_scopes": (
            [
                search_scope
            ]
            if search_scope
            else
            []
        ),
        "source_providers": [
            "Europe PMC"
        ]
    }


# ==================================================
# SEARCH
# ==================================================

def search_query(
    query,
    limit=10,
    years=None,
    sort_mode="relevance",
    search_scope=None
):
    """
    Search Europe PMC's public REST API.

    `years=None` means no publication-year restriction.
    """

    current_year = (
        date.today().year
    )

    effective_query = (
        str(
            query
        ).strip()
    )

    if years is not None:

        from_year = (
            current_year
            -
            int(
                years
            )
        )

        effective_query = (
            f"({effective_query}) "
            f"AND FIRST_PDATE:"
            f"[{from_year}-01-01 TO "
            f"{current_year}-12-31]"
        )

    if sort_mode == "date":

        effective_query += (
            " sort_date:y"
        )

    elif sort_mode == "cited":

        effective_query += (
            " sort_cited:y"
        )

    params = {
        "query": effective_query,
        "format": "json",
        "resultType": "core",
        "pageSize": min(
            max(
                int(
                    limit
                ),
                1
            ),
            100
        )
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=25
    )

    response.raise_for_status()

    data = response.json()

    result_list = (
        data.get(
            "resultList",
            {}
        )
        or
        {}
    )

    records = (
        result_list.get(
            "result",
            []
        )
        or
        []
    )

    papers = [
        simplify_record(
            record,
            search_query=query,
            search_scope=search_scope
        )
        for record
        in records
    ]

    return {
        "query": query,
        "effective_query": effective_query,
        "results": papers,
        "total_results": _safe_int(
            data.get(
                "hitCount"
            ),
            default=len(
                papers
            )
        ),
        "error": None,
        "provider": "Europe PMC",
        "scope": search_scope
    }


def search_tool_literature(
    tool_name,
    years=5,
    limit=10,
    foundational=False
):
    """
    Search Europe PMC for a known tool name.

    Recent and foundational searches are separate so old,
    highly influential method papers are not discarded.
    """

    alias = str(
        tool_name
    ).strip()

    query = (
        f'"{alias}"'
    )

    try:

        if foundational:

            result = search_query(
                query=query,
                limit=limit,
                years=None,
                sort_mode="cited",
                search_scope="foundational"
            )

        else:

            result = search_query(
                query=query,
                limit=limit,
                years=years,
                sort_mode="date",
                search_scope="recent"
            )

        for paper in result.get(
            "results",
            []
        ):

            paper[
                "matched_aliases"
            ] = [
                alias
            ]

        return result

    except requests.RequestException as error:

        return {
            "query": query,
            "results": [],
            "total_results": 0,
            "error": (
                "Europe PMC connection error: "
                f"{error}"
            ),
            "provider": "Europe PMC",
            "scope": (
                "foundational"
                if foundational
                else
                "recent"
            )
        }

    except ValueError as error:

        return {
            "query": query,
            "results": [],
            "total_results": 0,
            "error": (
                "Europe PMC JSON error: "
                f"{error}"
            ),
            "provider": "Europe PMC",
            "scope": (
                "foundational"
                if foundational
                else
                "recent"
            )
        }


def search_topic_literature(
    query,
    years=8,
    limit=10
):
    """
    Broad topic search for Research Engine v2 discovery.
    """

    try:

        return search_query(
            query=query,
            limit=limit,
            years=years,
            sort_mode="relevance",
            search_scope="discovery"
        )

    except requests.RequestException as error:

        return {
            "query": query,
            "results": [],
            "total_results": 0,
            "error": (
                "Europe PMC topic-search error: "
                f"{error}"
            ),
            "provider": "Europe PMC",
            "scope": "discovery"
        }

    except ValueError as error:

        return {
            "query": query,
            "results": [],
            "total_results": 0,
            "error": (
                "Europe PMC JSON error: "
                f"{error}"
            ),
            "provider": "Europe PMC",
            "scope": "discovery"
        }
