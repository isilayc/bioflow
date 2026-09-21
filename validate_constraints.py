from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys
import yaml

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CONSTRAINTS_FILE = DATA_DIR / "constraints.yaml"
TOOLS_FILE = DATA_DIR / "tools.yaml"
WORKFLOWS_FILE = DATA_DIR / "workflows.yaml"

ALLOWED_FIELD_TYPES = {"boolean", "integer", "float", "string", "choice", "enum"}
ALLOWED_RULE_KINDS = {"required", "equals", "numeric_min", "numeric_max", "one_of", "sum_minus_min"}
ALLOWED_SEVERITIES = {"warning", "block"}
CONTEXT_FIELDS = {"sample_type", "sequencing", "read_type", "goal", "operation"}


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"duplicate key: {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def load_unique(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.load(handle, Loader=UniqueKeyLoader)


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def validate_definition(scope_name, item_id, definition, known_context, errors, warnings):
    prefix = f"{scope_name}.{item_id}"
    if not isinstance(definition, dict):
        errors.append(f"{prefix}: definition must be a mapping")
        return

    fields = definition.get("fields", {}) or {}
    rules = definition.get("rules", []) or []

    if not isinstance(fields, dict):
        errors.append(f"{prefix}.fields must be a mapping")
        fields = {}
    if not isinstance(rules, list):
        errors.append(f"{prefix}.rules must be a list")
        rules = []

    for field_id, field_def in fields.items():
        fp = f"{prefix}.fields.{field_id}"
        if not isinstance(field_def, dict):
            errors.append(f"{fp}: field definition must be a mapping")
            continue
        field_type = field_def.get("type", "string")
        if field_type not in ALLOWED_FIELD_TYPES:
            errors.append(f"{fp}: unsupported type {field_type!r}")
        if field_type in {"choice", "enum"}:
            options = field_def.get("options")
            if not isinstance(options, list) or not options:
                errors.append(f"{fp}: choice/enum field requires a non-empty options list")

    local_rule_ids = []
    available_fields = set(fields) | set(known_context)

    def require_known_field(rule_prefix, field_name):
        if not field_name:
            errors.append(f"{rule_prefix}: missing field reference")
        elif field_name not in available_fields:
            errors.append(f"{rule_prefix}: references undefined field {field_name!r}")

    for index, rule in enumerate(rules, start=1):
        rp = f"{prefix}.rules[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{rp}: rule must be a mapping")
            continue

        rule_id = rule.get("id")
        if not rule_id:
            errors.append(f"{rp}: rule id is required")
        else:
            local_rule_ids.append(rule_id)

        kind = rule.get("kind")
        if kind not in ALLOWED_RULE_KINDS:
            errors.append(f"{rp}: unsupported kind {kind!r}")
            continue

        severity = rule.get("severity", "warning")
        if severity not in ALLOWED_SEVERITIES:
            errors.append(f"{rp}: severity must be warning or block, got {severity!r}")

        when = rule.get("when")
        if when is not None:
            if not isinstance(when, dict):
                errors.append(f"{rp}.when must be a mapping")
            else:
                for field_name in when:
                    if field_name not in available_fields:
                        errors.append(f"{rp}.when references undefined/context field {field_name!r}")

        if kind == "required":
            refs = as_list(rule.get("fields"))
            if not refs and rule.get("field"):
                refs = [rule.get("field")]
            if not refs:
                errors.append(f"{rp}: required rule needs field or fields")
            for field_name in refs:
                require_known_field(rp, field_name)

        elif kind in {"equals", "numeric_min", "numeric_max", "one_of"}:
            require_known_field(rp, rule.get("field"))
            if kind == "equals" and "expected" not in rule:
                errors.append(f"{rp}: equals rule requires expected")
            if kind == "numeric_min" and "min_value" not in rule:
                errors.append(f"{rp}: numeric_min rule requires min_value")
            if kind == "numeric_max" and "max_value" not in rule:
                errors.append(f"{rp}: numeric_max rule requires max_value")
            if kind == "one_of":
                allowed = rule.get("allowed")
                if not isinstance(allowed, list) or not allowed:
                    errors.append(f"{rp}: one_of rule requires non-empty allowed list")

        elif kind == "sum_minus_min":
            refs = as_list(rule.get("fields"))
            if not refs:
                errors.append(f"{rp}: sum_minus_min requires fields")
            for field_name in refs:
                require_known_field(rp, field_name)
            require_known_field(rp, rule.get("subtract_field"))
            if "min_value" not in rule:
                errors.append(f"{rp}: sum_minus_min requires min_value")

    duplicates = sorted(k for k, count in Counter(local_rule_ids).items() if count > 1)
    for rule_id in duplicates:
        errors.append(f"{prefix}: duplicate rule id {rule_id!r} within the same definition")


