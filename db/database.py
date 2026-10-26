import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PATH = BASE_DIR / "data" / "theatre.sqlite"
SQL_DIR = BASE_DIR / "sql"


@contextmanager
def connect(path=DEFAULT_PATH, *, readonly=False):
    """Транзакция с закрытием соединения."""
    path = Path(path).resolve()
    target = path.as_uri() + "?mode=ro" if readonly else str(path)
    conn = sqlite3.connect(target, uri=readonly)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def initialize_database(path=DEFAULT_PATH):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript((SQL_DIR / "schema.sql").read_text("utf-8"))


def load_queries():
    queries = {}
    source = (SQL_DIR / "queries.sql").read_text("utf-8")
    for block in source.split("-- name: ")[1:]:
        name, statement = block.split("\n", 1)
        queries[name.strip()] = statement.strip()
    return queries


QUERIES = load_queries()


def fetch(conn, name, parameters=()):
    return conn.execute(QUERIES[name], parameters).fetchall()
