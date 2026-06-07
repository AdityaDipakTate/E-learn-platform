# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Update this URL with your local PostgreSQL credentials:
# Format: postgresql://[username]:[password]@[host]:[port]/[database_name]
DATABASE_URL = "postgresql://aditya:root@localhost:5432/ojt_learn_db"

# 2. Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# 3. Create a SessionLocal class. Each instance of this class will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create the Base class that our models.py already uses
Base = declarative_base()

# 5. Dependency injection function for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()