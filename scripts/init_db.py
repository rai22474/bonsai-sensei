import logging
import os
from sqlmodel import SQLModel, create_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://bonsai_user:bonsai_password@localhost:5432/bonsai_db")

def create_db_and_tables():
    logger.info(f"Connecting to database at {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    logger.info("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    logger.info("Tables created.")

if __name__ == "__main__":
    create_db_and_tables()
