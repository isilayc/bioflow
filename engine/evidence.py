import re
from datetime import date


# ==================================================
# KEYWORDS
# ==================================================

BENCHMARK_KEYWORDS = [
    "benchmark",
    "benchmarking",
    "comparison",
    "comparative",
    "compare",
    "evaluation",
    "evaluating",
    "performance assessment",
    "performance comparison",
    "compared"
]


REVIEW_KEYWORDS = [
    "review",
    "systematic review",
    "scoping review",
    "survey",
    "overview"
]


METHOD_KEYWORDS = [
    "introducing",
    "we present",
    "we developed",
    "we introduce",
    "new tool",
    "new software",
    "software for",
    "algorithm for",
    "pipeline for",
    "web server",
    "framework for",
    "package for"
]


GENERIC_TOOL_NAMES = {
    "mlst",
    "blast",
    "star",
    "raven"
}


GENERIC_TOOL_CONTEXT = {

    "star": [
        "rna-seq",
        "rna seq",
        "splice",
        "spliced",
        "transcriptome",
        "transcriptomic",
        "read alignment"
    ],

    "mlst": [
        "software",
        "command-line",
        "command line",
        "bioinformatics tool",
        "package",
        "github"
    ],

    "blast": [
        "sequence alignment",
        "sequence similarity",
        "nucleotide",
        "protein sequence",
        "bioinformatics"
    ],

    "raven": [
        "genome assembly",
        "assembler",
        "long-read",
        "long read",
        "nanopore",
        "pacbio"
    ]
}


# ==================================================
# TEXT UTILITIES
# ==================================================

def normalize_text(
    value
):

    if value is None:
        return ""

    return str(
        value
    ).lower().strip()


def compact_text(
    value
):
    """
    Remove spaces and punctuation for controlled alias comparison.
    """

    text = normalize_text(
        value
    )

    return re.sub(
        r"[^a-z0-9]+",
        "",
        text
    )


def generate_tool_aliases(
    tool_name
):

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


def contains_keyword(
    text,
    keywords
):

    normalized = normalize_text(
        text
    )

    for keyword in keywords:

        if normalize_text(
            keyword
        ) in normalized:

            return True

    return False


def _exact_token_match(
    text,
    alias
):
    """
    Word-boundary style matching for short/generic tool names.
    """

    if not text or not alias:
        return False

    escaped = re.escape(
        alias
    )

    pattern = (
        r"(?<![A-Za-z0-9])"
        f"{escaped}"
        r"(?![A-Za-z0-9])"
    )

    return bool(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )
    )


# ==================================================
# TOOL MENTION
# ==================================================

def tool_is_mentioned(
    paper,
    tool_name,
    operation=None
):
    """
    Detect whether a paper actually mentions the named tool.

    Generic names are handled more conservatively than in the
    original BioFlow implementation to reduce false positives.
    """

    title = (
        paper.get(
            "title"
        )
        or
        ""
    )

    abstract = (
        paper.get(
            "abstract"
        )
        or
        ""
    )

    text = (
        title
        +
        " "
        +
        abstract
    )

    aliases = generate_tool_aliases(
        tool_name
    )

    normalized_name = normalize_text(
        tool_name
    )

    generic = (
        normalized_name
        in
        GENERIC_TOOL_NAMES
    )

    visible_match = False

    for alias in aliases:

        if generic:

            if _exact_token_match(
                text,
                alias
            ):

                visible_match = True
                break

        else:

            if (
                compact_text(
                    alias
                )
                in
                compact_text(
                    text
                )
            ):

                visible_match = True
                break

    if visible_match:

        if not generic:

            return True

        required_context = (
            GENERIC_TOOL_CONTEXT.get(
                normalized_name,
                []
            )
        )

        if contains_keyword(
            text,
            required_context
        ):

            return True

    matched_aliases = (
        paper.get(
            "matched_aliases",
            []
        )
        or
        []
    )

    tool_compact = compact_text(
        tool_name
    )

    for alias in matched_aliases:

        if (
            compact_text(
                alias
            )
            ==
            tool_compact
        ):

            if not generic:

                return True

            if contains_keyword(
                text,
                GENERIC_TOOL_CONTEXT.get(
                    normalized_name,
                    []
                )
            ):

                return True

    return False


