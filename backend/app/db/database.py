import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()  # This reads the .env file and loads the variables

DATABASE_URL = os.getenv('DATABASE_URL')

# Create the SQLAlchemy engine
# pool_pre_ping=True means SQLAlchemy will test connections before using them
# This prevents 'connection closed' errors after the DB restarts
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# SessionLocal is the class we use to create database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class all our database models inherit from
class Base(DeclarativeBase):
    pass

def get_db():
    """
    FastAPI dependency function.
    Creates a database session, yields it to the route,
    then closes it when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()