def validate_constraints(verbose=True):
    errors = []
    warnings = []

    for path in (CONSTRAINTS_FILE, TOOLS_FILE, WORKFLOWS_FILE):
        if not path.exists():
            errors.append(f"Missing required file: {path}")

    if errors:
        return errors, warnings

    try:
        constraints = load_unique(CONSTRAINTS_FILE) or {}
    except Exception as exc:
        return [f"constraints.yaml failed strict YAML parsing: {exc}"], warnings

    try:
        tools_catalog = load_unique(TOOLS_FILE) or {}
    except Exception as exc:
        return [f"tools.yaml failed strict YAML parsing: {exc}"], warnings

    try:
        workflows_catalog = load_unique(WORKFLOWS_FILE) or {}
    except Exception as exc:
        return [f"workflows.yaml failed strict YAML parsing: {exc}"], warnings

    if not isinstance(constraints, dict):
        return ["constraints.yaml root must be a mapping"], warnings

    if constraints.get("schema_version") != 1:
        warnings.append(f"Unexpected schema_version: {constraints.get('schema_version')!r} (expected 1)")

    allowed_root = {"schema_version", "tools", "workflow_constraints"}
    unknown_root = sorted(set(constraints) - allowed_root)
    for key in unknown_root:
        warnings.append(f"Unknown top-level constraints key: {key!r}")

    tool_constraints = constraints.get("tools", {}) or {}
    workflow_constraints = constraints.get("workflow_constraints", {}) or {}

    if not isinstance(tool_constraints, dict):
        errors.append("constraints.tools must be a mapping")
        tool_constraints = {}
    if not isinstance(workflow_constraints, dict):
        errors.append("constraints.workflow_constraints must be a mapping")
        workflow_constraints = {}

    known_tool_ids = set(tools_catalog) if isinstance(tools_catalog, dict) else set()
    known_workflow_ids = set(workflows_catalog) if isinstance(workflows_catalog, dict) else set()

    for tool_id, definition in tool_constraints.items():
        if tool_id not in known_tool_ids:
            errors.append(f"tools.{tool_id}: constraint tool id is not present in data/tools.yaml")
        validate_definition("tools", tool_id, definition, CONTEXT_FIELDS, errors, warnings)

    for workflow_id, definition in workflow_constraints.items():
        if workflow_id not in known_workflow_ids:
            errors.append(f"workflow_constraints.{workflow_id}: id is not present in data/workflows.yaml")
        validate_definition("workflow_constraints", workflow_id, definition, CONTEXT_FIELDS, errors, warnings)

    # Detect common scope-placement mistakes explicitly.
    for item_id in workflow_constraints:
        if item_id in known_tool_ids and item_id not in known_workflow_ids:
            errors.append(
                f"workflow_constraints.{item_id}: looks like a tool id; move this block under top-level tools:"
            )
    for item_id in tool_constraints:
        if item_id in known_workflow_ids and item_id not in known_tool_ids:
            errors.append(
                f"tools.{item_id}: looks like a workflow id; move this block under workflow_constraints:"
            )

    if verbose:
        print("=" * 72)
        print("BioFlow constraints structural validation")
        print("=" * 72)
        print(f"Tool constraints:     {len(tool_constraints)}")
        print(f"Workflow constraints: {len(workflow_constraints)}")
        print(f"Errors:               {len(errors)}")
        print(f"Warnings:             {len(warnings)}")
        if warnings:
            print("\nWARNINGS")
            for warning in warnings:
                print(f"  - {warning}")
        if errors:
            print("\nERRORS")
            for error in errors:
                print(f"  - {error}")
        print("\nRESULT:", "PASS" if not errors else "FAIL")

    return errors, warnings


if __name__ == "__main__":
    errors, _warnings = validate_constraints(verbose=True)
    sys.exit(1 if errors else 0)