# ==================================================
# EVIDENCE CLASSIFICATION
# ==================================================

def classify_evidence(
    paper,
    tool_name,
    operation=None
):

    title = normalize_text(
        paper.get(
            "title"
        )
    )

    abstract = normalize_text(
        paper.get(
            "abstract"
        )
    )

    combined_text = (
        title
        +
        " "
        +
        abstract
    )

    paper_type = normalize_text(
        paper.get(
            "type"
        )
    )

    publication_types = " ".join(
        normalize_text(
            value
        )
        for value in (
            paper.get(
                "publication_types",
                []
            )
            or
            []
        )
    )

    mentioned = tool_is_mentioned(
        paper,
        tool_name,
        operation=operation
    )

    if not mentioned:

        return {
            "category": "weak",
            "label": "General / weak evidence",
            "score": 1
        }

    if contains_keyword(
        combined_text,
        BENCHMARK_KEYWORDS
    ):

        return {
            "category": "benchmark",
            "label": "Benchmark / comparative study",
            "score": 5
        }

    if contains_keyword(
        combined_text,
        METHOD_KEYWORDS
    ):

        return {
            "category": "method",
            "label": "Method / tool paper",
            "score": 4
        }

    if (
        "review"
        in paper_type
        or
        "review"
        in publication_types
        or
        contains_keyword(
            combined_text,
            REVIEW_KEYWORDS
        )
    ):

        return {
            "category": "review",
            "label": "Review",
            "score": 3
        }

    return {
        "category": "application",
        "label": "Application / usage evidence",
        "score": 2
    }


def classify_papers(
    papers,
    tool_name,
    operation=None
):

    classified = []

    for paper in papers or []:

        evidence = classify_evidence(
            paper,
            tool_name,
            operation=operation
        )

        paper_copy = paper.copy()

        paper_copy[
            "evidence_category"
        ] = evidence[
            "category"
        ]

        paper_copy[
            "evidence_label"
        ] = evidence[
            "label"
        ]

        paper_copy[
            "evidence_score"
        ] = evidence[
            "score"
        ]

        classified.append(
            paper_copy
        )

    return classified


# ==================================================
# PAPER RANKING
# ==================================================

