import hashlib

import pytest

from cinedata.database import Database, QueryError


@pytest.mark.parametrize("sql", [
    "DELETE FROM dim_movies", "DROP TABLE dim_movies",
    "UPDATE dim_movies SET titulo='x'", "CREATE TABLE x (a)",
    "ATTACH DATABASE ':memory:' AS other", "PRAGMA query_only=OFF",
    "SELECT * FROM sqlite_master", "SELECT load_extension('anything')",
    "SELECT * FROM dim_movies; DELETE FROM dim_movies;",
    "WITH x AS (SELECT 1) DELETE FROM dim_movies",
])
def test_rejects_changes_and_external_access(database, sql):
    before = hashlib.sha256(database.path.read_bytes()).digest()
    with pytest.raises(QueryError):
        database.query(sql)
    assert hashlib.sha256(database.path.read_bytes()).digest() == before


def test_cte_aggregation_and_truncation(database):
    database.max_rows = 2
    result = database.query("WITH x AS (SELECT * FROM dim_movies) SELECT * FROM x ORDER BY sk_movie_id")
    assert len(result.rows) == 2
    assert result.truncated
    assert database.query("SELECT COUNT(*) FROM dim_movies").rows == [[6]]


def test_empty_result_and_sql_error(database):
    result = database.query("SELECT titulo FROM dim_movies WHERE 1=0")
    assert result.rows == []
    assert result.columns == ["titulo"]
    with pytest.raises(QueryError):
        database.query("SELECT nonexistent FROM dim_movies")


def test_query_deadline(database):
    database.timeout = 0
    with pytest.raises(QueryError, match="tempo"):
        database.query("WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n) SELECT SUM(x) FROM n")


def test_missing_database_does_not_create_file(tmp_path):
    path = tmp_path / "missing.db"
    with pytest.raises(FileNotFoundError):
        Database(path)
    assert not path.exists()

