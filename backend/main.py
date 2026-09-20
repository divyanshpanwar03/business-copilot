from fastapi import FastAPI, Depends
from pydantic import BaseModel
from models import BusinessProfileDB, ComplianceRule
from sqlalchemy.orm import Session
from database import get_db
from rule_engine import get_applicable_rules
app = FastAPI()

class BusinessProfile(BaseModel):
    business_name: str
    entity_type:str
    location:str
    industry:str
    annual_turnover:float
    employee_count:int
    gst_registered: bool    

@app.get("/")
def root():
    return {"message":"Hello, Business Copilot"}

@app.get("/health")
def health():
    return {"status":"healthy"}

@app.post("/business-profile")
def create_business_profile(profile: BusinessProfile, db: Session = Depends(get_db)): #"FastAPI, please get me a database session using get_db()."
    db_profile = BusinessProfileDB(**profile.model_dump())# takes the Pydantic object and converts it into a Python dictionary.

    db.add(db_profile) # "SQLAlchemy, I want to insert this object into the database."
    db.commit() # "Save this transaction."
    db.refresh(db_profile) # asks the database to give us the latest version of the object.

    return {
        "message": "Business profile saved",
        "id": db_profile.id
    }

@app.get("/business-profile/{profile_id}")
def get_business_profile(
    profile_id: int,
    db: Session = Depends(get_db)
):
    profile = db.get(BusinessProfileDB, profile_id)

    if profile is None:
        return {"message": "Business profile not found"}

    return {
        "id": profile.id,
        "business_name": profile.business_name,
        "entity_type": profile.entity_type,
        "location": profile.location,
        "industry": profile.industry,
        "annual_turnover": profile.annual_turnover,
        "employee_count": profile.employee_count,
        "gst_registered": profile.gst_registered
    }

@app.put("/business-profile/{profile_id}")
def update_business_profile(
    profile_id: int,
    profile: BusinessProfile,
    db: Session = Depends(get_db)
):
    db_profile = db.get(BusinessProfileDB, profile_id)

    if db_profile is None:
        return {"message": "Business profile not found"}

    db_profile.business_name = profile.business_name
    db_profile.entity_type = profile.entity_type
    db_profile.location = profile.location
    db_profile.industry = profile.industry
    db_profile.annual_turnover = profile.annual_turnover
    db_profile.employee_count = profile.employee_count
    db_profile.gst_registered = profile.gst_registered

    db.commit()
    db.refresh(db_profile)

    return {
        "message": "Business profile updated",
        "id": db_profile.id
    }

@app.delete("/business-profile/{profile_id}")
def delete_business_profile(
    profile_id: int,
    db: Session = Depends(get_db)
):
    db_profile = db.get(BusinessProfileDB, profile_id)

    if db_profile is None:
        return {"message": "Business profile not found"}

    db.delete(db_profile)
    db.commit()

    return {
        "message": "Business profile deleted",
        "id": profile_id
    }
def evaluate_rule(profile, rule):
    field_value = getattr(profile, rule.condition_field)

    if rule.condition_operator == ">=":
        return field_value >= float(rule.condition_value)

    return False
@app.get("/business-profile/{profile_id}/compliance")
def get_compliance(
    profile_id: int,
    db: Session = Depends(get_db)
):
    profile = db.get(BusinessProfileDB, profile_id)

    if profile is None:
        return {"message": "Business profile not found"}

    rules = db.query(ComplianceRule).all()

    applicable_rules = get_applicable_rules(profile, rules)

    applicable_rule_data = []

    for rule in applicable_rules:
     applicable_rule_data.append({
        "name": rule.name,
        "obligation": rule.obligation,
        "source": rule.source
    })
    return {
    "business_name": profile.business_name,
    "applicable_rules": applicable_rule_data
}