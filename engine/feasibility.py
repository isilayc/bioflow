from pathlib import Path
import os

import yaml


# ==================================================
# PATHS / CACHE
# ==================================================

ENGINE_DIR = (
    Path(__file__)
    .resolve()
    .parent
)

APP_DIR = (
    ENGINE_DIR
    .parent
)

DATA_DIR = (
    APP_DIR
    / "data"
)

OPERATIONAL_FILE = (
    DATA_DIR
    / "operational.yaml"
)

_operational_cache = {
    "signature": None,
    "data": {}
}


def _file_signature(filepath):
    """
    Return a simple mtime/size signature for cache invalidation.
    """

    if not filepath.exists():

        return None

    stat = filepath.stat()

    return (
        stat.st_mtime_ns,
        stat.st_size
    )


def load_operational_metadata():
    """
    Load curated operational feasibility metadata.

    Missing data/operational.yaml is intentionally allowed so
    BioFlow can continue to run while this catalogue is being built.
    """

    signature = (
        _file_signature(
            OPERATIONAL_FILE
        )
    )

    if (
        _operational_cache[
            "signature"
        ]
        ==
        signature
    ):

        return (
            _operational_cache[
                "data"
            ]
        )

    if not OPERATIONAL_FILE.exists():

        data = {}

    else:

        with open(
            OPERATIONAL_FILE,
            "r",
            encoding="utf-8"
        ) as handle:

            data = (
                yaml.safe_load(
                    handle
                )
                or
                {}
            )

    if not isinstance(
        data,
        dict
    ):

        data = {}

    _operational_cache[
        "signature"
    ] = signature

    _operational_cache[
        "data"
    ] = data

    return data


# ==================================================
# NORMALIZATION
# ==================================================

def normalize(value):
    """
    Normalize free text for internal comparisons.
    """

    if value is None:

        return ""

    return (
        str(value)
        .strip()
        .lower()
    )


def normalize_os(value):
    """
    Normalize operating-system labels used by the UI/YAML.
    """

    value = normalize(
        value
    )

    aliases = {
        "windows": "windows",
        "win": "windows",
        "linux": "linux",
        "mac": "macos",
        "macos": "macos",
        "mac os": "macos",
        "osx": "macos"
    }

    return aliases.get(
        value,
        value
    )


def _as_list(value):
    """
    Normalize a scalar/list YAML field to a list.
    """

    if value is None:

        return []

    if isinstance(
        value,
        list
    ):

        return value

    return [
        value
    ]


