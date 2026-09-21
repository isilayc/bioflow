import os
import time
import xml.etree.ElementTree as ET
from datetime import date

import requests


EUTILS_BASE = (
    "https://eutils.ncbi.nlm.nih.gov/"
    "entrez/eutils"
)


# ==================================================
# SETTINGS
# ==================================================

def get_ncbi_api_key():
    """
    Optional NCBI API key.
    """

    return os.getenv(
        "NCBI_API_KEY"
    )


def get_ncbi_email():
    """
    Optional contact e-mail recommended by NCBI.

    BioFlow remains usable without it at the conservative
    anonymous request rate used here.
    """

    return os.getenv(
        "NCBI_EMAIL"
    )


def _base_params():
    """
    Common NCBI E-utilities parameters.
    """

    params = {
        "tool": "BioFlow"
    }

    email = get_ncbi_email()

    if email:

        params[
            "email"
        ] = email

    api_key = get_ncbi_api_key()

    if api_key:

        params[
            "api_key"
        ] = api_key

    return params


def _polite_pause():
    """
    Keep anonymous requests comfortably below NCBI's
    standard unauthenticated request-rate guidance.
    """

    if not get_ncbi_api_key():

        time.sleep(
            0.36
        )


# ==================================================
# XML UTILITIES
# ==================================================

def _text(
    element
):

    if element is None:
        return None

    value = "".join(
        element.itertext()
    ).strip()

    return value or None


def _safe_int(
    value,
    default=None
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


def _extract_year(
    article
):
    """
    Extract a best-effort publication year.
    """

    for xpath in [
        ".//ArticleDate/Year",
        ".//JournalIssue/PubDate/Year",
        ".//PubMedPubDate[@PubStatus='pubmed']/Year",
        ".//PubMedPubDate/Year"
    ]:

        value = article.findtext(
            xpath
        )

        year = _safe_int(
            value
        )

        if year:

            return year

    medline_date = article.findtext(
        ".//JournalIssue/PubDate/MedlineDate"
    )

    if medline_date:

        for token in medline_date.split():

            year = _safe_int(
                token[:4]
            )

            if year:

                return year

    return None


def _extract_ids(
    article
):

    identifiers = {
        "doi": None,
        "pmid": None,
        "pmcid": None
    }

    pmid = article.findtext(
        ".//MedlineCitation/PMID"
    )

    if pmid:

        identifiers[
            "pmid"
        ] = pmid.strip()

    for item in article.findall(
        ".//PubmedData/ArticleIdList/ArticleId"
    ):

        value = _text(
            item
        )

        id_type = (
            item.attrib.get(
                "IdType",
                ""
            )
            .strip()
            .lower()
        )

        if id_type == "doi":

            identifiers[
                "doi"
            ] = value

        elif id_type == "pmc":

            identifiers[
                "pmcid"
            ] = value

        elif id_type == "pubmed":

            identifiers[
                "pmid"
            ] = (
                value
                or
                identifiers[
                    "pmid"
                ]
            )

    return identifiers


def _extract_authors(
    article
):

    authors = []

    for author in article.findall(
        ".//Article/AuthorList/Author"
    ):

        collective = author.findtext(
            "CollectiveName"
        )

        if collective:

            authors.append(
                collective.strip()
            )

            continue

        last = (
            author.findtext(
                "LastName"
            )
            or
            ""
        ).strip()

        initials = (
            author.findtext(
                "Initials"
            )
            or
            ""
        ).strip()

        name = " ".join(
            value
            for value in [
                last,
                initials
            ]
            if value
        )

        if name:

            authors.append(
                name
            )

    return authors[
        :8
    ]


def _extract_abstract(
    article
):

    parts = []

    for item in article.findall(
        ".//Article/Abstract/AbstractText"
    ):

        value = _text(
            item
        )

        if not value:
            continue

        label = (
            item.attrib.get(
                "Label"
            )
            or
            item.attrib.get(
                "NlmCategory"
            )
        )

        if label:

            parts.append(
                f"{label}: {value}"
            )

        else:

            parts.append(
                value
            )

    return (
        "\n".join(
            parts
        )
        or
        None
    )


def simplify_article(
    article,
    matched_alias=None,
    search_query=None,
    search_scope=None
):
    """
    Convert one PubMedArticle XML node to BioFlow's
    common literature representation.
    """

    identifiers = _extract_ids(
        article
    )

    doi = identifiers.get(
        "doi"
    )

    pmid = identifiers.get(
        "pmid"
    )

    pmcid = identifiers.get(
        "pmcid"
    )

    title = _text(
        article.find(
            ".//Article/ArticleTitle"
        )
    )

    journal = (
        article.findtext(
            ".//Article/Journal/Title"
        )
        or
        article.findtext(
            ".//Article/Journal/ISOAbbreviation"
        )
    )

    publication_types = [
        _text(
            item
        )
        for item in article.findall(
            ".//Article/PublicationTypeList/PublicationType"
        )
    ]

    publication_types = [
        value
        for value in publication_types
        if value
    ]

    return {
        "id": (
            f"pubmed:{pmid}"
            if pmid
            else
            None
        ),
        "title": title,
        "abstract": _extract_abstract(
            article
        ),
        "year": _extract_year(
            article
        ),
        "publication_date": None,
        "authors": _extract_authors(
            article
        ),
        "source": journal,
        "doi": doi,
        "doi_url": (
            f"https://doi.org/{doi}"
            if doi
            else
            None
        ),
        "pmid": pmid,
        "pmcid": pmcid,
        "pubmed_url": (
            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            if pmid
            else
            None
        ),
        "europepmc_url": (
            f"https://europepmc.org/article/MED/{pmid}"
            if pmid
            else
            None
        ),
        "openalex_url": None,
        "cited_by_count": 0,
        "type": (
            "; ".join(
                publication_types
            )
            if publication_types
            else
            None
        ),
        "publication_types": publication_types,
        "is_open_access": False,
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
            "PubMed"
        ]
    }


