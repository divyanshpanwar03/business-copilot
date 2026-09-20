from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

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

    condition_field: Mapped[str] = mapped_column(String)
    condition_operator: Mapped[str] = mapped_column(String)
    condition_value: Mapped[str] = mapped_column(String)

    obligation: Mapped[str] = mapped_column(String)

    source: Mapped[str] = mapped_column(String)