from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import quote

import requests


BASE_URL = "https://api.ncbi.nlm.nih.gov/datasets/v2"
USER_AGENT = "OmicsRoute/1.2 (https://github.com/isilayc/omicsroute)"
ASSEMBLY_ACCESSION_RE = re.compile(
    r"^(GCF|GCA)_\d+\.\d+$",
    re.IGNORECASE
)


class NCBIReferenceError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }

    api_key = os.getenv("NCBI_API_KEY")
    if api_key:
        headers["api-key"] = api_key

    return headers


def _get_json(
    path: str,
    params: dict[str, Any] | None = None,
    timeout: int = 15,
) -> dict[str, Any]:
    url = f"{BASE_URL}{path}"

    try:
        response = requests.get(
            url,
            params=params or {},
            headers=_headers(),
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise NCBIReferenceError(
            f"NCBI Datasets could not be reached: {exc}"
        ) from exc

    if response.status_code == 429:
        raise NCBIReferenceError(
            "NCBI rate limit reached. Please wait briefly and try again."
        )

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise NCBIReferenceError(
            f"NCBI Datasets returned HTTP {response.status_code}."
        ) from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise NCBIReferenceError(
            "NCBI Datasets returned an unreadable response."
        ) from exc

    if not isinstance(payload, dict):
        raise NCBIReferenceError(
            "NCBI Datasets returned an unexpected response shape."
        )

    return payload


def parse_taxon_suggestions(
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    for item in payload.get("sci_name_and_ids", []) or []:
        if not isinstance(item, dict):
            continue

        tax_id = item.get("tax_id")
        scientific_name = item.get("sci_name")

        if not tax_id or not scientific_name:
            continue

        items.append(
            {
                "tax_id": int(tax_id),
                "scientific_name": str(scientific_name),
                "common_name": item.get("common_name") or "",
                "rank": item.get("rank") or "",
                "group_name": item.get("group_name") or "",
                "matched_term": item.get("matched_term") or "",
            }
        )

    if items:
        return items

    for report in payload.get("reports", []) or []:
        if not isinstance(report, dict):
            continue

        taxonomy = report.get("taxonomy", {}) or {}
        current_name = taxonomy.get(
            "current_scientific_name",
            {}
        ) or {}

        tax_id = taxonomy.get("tax_id")
        scientific_name = (
            taxonomy.get("organism_name")
            or current_name.get("name")
        )

        if not tax_id or not scientific_name:
            continue

        items.append(
            {
                "tax_id": int(tax_id),
                "scientific_name": str(scientific_name),
                "common_name": (
                    taxonomy.get("genbank_common_name")
                    or taxonomy.get("common_name")
                    or ""
                ),
                "rank": taxonomy.get("rank") or "",
                "group_name": taxonomy.get("group_name") or "",
                "matched_term": "",
            }
        )

    return items


def search_taxa(
    query: str,
    limit: int = 10,
) -> dict[str, Any]:
    query = str(query or "").strip()

    if len(query) < 2:
        return {
            "ok": False,
            "error": "Enter an organism name or NCBI Taxonomy ID.",
            "results": [],
        }

    try:
        if query.isdigit():
            payload = _get_json(
                f"/taxonomy/taxon/{quote(query, safe='')}/dataset_report"
            )
        else:
            payload = _get_json(
                f"/taxonomy/taxon_suggest/{quote(query, safe='')}"
            )

        results = parse_taxon_suggestions(payload)

    except NCBIReferenceError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "results": [],
        }

    query_lower = query.lower()

    def rank_key(item: dict[str, Any]):
        scientific = str(
            item.get("scientific_name") or ""
        ).lower()

        common = str(
            item.get("common_name") or ""
        ).lower()

        rank = str(
            item.get("rank") or ""
        ).lower()

        exact = (
            scientific == query_lower
            or common == query_lower
            or str(item.get("tax_id")) == query
        )

        species_like = rank in {
            "species",
            "subspecies",
            "strain",
            "varietas",
            "forma",
        }

        return (
            0 if exact else 1,
            0 if species_like else 1,
            scientific,
        )

    results = sorted(
        results,
        key=rank_key,
    )[:max(1, int(limit))]

    return {
        "ok": True,
        "error": "",
        "results": results,
    }


def normalise_assembly_report(
    report: dict[str, Any],
) -> dict[str, Any]:
    assembly_info = report.get(
        "assembly_info",
        {}
    ) or {}

    assembly_stats = report.get(
        "assembly_stats",
        {}
    ) or {}

    organism = report.get(
        "organism",
        {}
    ) or {}

    annotation_info = report.get(
        "annotation_info",
        {}
    ) or {}

    accession = (
        report.get("current_accession")
        or report.get("accession")
        or ""
    )

    refseq_category = (
        assembly_info.get("refseq_category")
        or report.get("refseq_category")
        or ""
    )

    category_lower = str(
        refseq_category
    ).lower()

    source_database = str(
        report.get("source_database")
        or ""
    )

    is_refseq = (
        str(accession).upper().startswith("GCF_")
        or "REFSEQ" in source_database.upper()
    )

    return {
        "accession": str(accession),
        "paired_accession": (
            report.get("paired_accession")
            or ""
        ),
        "assembly_name": (
            assembly_info.get("assembly_name")
            or str(accession)
        ),
        "assembly_level": (
            assembly_info.get("assembly_level")
            or ""
        ),
        "assembly_status": (
            assembly_info.get("assembly_status")
            or ""
        ),
        "refseq_category": str(refseq_category),
        "is_reference": (
            "reference genome" in category_lower
            or category_lower == "reference"
        ),
        "is_representative": (
            "representative" in category_lower
        ),
        "is_refseq": is_refseq,
        "source": (
            "RefSeq"
            if is_refseq
            else "GenBank"
        ),
        "organism_name": (
            organism.get("organism_name")
            or ""
        ),
        "common_name": (
            organism.get("common_name")
            or ""
        ),
        "tax_id": organism.get("tax_id"),
        "annotation_status": (
            annotation_info.get("status")
            or ""
        ),
        "annotation_name": (
            annotation_info.get("name")
            or ""
        ),
        "contig_n50": (
            assembly_stats.get("contig_n50")
            or 0
        ),
        "scaffold_n50": (
            assembly_stats.get("scaffold_n50")
            or 0
        ),
        "total_sequence_length": (
            assembly_stats.get("total_sequence_length")
            or 0
        ),
        "release_date": (
            assembly_info.get("release_date")
            or ""
        ),
    }


def _assembly_sort_key(
    item: dict[str, Any],
):
    level_order = {
        "complete genome": 0,
        "chromosome": 1,
        "scaffold": 2,
        "contig": 3,
    }

    level = str(
        item.get("assembly_level")
        or ""
    ).lower()

    try:
        n50 = int(
            item.get("contig_n50")
            or 0
        )
    except (TypeError, ValueError):
        n50 = 0

    return (
        0 if item.get("is_reference") else 1,
        0 if item.get("is_representative") else 1,
        0 if item.get("is_refseq") else 1,
        level_order.get(level, 9),
        0 if item.get("annotation_status") else 1,
        -n50,
        item.get("accession") or "",
    )


def parse_assembly_reports(
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for report in payload.get("reports", []) or []:
        if not isinstance(report, dict):
            continue

        normalised = normalise_assembly_report(
            report
        )

        if not normalised.get("accession"):
            continue

        status = str(
            normalised.get("assembly_status")
            or ""
        ).lower()

        if status and status not in {
            "current",
            "latest",
        }:
            continue

        results.append(
            normalised
        )

    return sorted(
        results,
        key=_assembly_sort_key,
    )


def _merge_assemblies(
    *groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}

    for group in groups:
        for item in group:
            accession = item.get("accession")
            if not accession:
                continue
            merged[str(accession)] = item

    return sorted(
        merged.values(),
        key=_assembly_sort_key,
    )


def search_genome_assemblies(
    tax_id: int | str,
    limit: int = 50,
) -> dict[str, Any]:
    tax_id = str(tax_id).strip()

    if not tax_id:
        return {
            "ok": False,
            "error": "A Taxonomy ID is required.",
            "assemblies": [],
            "status": "unresolved",
        }

    page_size = min(
        max(int(limit), 1),
        100,
    )

    base_path = (
        f"/genome/taxon/{quote(tax_id, safe='')}/dataset_report"
    )

    try:
        all_payload = _get_json(
            base_path,
            params={
                "page_size": page_size,
            },
        )

        all_assemblies = parse_assembly_reports(
            all_payload
        )

        reference_assemblies: list[dict[str, Any]] = []

        try:
            reference_payload = _get_json(
                base_path,
                params={
                    "page_size": 10,
                    "filters.reference_only": "true",
                },
            )

            reference_assemblies = parse_assembly_reports(
                reference_payload
            )

        except NCBIReferenceError:
            reference_assemblies = []

    except NCBIReferenceError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "assemblies": [],
            "status": "unresolved",
        }

    assemblies = _merge_assemblies(
        reference_assemblies,
        all_assemblies,
    )

    if not assemblies:
        status = "no_assembly"
    elif any(
        item.get("is_reference")
        for item in assemblies
    ):
        status = "reference_available"
    elif any(
        item.get("is_representative")
        for item in assemblies
    ):
        status = "representative_available"
    else:
        status = "assemblies_available"

    return {
        "ok": True,
        "error": "",
        "assemblies": assemblies[:page_size],
        "status": status,
    }


def lookup_assembly_accession(
    accession: str,
) -> dict[str, Any]:
    accession = str(
        accession or ""
    ).strip().upper()

    if not ASSEMBLY_ACCESSION_RE.match(
        accession
    ):
        return {
            "ok": False,
            "error": (
                "Use a versioned NCBI Assembly accession such as "
                "GCF_000001405.40 or GCA_000001405.29."
            ),
            "assembly": None,
        }

    try:
        payload = _get_json(
            f"/genome/accession/{quote(accession, safe='')}/dataset_report"
        )

        assemblies = parse_assembly_reports(
            payload
        )

    except NCBIReferenceError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "assembly": None,
        }

    if not assemblies:
        return {
            "ok": False,
            "error": (
                "NCBI did not return a current assembly for this accession."
            ),
            "assembly": None,
        }

    exact = next(
        (
            item
            for item in assemblies
            if item.get("accession", "").upper()
            == accession
        ),
        assemblies[0],
    )

    return {
        "ok": True,
        "error": "",
        "assembly": exact,
    }


