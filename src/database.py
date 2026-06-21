# KI Claude <KI-18>
# Database connection. The URL now comes from the DATABASE_URL environment variable so the
# API can be pointed at a Cloud database (Supabase / Railway / PlanetScale, ...) instead of the
# local SQLite file, WITHOUT changing the code. If DATABASE_URL is not set we fall back to the
# local SQLite file so development still works out of the box.
#
# Set it either as a real environment variable or in a `.env` file next to this module, e.g.:
#   DATABASE_URL=postgresql+psycopg2://user:password@host:5432/dbname   (Supabase/Railway)
#   DATABASE_URL=mysql+pymysql://user:password@host:3306/dbname         (PlanetScale)
# (.env is gitignored so the credentials are not committed.)
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


def _load_dotenv() -> None:
    """Minimal .env loader (KEY=VALUE per line) so we don't need an extra dependency.

    Existing real environment variables always win over the .env file.
    """
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


_load_dotenv()

# KI Claude <KI-20>
# Default the SQLite file to an ABSOLUTE path next to this module (src/RATBASE.db) so the
# server and init_db.py always agree on the same file, no matter the working directory
# (e.g. `uvicorn src.main:app` from the project root vs. `uvicorn main:app` from src/).
_DEFAULT_SQLITE = "sqlite:///" + os.path.join(os.path.dirname(os.path.abspath(__file__)), "RATBASE.db")
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", _DEFAULT_SQLITE)
# KI END <KI-20>

# check_same_thread is a SQLite-only argument; only pass it for SQLite URLs.
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
# KI END <KI-18>

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
 db = SessionLocal()
 try:
    yield db
 finally:
    db.close()
