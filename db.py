import os
from sqlalchemy import create_engine

def get_engine(db_url: str | None = None):
    url = db_url or os.getenv('DB_URL')
    if not url:
        raise RuntimeError('DB_URL not set. Define it in .env or pass explicitly.')
    engine = create_engine(url, pool_pre_ping=True, future=True)
    return engine