def _safe_number(value):
    """
    Convert an optional numeric input safely.
    """

    if value in (
        None,
        ""
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


# ==================================================
# PROFILE HELPERS
# ==================================================

def operational_status_priority(status):
    """
    Priority used only for ranking after technical dependency status.

    Scientific score is intentionally kept separate.
    """

    priorities = {
        "good": 4,
        "warning": 3,
        "unknown": 2,
        "blocked": 1,
        "not_evaluated": 3
    }

    return priorities.get(
        normalize(status),
        2
    )


def _demand_warning_threshold(
    demand,
    resource_type
):
    """
    Conservative heuristic thresholds.

    These are not vendor minimum requirements. They are only used
    to flag likely local-compute friction when a tool has qualitative
    resource metadata but no defensible fixed minimum.
    """

    demand = normalize(
        demand
    )

    thresholds = {
        "ram": {
            "low": 4,
            "moderate": 8,
            "high": 24,
            "very_high": 48
        },
        "disk": {
            "low": 10,
            "moderate": 25,
            "high": 100,
            "very_high": 250
        },
        "cpu": {
            "low": 2,
            "moderate": 4,
            "high": 8,
            "very_high": 16
        }
    }

    return (
        thresholds
        .get(
            resource_type,
            {}
        )
        .get(
            demand
        )
    )


# ==================================================
# EVALUATION
# ==================================================

def evaluate_operational_feasibility(
    tool,
    user_profile,
    operation=None
):
    """
    Evaluate whether a tool is practical for the user's environment.

    This function deliberately keeps operational feasibility separate
    from BioFlow's scientific/support score. It can affect display
    ranking, but it does not silently rewrite scientific suitability.

    Returned status:
      good
      warning
      blocked
      unknown
      not_evaluated
    """

    if not isinstance(
        tool,
        dict
    ):

        return {
            "status": "unknown",
            "score": None,
            "metadata_found": False,
            "profile_enabled": False,
            "reasons": [],
            "warnings": [],
            "blockers": [],
            "details": {}
        }

    if not isinstance(
        user_profile,
        dict
    ):

        user_profile = {}

    profile_enabled = bool(
        user_profile.get(
            "enabled",
            False
        )
    )

    tool_id = (
        tool.get(
            "id"
        )
        or
        tool.get(
            "tool_id"
        )
        or
        ""
    )

    catalogue = (
        load_operational_metadata()
    )

    metadata = (
        catalogue.get(
            tool_id,
            {}
        )
    )

    if not profile_enabled:

        return {
            "status": "not_evaluated",
            "score": None,
            "metadata_found": bool(
                metadata
            ),
            "profile_enabled": False,
            "reasons": [],
            "warnings": [],
            "blockers": [],
            "details": metadata
        }

    if not isinstance(
        metadata,
        dict
    ) or not metadata:

        return {
            "status": "unknown",
            "score": 50,
            "metadata_found": False,
            "profile_enabled": True,
            "reasons": [
                "No curated operational metadata is available for this tool yet."
            ],
            "warnings": [],
            "blockers": [],
            "details": {}
        }

    blockers = []
    warnings = []
    reasons = []

    platform = (
        metadata.get(
            "platform",
            {}
        )
        or
        {}
    )

    compute = (
        metadata.get(
            "compute",
            {}
        )
        or
        {}
    )

    database = (
        metadata.get(
            "database",
            {}
        )
        or
        {}
    )

    service = (
        metadata.get(
            "service",
            {}
        )
        or
        {}
    )

    user_os = (
        normalize_os(
            user_profile.get(
                "operating_system"
            )
        )
    )

    native_platforms = [
        normalize_os(
            value
        )
        for value
        in _as_list(
            platform.get(
                "native"
            )
        )
    ]

    if (
        user_os
        and
        native_platforms
        and
        user_os
        not in
        native_platforms
    ):

        windows_wsl_route = (
            user_os
            ==
            "windows"
            and
            bool(
                platform.get(
                    "windows_via_wsl",
                    False
                )
            )
            and
            bool(
                user_profile.get(
                    "wsl_available",
                    False
                )
            )
        )

        container_route = (
            bool(
                platform.get(
                    "container_route",
                    False
                )
            )
            and
            bool(
                user_profile.get(
                    "container_available",
                    False
                )
            )
        )

        hpc_route = bool(
            user_profile.get(
                "hpc_available",
                False
            )
        )

        if windows_wsl_route:

            warnings.append(
                "No native Windows route is curated; WSL can provide a practical Linux execution route."
            )

        elif container_route:

            warnings.append(
                "The selected operating system is not a curated native target, but a container route is available."
            )

        elif hpc_route:

            warnings.append(
                "Local native execution is not curated for this operating system; an HPC/cloud environment can be used instead."
            )

        else:

            blockers.append(
                "The selected operating system is not a curated native target and no WSL/container/HPC fallback is available."
            )

    if bool(
        compute.get(
            "gpu_required",
            False
        )
    ) and not bool(
        user_profile.get(
            "gpu_available",
            False
        )
    ):

        blockers.append(
            "A compatible GPU is required but the current compute profile has no GPU available."
        )

    elif (
        compute.get(
            "gpu_required"
        )
        is False
    ):

        reasons.append(
            "GPU is not required."
        )

    ram_gb = (
        _safe_number(
            user_profile.get(
                "ram_gb"
            )
        )
    )

    ram_minimum = (
        _safe_number(
            compute.get(
                "ram_minimum_gb"
            )
        )
    )

    ram_recommended = (
        _safe_number(
            compute.get(
                "ram_recommended_gb"
            )
        )
    )

    ram_demand = normalize(
        compute.get(
            "memory_demand"
        )
    )

    if (
        ram_gb
        is not None
        and
        ram_minimum
        is not None
        and
        ram_gb
        <
        ram_minimum
    ):

        blockers.append(
            f"Available RAM ({ram_gb:g} GB) is below the curated minimum ({ram_minimum:g} GB)."
        )

    elif (
        ram_gb
        is not None
        and
        ram_recommended
        is not None
        and
        ram_gb
        <
        ram_recommended
    ):

        warnings.append(
            f"Available RAM ({ram_gb:g} GB) is below the curated recommended level ({ram_recommended:g} GB)."
        )

    elif (
        ram_gb
        is not None
        and
        ram_minimum
        is None
        and
        ram_recommended
        is None
    ):

        threshold = (
            _demand_warning_threshold(
                ram_demand,
                "ram"
            )
        )

        if (
            threshold
            is not None
            and
            ram_gb
            <
            threshold
        ):

            warnings.append(
                f"Memory demand is curated as '{ram_demand}'. "
                f"{ram_gb:g} GB RAM may be restrictive for some datasets "
                "(heuristic warning, not a vendor minimum)."
            )

    disk_gb = (
        _safe_number(
            user_profile.get(
                "free_disk_gb"
            )
        )
    )

    disk_minimum = (
        _safe_number(
            compute.get(
                "disk_minimum_gb"
            )
        )
    )

    disk_recommended = (
        _safe_number(
            compute.get(
                "disk_recommended_gb"
            )
        )
    )

    disk_demand = normalize(
        compute.get(
            "disk_demand"
        )
    )

    if (
        disk_gb
        is not None
        and
        disk_minimum
        is not None
        and
        disk_gb
        <
        disk_minimum
    ):

        blockers.append(
            f"Free disk space ({disk_gb:g} GB) is below the curated minimum ({disk_minimum:g} GB)."
        )

    elif (
        disk_gb
        is not None
        and
        disk_recommended
        is not None
        and
        disk_gb
        <
        disk_recommended
    ):

        warnings.append(
            f"Free disk space ({disk_gb:g} GB) is below the curated recommended level ({disk_recommended:g} GB)."
        )

    elif (
        disk_gb
        is not None
        and
        disk_minimum
        is None
        and
        disk_recommended
        is None
    ):

        threshold = (
            _demand_warning_threshold(
                disk_demand,
                "disk"
            )
        )

        if (
            threshold
            is not None
            and
            disk_gb
            <
            threshold
        ):

            warnings.append(
                f"Disk demand is curated as '{disk_demand}'. "
                f"{disk_gb:g} GB free space may be restrictive "
                "(heuristic warning, not a vendor minimum)."
            )

    cpu_cores = (
        _safe_number(
            user_profile.get(
                "cpu_cores"
            )
        )
    )

    cpu_demand = normalize(
        compute.get(
            "cpu_demand"
        )
    )

    if cpu_cores is not None:

        cpu_threshold = (
            _demand_warning_threshold(
                cpu_demand,
                "cpu"
            )
        )

        if (
            cpu_threshold
            is not None
            and
            cpu_cores
            <
            cpu_threshold
        ):

            warnings.append(
                f"CPU demand is curated as '{cpu_demand}'. "
                f"{cpu_cores:g} cores may result in slow execution."
            )

    dataset_scale = normalize(
        user_profile.get(
            "dataset_scale"
        )
    )

    scaling = normalize(
        compute.get(
            "dataset_scaling"
        )
    )

    if (
        dataset_scale
        in (
            "large",
            "very large"
        )
        and
        scaling
        in (
            "high",
            "very_high",
            "very high"
        )
        and
        not bool(
            user_profile.get(
                "hpc_available",
                False
            )
        )
    ):

        warnings.append(
            "Resource use scales strongly with dataset size; large datasets may be impractical on a local workstation."
        )

    if bool(
        database.get(
            "required",
            False
        )
    ):

        footprint = normalize(
            database.get(
                "footprint"
            )
        )

        if (
            footprint
            in (
                "high",
                "very_high",
                "very high",
                "variable_high",
                "variable high"
            )
            and
            not bool(
                user_profile.get(
                    "large_database_ok",
                    False
                )
            )
        ):

            warnings.append(
                "This workflow depends on a large or database-dependent reference footprint, but the compute profile marks large database downloads/storage as undesirable."
            )

        if bool(
            database.get(
                "memory_resident_default",
                False
            )
        ):

            reasons.append(
                "Database memory footprint can materially affect RAM requirements."
            )

    internet_mode = normalize(
        user_profile.get(
            "internet"
        )
    )

    if (
        bool(
            metadata.get(
                "large_downloads",
                False
            )
        )
        and
        internet_mode
        ==
        "limited"
    ):

        warnings.append(
            "The tool or its reference data may require large downloads, which conflicts with the selected limited-internet profile."
        )

    if bool(
        service.get(
            "online_only",
            False
        )
    ) and not bool(
        user_profile.get(
            "web_services_allowed",
            True
        )
    ):

        blockers.append(
            "This is an online-only service, but the compute profile does not allow web-service execution."
        )

    if blockers:

        status = (
            "blocked"
        )

        score = 0

    elif warnings:

        status = (
            "warning"
        )

        score = max(
            40,
            100
            -
            (
                12
                *
                len(
                    warnings
                )
            )
        )

    else:

        status = (
            "good"
        )

        score = 100

    return {
        "status": status,
        "score": score,
        "metadata_found": True,
        "profile_enabled": True,
        "reasons": reasons,
        "warnings": warnings,
        "blockers": blockers,
        "details": metadata,
        "operation": operation
    }
