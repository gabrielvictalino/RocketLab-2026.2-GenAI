"""Acesso SQLite somente leitura, com limites por consulta."""

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

TABLES = frozenset({
    "dim_movies", "fact_movies_performance", "dim_genres", "dim_people",
    "dim_companies", "dim_reviews", "movie_reviews", "bridge_movie_genre",
    "bridge_movie_person", "bridge_movie_company",
})
FUNCTIONS = frozenset({
    "abs", "avg", "count", "sum", "total", "min", "max", "round", "coalesce",
    "nullif", "ifnull", "date", "datetime", "strftime", "julianday", "unixepoch",
    "lower", "upper", "like", "length", "substr", "substring", "trim", "replace",
    "row_number", "rank", "dense_rank", "lag", "lead", "first_value", "last_value",
    "group_concat", "typeof", "iif", "concat", "concat_ws",
})


class QueryError(ValueError):
    """Consulta rejeitada, inválida ou que excedeu o tempo permitido."""


@dataclass
class QueryResult:
    sql: str
    columns: list[str]
    rows: list[list]
    truncated: bool


class Database:
    def __init__(self, path: Path, max_rows: int = 100, timeout: float = 30):
        self.path = path.resolve()
        if not self.path.is_file():
            raise FileNotFoundError(f"Banco não encontrado: {self.path}")
        self.max_rows = max_rows
        self.timeout = timeout

    def _connect(self):
        connection = sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True)
        connection.execute("PRAGMA query_only = ON")
        # Page cache per connection, released on close; no answer caching.
        connection.execute("PRAGMA cache_size = -65536")
        return connection

    def schema(self) -> str:
        connection = self._connect()
        try:
            found = dict(connection.execute(
                "SELECT name, sql FROM sqlite_master WHERE type = 'table'"
            ))
            missing = TABLES - found.keys()
            if missing:
                raise QueryError("Tabelas ausentes: " + ", ".join(sorted(missing)))
            return "\n\n".join(found[name] for name in sorted(TABLES))
        finally:
            connection.close()

    @staticmethod
    def _authorize(action, arg1, arg2, database, source):
        if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_RECURSIVE):
            return sqlite3.SQLITE_OK
        # SQLite supplies no database name for COUNT(*)'s table-level read.
        if action == sqlite3.SQLITE_READ and arg1 in TABLES and (
            database == "main" or (database is None and arg2 == "")
        ):
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_FUNCTION and (arg2 or "").lower() in FUNCTIONS:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY

    def query(self, sql: str) -> QueryResult:
        if not sql.strip() or len(sql) > 20000:
            raise QueryError("SQL vazio ou maior que 20.000 caracteres.")
        connection = self._connect()
        started = time.monotonic()
        try:
            connection.set_authorizer(self._authorize)
            connection.set_progress_handler(
                lambda: int(time.monotonic() - started > self.timeout), 1000
            )
            cursor = connection.execute(sql)
            if cursor.description is None:
                raise QueryError("A consulta precisa retornar uma tabela.")
            rows = cursor.fetchmany(self.max_rows + 1)
            return QueryResult(
                sql=sql,
                columns=[column[0] for column in cursor.description],
                rows=[list(row) for row in rows[:self.max_rows]],
                truncated=len(rows) > self.max_rows,
            )
        except sqlite3.Error as exc:
            if time.monotonic() - started > self.timeout:
                raise QueryError("Consulta excedeu o limite de tempo; simplifique o SQL.") from exc
            raise QueryError(f"Consulta inválida ou não permitida: {exc}") from exc
        finally:
            connection.close()

