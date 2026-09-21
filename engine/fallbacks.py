from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
FALLBACKS_FILE = DATA_DIR / "fallbacks.yaml"
WORKFLOWS_FILE = DATA_DIR / "workflows.yaml"


@lru_cache(maxsize=1)
def load_fallbacks() -> Dict[str, Any]:
    if not FALLBACKS_FILE.exists():
        return {"schema_version": 1, "rules": []}

    with FALLBACKS_FILE.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        return {"schema_version": 1, "rules": []}

    data.setdefault("schema_version", 1)
    data.setdefault("rules", [])
    return data


@lru_cache(maxsize=1)
def load_workflows_for_fallbacks() -> Dict[str, Any]:
    if not WORKFLOWS_FILE.exists():
        return {}

    with WORKFLOWS_FILE.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    return data if isinstance(data, dict) else {}


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _step_candidates(step: Dict[str, Any]) -> List[str]:
    candidates = _as_list(step.get("candidates"))
    if candidates:
        return [str(x) for x in candidates if x]

    values: List[str] = []
    preferred = step.get("preferred")
    if preferred:
        values.append(str(preferred))

    values.extend(str(x) for x in _as_list(step.get("alternatives")) if x)

    seen: Set[str] = set()
    output: List[str] = []
    for tool_id in values:
        if tool_id not in seen:
            seen.add(tool_id)
            output.append(tool_id)
    return output


def get_recovery_rule(tool_id: str, operation: Optional[str] = None) -> Optional[Dict[str, Any]]:
    rules = load_fallbacks().get("rules", [])
    if not isinstance(rules, list):
        return None

    for rule in rules:
        if not isinstance(rule, dict):
            continue
        if str(rule.get("tool_id", "")) != str(tool_id):
            continue

        operations = [str(x) for x in _as_list(rule.get("operations")) if x is not None]
        if operations and operation not in operations:
            continue
        return rule

    return None


def _core_context_matches(current_context: Dict[str, Any], candidate_context: Dict[str, Any]) -> bool:
    # Only biological/user-facing context is matched here. Route-specific
    # metadata is deliberately ignored because that is what may need to change.
    keys = ["sample_type", "sequencing", "read_type", "goal"]
    if current_context.get("marker") is not None:
        keys.append("marker")

    for key in keys:
        current = current_context.get(key)
        if current is None:
            continue
        if candidate_context.get(key) != current:
            return False
    return True


def _workflow_uses_any_tool(workflow: Dict[str, Any], blocked_tool_ids: Set[str]) -> bool:
    if not blocked_tool_ids:
        return False

    for step in workflow.get("steps", []) or []:
        if not isinstance(step, dict):
            continue
        if blocked_tool_ids.intersection(_step_candidates(step)):
            return True
    return False


def find_alternative_strategies(
    workflow: Dict[str, Any],
    blocked_tool_ids: List[str],
    limit: int = 6,
) -> List[Dict[str, Any]]:
    current_id = str(workflow.get("id", ""))
    current_context = workflow.get("context", {}) or {}
    blocked = {str(x) for x in blocked_tool_ids if x}

    matches: List[Dict[str, Any]] = []
    for workflow_id, candidate in load_workflows_for_fallbacks().items():
        if not isinstance(candidate, dict):
            continue
        if str(workflow_id) == current_id:
            continue

        candidate_context = candidate.get("context", {}) or {}
        if not _core_context_matches(current_context, candidate_context):
            continue

        # Do not suggest a route that still depends on the same blocked tool.
        if _workflow_uses_any_tool(candidate, blocked):
            continue

        matches.append(
            {
                "id": workflow_id,
                "name": candidate.get("name", workflow_id),
                "description": candidate.get("description", ""),
            }
        )

    return matches[: max(1, int(limit))]


def resolve_step_recovery(
    workflow: Dict[str, Any],
    step: Dict[str, Any],
    blocked_tool_ids: List[str],
) -> Dict[str, Any]:
    operation = step.get("operation")
    blocked = [str(x) for x in blocked_tool_ids if x]

    strategy_search_allowed = False
    direct_tool_ids: List[str] = []
    remediations: List[Dict[str, str]] = []

    for tool_id in blocked:
        rule = get_recovery_rule(tool_id, operation)
        if not rule:
            continue

        strategy_search_allowed = strategy_search_allowed or bool(
            rule.get("allow_strategy_search", False)
        )

        for alt in _as_list(rule.get("direct_tool_ids")):
            alt = str(alt)
            if alt and alt not in direct_tool_ids:
                direct_tool_ids.append(alt)

        remediation = rule.get("remediation")
        if remediation:
            remediations.append(
                {
                    "tool_id": tool_id,
                    "title": str(rule.get("title", f"Resolve {tool_id} requirements")),
                    "message": str(remediation),
                    "fallback_note": str(rule.get("fallback_note", "")),
                }
            )

    strategies: List[Dict[str, Any]] = []
    if strategy_search_allowed:
        strategies = find_alternative_strategies(workflow, blocked)

    return {
        "operation": operation,
        "blocked_tool_ids": blocked,
        "direct_tool_ids": direct_tool_ids,
        "strategies": strategies,
        "remediations": remediations,
    }
