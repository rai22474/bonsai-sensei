import logging
import os
from sqlmodel import SQLModel, create_engine
from bonsai_sensei.database import species

# Configure logging locally
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://bonsai_user:bonsai_password@localhost:5432/bonsai_db"
)


def reset_db():
    logger.info(f"Connecting to database at {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)

    logger.info("Dropping all existing tables...")
    SQLModel.metadata.drop_all(engine)
    logger.info("All tables dropped.")


if __name__ == "__main__":
    reset_db()
