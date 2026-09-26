from database import SessionLocal
from models import ComplianceRule, RuleCondition
from datetime import date

RULES = [
    {
        "name": "Employee Compliance Rule",
        "description": (
            "Applies when the business is a Private Limited company "
            "with 100 or more employees"
        ),
        "category": "Employee",
        "priority": 1,
        "frequency": "Annual",
        "effective_from": date(2025,4,1),
        "effective_to": None,
        "condition_logic": "AND",
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
        "category": "GST",
        "priority": 1,
        "frequency": "Monthly",
        "effective_from": date(2025,4,1),
        "effective_to": None,
        "condition_logic": "AND",
        "obligation": "Example GST compliance obligation",
        "source": "GST Portal",
        "conditions": [
            {
                "field": "gst_registered",
                "operator": "==",
                "value": "true"
            }
        ]
    },
    {
        "name": "High Business Size Rule",
        "description": (
            "Applies when either employee count or annual turnover "
            "reaches the defined threshold"
        ),
        "category": "Business Size",
        "priority": 2,
        "frequency": "Annual",
        "effective_from": date(2025, 4, 1),
        "effective_to": None,
        "condition_logic": "OR",
        "obligation": "Example high-business-size compliance obligation",
        "source": "Dummy source for development",
        "conditions": [
            {
                "field": "employee_count",
                "operator": ">=",
                "value": "100"
            },
            {
                "field": "annual_turnover",
                "operator": ">=",
                "value": "50000000"
            }
        ]
    },
    {
        "name": "EPF Coverage Threshold",
        "description": (
            "Simplified development rule for establishments "
            "with 20 or more employees"
        ),
        "category": "Employee",
        "priority": 1,
        "frequency": "Ongoing",
        "effective_from": date(1952,11,1),
        "effective_to": None,
        "condition_logic": "AND",
        "obligation": (
            "Check EPF applicability and registration requirements"
        ),
        "source": (
            "https://www.epfindia.gov.in/site_docs/"
            "PDFs/Downloads_PDFs/EPFAct1952.pdf"
        ),
        "conditions": [
            {
                "field": "employee_count",
                "operator": ">=",
                "value": "20"
            }
        ]
    },
    {
    "name": "Maharashtra Shops and Establishments Coverage",
    "description": (
        "Applies to establishments in Maharashtra employing "
        "10 or more workers"
    ),
    "category": "Labour",
    "priority": 2,
    "frequency": "Ongoing",
    "effective_from": date(2017, 9, 7),
    "effective_to": None,
    "condition_logic": "AND",
    "obligation": (
        "Check applicable registration and employment-condition "
        "requirements under Maharashtra Shops and Establishments law"
    ),
    "source": (
        "Maharashtra Shops and Establishments "
        "(Regulation of Employment and Conditions of Service) Act, 2017"
    ),
    "conditions": [
        {
            "field": "location",
            "operator": "==",
            "value": "Maharashtra"
        },
        {
            "field": "employee_count",
            "operator": ">=",
            "value": "10"
        }
    ]
},
{
    "name": "ESIC Coverage Threshold",
    "description": (
        "Simplified development rule for establishments "
        "with 10 or more employees"
    ),
    "category": "Employee",
    "priority": 1,
    "frequency": "Ongoing",
    "effective_from": date(2025, 11, 21),
    "effective_to": None,
    "condition_logic": "AND",
    "obligation": (
        "Check ESI applicability and registration requirements"
    ),
    "source": (
        "Ministry of Labour and Employment - "
        "Code on Social Security, 2020"
    ),
    "conditions": [
        {
            "field": "employee_count",
            "operator": ">=",
            "value": "10"
        }
    ]
}
]


db = SessionLocal()

try:
    for rule_data in RULES:

        existing_rule = (
            db.query(ComplianceRule)
            .filter(
                ComplianceRule.name == rule_data["name"]
            )
            .first()
        )

        if existing_rule:
            print(
                f"Skipping existing rule: "
                f"{rule_data['name']}"
            )
            continue

        rule = ComplianceRule(
            name=rule_data["name"],
            description=rule_data["description"],
            category=rule_data["category"],
            priority=rule_data["priority"],
            frequency=rule_data["frequency"],
            effective_from=rule_data["effective_from"],
            effective_to=rule_data["effective_to"],
            condition_logic=rule_data["condition_logic"],
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

    print("Rule seeding completed!")

finally:
    db.close()