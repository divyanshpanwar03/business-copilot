from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import date

class Base(DeclarativeBase):
    pass


class BusinessProfileDB(Base):
    __tablename__ = "business_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_name: Mapped[str] = mapped_column(String)
    entity_type: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String)
    industry: Mapped[str] = mapped_column(String)
    annual_turnover: Mapped[float] = mapped_column(Float)
    employee_count: Mapped[int] = mapped_column(Integer)
    gst_registered: Mapped[bool] = mapped_column(Boolean)


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    priority: Mapped[int] = mapped_column(Integer)
    frequency: Mapped[str] = mapped_column(String)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    condition_logic: Mapped[str] = mapped_column(String, default="AND")
    obligation: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)

    conditions: Mapped[list["RuleCondition"]] = relationship(
        back_populates="rule",
        cascade="all, delete-orphan"
    )


class RuleCondition(Base):
    __tablename__ = "rule_conditions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    rule_id: Mapped[int] = mapped_column(
        ForeignKey("compliance_rules.id")
    )

    condition_field: Mapped[str] = mapped_column(String)
    condition_operator: Mapped[str] = mapped_column(String)
    condition_value: Mapped[str] = mapped_column(String)

    rule: Mapped["ComplianceRule"] = relationship(
        back_populates="conditions"
    )