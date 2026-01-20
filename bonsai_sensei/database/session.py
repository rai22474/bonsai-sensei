import os
from functools import lru_cache
from sqlmodel import create_engine, Session

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://bonsai_user:bonsai_password@localhost:5432/bonsai_db"
)

@lru_cache()
def get_engine():
    return create_engine(DATABASE_URL)

def get_session(engine):
    # expire_on_commit=False allows objects to persist detached after transaction commit/session close,
    # which is crucial when returning objects from functions decorated with @with_session
    return Session(engine, expire_on_commit=False)
