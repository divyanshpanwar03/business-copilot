import json
from datetime import date
from pathlib import Path

from database import SessionLocal
from models import ComplianceRule, RuleCondition
from rules_validator import validate_rule

BASE_DIR = Path(__file__).resolve().parent.parent # gets you to business-copilot
RULES_FILE = BASE_DIR / "data" / "rules.json"


with open(RULES_FILE, "r", encoding="utf-8") as file:
    data = json.load(file)


rules_data = data["rules"]

db = SessionLocal()

try:
    for rule_data in rules_data:
        errors = validate_rule(rule_data)

        if errors:
            print(
                f"Invalid rule: {rule_data.get('name', 'Unknown')}"
    )

        for error in errors:
            print(f"  - {error}")

        continue
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

        effective_from = None

        if rule_data["effective_from"]:
            effective_from = date.fromisoformat(
                rule_data["effective_from"]
            )

        effective_to = None

        if rule_data["effective_to"]:
            effective_to = date.fromisoformat(
                rule_data["effective_to"]
            )

        rule = ComplianceRule(
            name=rule_data["name"],
            description=rule_data["description"],
            category=rule_data["category"],
            priority=rule_data["priority"],
            frequency=rule_data["frequency"],
            effective_from=effective_from,
            effective_to=effective_to,
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