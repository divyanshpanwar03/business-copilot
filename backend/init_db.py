from database import engine
from models import Base

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")

#Base.metadata contains information about all the SQLAlchemy models that inherit from Base.

#create_all() tells SQLAlchemy:

#"Look at these models and create the corresponding tables in the database if they don't already exist."**/