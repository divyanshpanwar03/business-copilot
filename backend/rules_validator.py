from datetime import date

from models import BusinessProfileDB


SUPPORTED_OPERATORS = {
    ">=",
    ">",
    "<=",
    "<",
    "==",
    "!="
}

SUPPORTED_LOGIC = {
    "AND",
    "OR"
}

SUPPORTED_FIELDS = {
    "business_name",
    "entity_type",
    "location",
    "industry",
    "annual_turnover",
    "employee_count",
    "gst_registered"
}


def validate_rule(rule_data):
    errors = []

    required_fields = [
        "name",
        "description",
        "category",
        "priority",
        "frequency",
        "condition_logic",
        "obligation",
        "source",
        "conditions"
    ]

    for field in required_fields:
        if field not in rule_data:
            errors.append(
                f"Missing required field: {field}"
            )

    if errors:
        return errors

    if rule_data["condition_logic"] not in SUPPORTED_LOGIC:
        errors.append(
            f"Unsupported condition logic: "
            f"{rule_data['condition_logic']}"
        )

    if not isinstance(rule_data["conditions"], list):
        errors.append(
            "conditions must be a list"
        )
    elif len(rule_data["conditions"]) == 0:
        errors.append(
            "Rule must contain at least one condition"
        )

    for index, condition in enumerate(
        rule_data["conditions"],
        start=1
    ):
        if "field" not in condition:
            errors.append(
                f"Condition {index}: missing field"
            )

        if "operator" not in condition:
            errors.append(
                f"Condition {index}: missing operator"
            )

        if "value" not in condition:
            errors.append(
                f"Condition {index}: missing value"
            )

        if (
            "field" in condition
            and condition["field"] not in SUPPORTED_FIELDS
        ):
            errors.append(
                f"Condition {index}: unsupported field "
                f"{condition['field']}"
            )

        if (
            "operator" in condition
            and condition["operator"]
            not in SUPPORTED_OPERATORS
        ):
            errors.append(
                f"Condition {index}: unsupported operator "
                f"{condition['operator']}"
            )

    if (
        "effective_from" in rule_data
        and rule_data["effective_from"]
    ):
        try:
            date.fromisoformat(
                rule_data["effective_from"]
            )
        except ValueError:
            errors.append(
                "effective_from must use YYYY-MM-DD format"
            )

    if (
        "effective_to" in rule_data
        and rule_data["effective_to"]
    ):
        try:
            date.fromisoformat(
                rule_data["effective_to"]
            )
        except ValueError:
            errors.append(
                "effective_to must use YYYY-MM-DD format"
            )

    if (
        rule_data.get("effective_from")
        and rule_data.get("effective_to")
    ):
        start_date = date.fromisoformat(
            rule_data["effective_from"]
        )

        end_date = date.fromisoformat(
            rule_data["effective_to"]
        )

        if end_date < start_date:
            errors.append(
                "effective_to cannot be before effective_from"
            )

    if not rule_data["source"].strip():
        errors.append(
            "source cannot be empty"
        )

    return errors