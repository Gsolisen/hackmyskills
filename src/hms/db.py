"""Deferred SQLite database object and base model for HackMySkills."""
from peewee import SqliteDatabase, Model

db = SqliteDatabase(None, pragmas={"journal_mode": "wal", "foreign_keys": 1})


class BaseModel(Model):
    class Meta:
        database = db


def initialize_db(path: str) -> None:
    """Initialize the database at the given path.

    Must be called once during first-run setup (ensure_initialized) before
    any model operations. Uses WAL journal mode for concurrent read access
    and enforces foreign key constraints.
    """
    db.init(path, pragmas={
        "journal_mode": "wal",
        "cache_size": -16000,  # 16 MB page cache
        "foreign_keys": 1,
    })
