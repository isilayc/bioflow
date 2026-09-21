from pathlib import Path
import yaml


ENGINE_DIR = Path(__file__).resolve().parent
APP_DIR = ENGINE_DIR.parent
REFERENCE_FILE = APP_DIR / "data" / "reference_profiles.yaml"

_cache = {
    "signature": None,
    "data": {}
}


def _signature(path):
    if not path.exists():
        return None

    stat = path.stat()

    return (
        stat.st_mtime_ns,
        stat.st_size
    )


def load_reference_profiles():
    signature = _signature(
        REFERENCE_FILE
    )

    if (
        _cache[
            "signature"
        ]
        ==
        signature
    ):
        return _cache[
            "data"
        ]

    if not REFERENCE_FILE.exists():
        data = {}
    else:
        with open(
            REFERENCE_FILE,
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

    _cache[
        "signature"
    ] = signature

    _cache[
        "data"
    ] = data

    return data


def get_scope_options(goal):
    profiles = load_reference_profiles()
    goal_profile = (
        profiles.get(
            goal,
            {}
        )
        or
        {}
    )

    scopes = (
        goal_profile.get(
            "scopes",
            {}
        )
        or
        {}
    )

    return [
        {
            "id": scope_id,
            "label": (
                scope_record.get(
                    "label"
                )
                or
                scope_id
            )
        }
        for scope_id, scope_record
        in scopes.items()
    ]


def get_default_scope(goal):
    profiles = load_reference_profiles()
    goal_profile = (
        profiles.get(
            goal,
            {}
        )
        or
        {}
    )

    return goal_profile.get(
        "default_scope"
    )


def get_scope_label(goal):
    profiles = load_reference_profiles()
    goal_profile = (
        profiles.get(
            goal,
            {}
        )
        or
        {}
    )

    return (
        goal_profile.get(
            "label"
        )
        or
        "Taxonomic scope"
    )


def get_reference_guidance(
    goal,
    workflow_id,
    scope_id=None
):
    profiles = load_reference_profiles()

    goal_profile = (
        profiles.get(
            goal,
            {}
        )
        or
        {}
    )

    if not goal_profile:
        return None

    scopes = (
        goal_profile.get(
            "scopes",
            {}
        )
        or
        {}
    )

    if (
        scope_id
        not in scopes
    ):
        scope_id = (
            goal_profile.get(
                "default_scope"
            )
        )

    scope_record = (
        scopes.get(
            scope_id,
            {}
        )
        or
        {}
    )

    route_record = (
        (
            goal_profile.get(
                "route_overrides",
                {}
            )
            or
            {}
        ).get(
            workflow_id,
            {}
        )
        or
        {}
    )

    status = (
        (
            route_record.get(
                "scope_status",
                {}
            )
            or
            {}
        ).get(
            scope_id
        )
        or
        route_record.get(
            "status"
        )
        or
        "supported"
    )

    scope_specific_notes = (
        (
            route_record.get(
                "scope_notes",
                {}
            )
            or
            {}
        ).get(
            scope_id,
            []
        )
        or
        []
    )

    return {
        "scope_id": scope_id,
        "scope_label": (
            scope_record.get(
                "label"
            )
            or
            scope_id
        ),
        "status": status,
        "preferred_database": (
            route_record.get(
                "preferred_database"
            )
            or
            scope_record.get(
                "preferred_database"
            )
        ),
        "alternatives": (
            scope_record.get(
                "alternatives",
                []
            )
            or
            []
        ),
        "avoid": (
            scope_record.get(
                "avoid",
                []
            )
            or
            []
        ),
        "scope_notes": (
            scope_record.get(
                "notes",
                []
            )
            or
            []
        ),
        "route_recommendation": route_record.get(
            "recommendation"
        ),
        "important": (
            route_record.get(
                "important",
                []
            )
            or
            []
        )
        +
        scope_specific_notes
    }
