from database import SessionLocal
from models import ComplianceRule, RuleCondition


RULES = [
    {
        "name": "Employee Compliance Rule",
        "description": (
            "Applies when the business is a Private Limited company "
            "with 100 or more employees"
        ),
        "obligation": "Example employee-related compliance obligation",
        "source": "Dummy source for development",
        "conditions": [
            {
                "field": "employee_count",
                "operator": ">=",
                "value": "100"
            },
            {
                "field": "entity_type",
                "operator": "==",
                "value": "Private Limited"
            }
        ]
    },
    {
        "name": "GST Registration Rule",
        "description": "Applies to businesses registered under GST",
        "obligation": "Example GST compliance obligation",
        "source": "GST Portal",
        "conditions": [
            {
                "field": "gst_registered",
                "operator": "==",
                "value": "true"
            }
        ]
    }
]


db = SessionLocal()

try:
    for rule_data in RULES:
        rule = ComplianceRule(
            name=rule_data["name"],
            description=rule_data["description"],
            obligation=rule_data["obligation"],
            source=rule_data["source"]
        )

        for condition_data in rule_data["conditions"]:
            condition = RuleCondition(
                condition_field=condition_data["field"],
                condition_operator=condition_data["operator"],
                condition_value=condition_data["value"]
            )

            rule.conditions.append(condition)

        db.add(rule)

    db.commit()

    print("Rules inserted successfully!")

finally:
    db.close()