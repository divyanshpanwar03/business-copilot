import operator

from models import BusinessProfileDB, ComplianceRule


OPERATORS = {
    ">=": operator.ge,
    ">": operator.gt,
    "<=": operator.le,
    "<": operator.lt,
    "==": operator.eq,
    "!=": operator.ne,
}


def convert_value(field_value, condition_value):
    if isinstance(field_value, bool):
        return field_value, condition_value.strip().lower() == "true"

    if isinstance(field_value, (int, float)):
        return field_value, float(condition_value)

    if isinstance(field_value, str):
        return field_value.strip().lower(), condition_value.strip().lower()

    return field_value, condition_value


def evaluate_rule(profile, rule):
    field_value = getattr(profile, rule.condition_field)

    operator_function = OPERATORS.get(rule.condition_operator)

    if operator_function is None:
        raise ValueError(
            f"Unsupported operator: {rule.condition_operator}"
        )

    field_value, condition_value = convert_value(
        field_value,
        rule.condition_value
    )

    return operator_function(
        field_value,
        condition_value
    )

def evaluate_condition(profile, condition):
    field_value = getattr(
        profile,
        condition.condition_field
    )

    operator_function = OPERATORS.get(
        condition.condition_operator
    )

    if operator_function is None:
        raise ValueError(
            f"Unsupported operator: "
            f"{condition.condition_operator}"
        )

    field_value, condition_value = convert_value(
        field_value,
        condition.condition_value
    )

    return operator_function(
        field_value,
        condition_value
    )

def get_applicable_rules(profile, rules):
    applicable_rules = []

    for rule in rules:

        condition_results = []

        for condition in rule.conditions:
            result = evaluate_condition(
                profile,
                condition
            )

            condition_results.append(result)

        if rule.condition_logic == "AND":
            rule_applies = all(condition_results)

        elif rule.condition_logic == "OR":
            rule_applies = any(condition_results)

        else:
            raise ValueError(
                f"Unsupported condition logic: "
                f"{rule.condition_logic}"
            )

        if rule_applies:
            applicable_rules.append(rule)

    return applicable_rules