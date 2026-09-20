from database import SessionLocal
from models import BusinessProfileDB, ComplianceRule
import operator

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
    field_value, condition_value = convert_value(field_value, rule.condition_value)

    return operator_function(
        field_value,
        condition_value
    )

db = SessionLocal()

profile = db.get(BusinessProfileDB, 1)
rules = db.query(ComplianceRule).all()

applicable_rules = []

for rule in rules:
    result = evaluate_rule(profile, rule)

    if result:
        applicable_rules.append(rule)

print("Applicable obligations:")

for rule in applicable_rules:
    print("-", rule.obligation)

db.close()