def rank_evidence(
    papers
):

    return sorted(
        papers or [],
        key=lambda paper: (
            paper.get(
                "evidence_score",
                0
            ),
            len(
                paper.get(
                    "source_providers",
                    []
                )
                or
                []
            ),
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


# ==================================================
# LITERATURE EVIDENCE SCORE
# ==================================================

def score_literature_evidence(
    papers
):
    """
    Score multi-source literature evidence.

    The score separates:
      evidence type      70
      recency            10
      source confirmation 10
      citation signal    10

    Old primary/method papers therefore remain valuable even
    when they fall outside the recent-literature window.
    """

    current_year = date.today().year

    papers = papers or []

    relevant_papers = [
        paper
        for paper in papers
        if paper.get(
            "evidence_category"
        )
        !=
        "weak"
    ]

    benchmark_count = sum(
        1
        for paper in relevant_papers
        if paper.get(
            "evidence_category"
        )
        ==
        "benchmark"
    )

    method_count = sum(
        1
        for paper in relevant_papers
        if paper.get(
            "evidence_category"
        )
        ==
        "method"
    )

    review_count = sum(
        1
        for paper in relevant_papers
        if paper.get(
            "evidence_category"
        )
        ==
        "review"
    )

    application_count = sum(
        1
        for paper in relevant_papers
        if paper.get(
            "evidence_category"
        )
        ==
        "application"
    )

    weak_count = sum(
        1
        for paper in papers
        if paper.get(
            "evidence_category"
        )
        ==
        "weak"
    )

    benchmark_points = min(
        benchmark_count
        *
        15,
        30
    )

    method_points = min(
        method_count
        *
        20,
        20
    )

    review_points = min(
        review_count
        *
        5,
        10
    )

    application_points = min(
        application_count
        *
        2,
        10
    )

    evidence_type_score = min(
        70,
        (
            benchmark_points
            +
            method_points
            +
            review_points
            +
            application_points
        )
    )

    recent_papers = [
        paper
        for paper in relevant_papers
        if (
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
            or
            (
                paper.get(
                    "year"
                )
                and
                paper.get(
                    "year"
                )
                >=
                current_year
                -
                5
            )
        )
    ]

    recent_count = len(
        recent_papers
    )

    if recent_count >= 5:

        recency_score = 10

    elif recent_count >= 3:

        recency_score = 8

    elif recent_count >= 1:

        recency_score = 5

    else:

        recency_score = 0

    providers = set()

    cross_source_paper_count = 0

    for paper in relevant_papers:

        paper_providers = set(
            paper.get(
                "source_providers",
                []
            )
            or
            []
        )

        providers.update(
            paper_providers
        )

        if len(
            paper_providers
        ) >= 2:

            cross_source_paper_count += 1

    provider_count = len(
        providers
    )

    if (
        provider_count
        >= 3
        and
        cross_source_paper_count
        >= 1
    ):

        source_confirmation_score = 10

    elif provider_count >= 2:

        source_confirmation_score = 7

    elif provider_count == 1:

        source_confirmation_score = 3

    else:

        source_confirmation_score = 0

    total_citations = sum(
        paper.get(
            "cited_by_count",
            0
        )
        or
        0
        for paper in relevant_papers
    )

    if total_citations >= 250:

        citation_score = 10

    elif total_citations >= 100:

        citation_score = 8

    elif total_citations >= 30:

        citation_score = 5

    elif total_citations >= 5:

        citation_score = 2

    else:

        citation_score = 0

    foundational_count = sum(
        1
        for paper in relevant_papers
        if "foundational"
        in
        (
            paper.get(
                "search_scopes",
                []
            )
            or
            []
        )
    )

    total_score = min(
        100,
        (
            evidence_type_score
            +
            recency_score
            +
            source_confirmation_score
            +
            citation_score
        )
    )

    return {
        "total": total_score,
        "evidence_type_score": evidence_type_score,
        "recency_score": recency_score,
        "source_confirmation_score": source_confirmation_score,
        "citation_score": citation_score,
        "benchmark_count": benchmark_count,
        "method_count": method_count,
        "review_count": review_count,
        "application_count": application_count,
        "weak_count": weak_count,
        "relevant_count": len(
            relevant_papers
        ),
        "recent_count": recent_count,
        "foundational_count": foundational_count,
        "provider_count": provider_count,
        "providers": sorted(
            providers
        ),
        "cross_source_paper_count": cross_source_paper_count,
        "total_citations": total_citations
    }


# ==================================================
# EVIDENCE USE IN RANKING
# ==================================================

def evidence_rank_signal(
    literature_score,
    available=True
):
    """
    Normalize a literature-support score for ranking.

    Evidence is a confidence / tie-breaker layer, not part of the
    BioFlow scientific recommendation score.

    A failed external search must not be treated as zero evidence.
    In that case `available=False` returns -1, which means
    "not evaluated" rather than "poor evidence".
    """

    if not available:

        return -1

    try:

        value = float(
            literature_score
        )

    except (
        TypeError,
        ValueError
    ):

        return -1

    return max(
        0,
        min(
            100,
            value
        )
    )


def calculate_evidence_adjusted_score(
    base_score,
    literature_score
):
    """
    Backward-compatible API.

    BioFlow scoring v2 no longer blends literature evidence into the
    recommendation score. Returning the base score keeps older callers
    from breaking while preventing literature availability/citation
    volume from silently changing scientific suitability.

    New code should use `evidence_rank_signal()` and display the
    literature evidence score separately.
    """

    try:

        return round(
            float(
                base_score
            ),
            1
        )

    except (
        TypeError,
        ValueError
    ):

        return 0.0