def reference_context_from_assembly(
    assembly: dict[str, Any],
    *,
    taxon: dict[str, Any] | None = None,
    source_mode: str = "ncbi_search",
) -> dict[str, Any]:
    if not assembly:
        return {
            "status": "unresolved",
            "usable_reference": False,
        }

    if assembly.get("is_reference"):
        status = "ncbi_reference"
    else:
        status = "same_species_assembly"

    taxon = taxon or {}

    return {
        "status": status,
        "usable_reference": True,
        "source_mode": source_mode,
        "reference_accession": (
            assembly.get("accession")
            or ""
        ),
        "reference_name": (
            assembly.get("assembly_name")
            or ""
        ),
        "reference_level": (
            assembly.get("assembly_level")
            or ""
        ),
        "reference_source": (
            assembly.get("source")
            or ""
        ),
        "reference_category": (
            assembly.get("refseq_category")
            or ""
        ),
        "organism_name": (
            assembly.get("organism_name")
            or taxon.get("scientific_name")
            or ""
        ),
        "common_name": (
            assembly.get("common_name")
            or taxon.get("common_name")
            or ""
        ),
        "tax_id": (
            assembly.get("tax_id")
            or taxon.get("tax_id")
        ),
        "taxon_rank": (
            taxon.get("rank")
            or ""
        ),
    }
