import os
from urllib.parse import quote_plus
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

password = quote_plus(os.getenv("DB_PASSWORD"))
print(os.getenv("DB_PASSWORD") is not None)  # Check if the password is loaded correctly
DATABASE_URL = f"postgresql+psycopg://postgres:{password}@localhost:5432/business_copilot"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker( #Think of a database session as a conversation with the database.
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db #"Here's the database session. Use it. 
    finally:
        db.close()
#makes sure the session gets closed even if something goes wrong.
#SessionLocal does not know which table you want to work with.
#It only knows which database to connect to.
#SessionLocal knows the database through engine
#engine = create_engine(DATABASE_URL)