# ==================================================
# SEARCH / FETCH
# ==================================================

def search_ids(
    query,
    limit=10,
    sort="relevance"
):
    """
    PubMed ESearch.
    """

    params = _base_params()

    params.update(
        {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": min(
                max(
                    int(
                        limit
                    ),
                    1
                ),
                100
            ),
            "sort": sort
        }
    )

    response = requests.get(
        f"{EUTILS_BASE}/esearch.fcgi",
        params=params,
        timeout=25
    )

    response.raise_for_status()

    data = response.json()

    result = (
        data.get(
            "esearchresult",
            {}
        )
        or
        {}
    )

    ids = (
        result.get(
            "idlist",
            []
        )
        or
        []
    )

    count = _safe_int(
        result.get(
            "count"
        ),
        default=len(
            ids
        )
    )

    _polite_pause()

    return ids, count


def fetch_articles(
    pmids
):
    """
    Fetch PubMed XML records in one batch.
    """

    if not pmids:

        return []

    params = _base_params()

    params.update(
        {
            "db": "pubmed",
            "id": ",".join(
                str(
                    pmid
                )
                for pmid
                in pmids
            ),
            "retmode": "xml"
        }
    )

    response = requests.get(
        f"{EUTILS_BASE}/efetch.fcgi",
        params=params,
        timeout=30
    )

    response.raise_for_status()

    root = ET.fromstring(
        response.content
    )

    _polite_pause()

    return root.findall(
        ".//PubmedArticle"
    )


def search_query(
    query,
    limit=10,
    years=None,
    sort="relevance",
    search_scope=None
):
    """
    Search PubMed and return parsed article metadata.
    """

    effective_query = (
        str(
            query
        ).strip()
    )

    if years is not None:

        current_year = (
            date.today().year
        )

        from_year = (
            current_year
            -
            int(
                years
            )
        )

        effective_query = (
            f"({effective_query}) AND "
            f'("{from_year}/01/01"[Date - Publication] : '
            f'"{current_year}/12/31"[Date - Publication])'
        )

    pmids, total_count = search_ids(
        effective_query,
        limit=limit,
        sort=sort
    )

    nodes = fetch_articles(
        pmids
    )

    papers = [
        simplify_article(
            node,
            search_query=query,
            search_scope=search_scope
        )
        for node
        in nodes
    ]

    return {
        "query": query,
        "effective_query": effective_query,
        "results": papers,
        "total_results": total_count,
        "error": None,
        "provider": "PubMed",
        "scope": search_scope
    }


# ==================================================
# PUBLIC HELPERS
# ==================================================

def search_tool_literature(
    tool_name,
    years=5,
    limit=10,
    foundational=False
):
    """
    Search PubMed for a known tool name.
    """

    alias = str(
        tool_name
    ).strip()

    query = (
        f'"{alias}"[Title/Abstract]'
    )

    try:

        if foundational:

            result = search_query(
                query=query,
                limit=limit,
                years=None,
                sort="relevance",
                search_scope="foundational"
            )

        else:

            result = search_query(
                query=query,
                limit=limit,
                years=years,
                sort="pub date",
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
                "PubMed connection error: "
                f"{error}"
            ),
            "provider": "PubMed",
            "scope": (
                "foundational"
                if foundational
                else
                "recent"
            )
        }

    except (
        ValueError,
        ET.ParseError
    ) as error:

        return {
            "query": query,
            "results": [],
            "total_results": 0,
            "error": (
                "PubMed parse error: "
                f"{error}"
            ),
            "provider": "PubMed",
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
    Broad PubMed search used for candidate discovery.
    """

    try:

        return search_query(
            query=query,
            limit=limit,
            years=years,
            sort="relevance",
            search_scope="discovery"
        )

    except requests.RequestException as error:

        return {
            "query": query,
            "results": [],
            "total_results": 0,
            "error": (
                "PubMed topic-search error: "
                f"{error}"
            ),
            "provider": "PubMed",
            "scope": "discovery"
        }

    except (
        ValueError,
        ET.ParseError
    ) as error:

        return {
            "query": query,
            "results": [],
            "total_results": 0,
            "error": (
                "PubMed topic-search parse error: "
                f"{error}"
            ),
            "provider": "PubMed",
            "scope": "discovery"
        }
