import sqlite3

import pytest
from pydantic_ai import models

from cinedata.database import Database


@pytest.fixture(autouse=True)
def no_external_model_requests(monkeypatch):
    monkeypatch.setattr(models, "ALLOW_MODEL_REQUESTS", False)


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "gold.db"
    connection = sqlite3.connect(path)
    connection.executescript("""
    CREATE TABLE dim_movies(sk_movie_id TEXT PRIMARY KEY, titulo TEXT,
        data_lancamento TEXT, ano_lancamento INTEGER);
    CREATE TABLE fact_movies_performance(sk_movie_id TEXT PRIMARY KEY,
        receita_brl REAL, orcamento_brl REAL, lucro_brl REAL, popularidade REAL,
        nota_imdb REAL, nota_tmdb REAL);
    CREATE TABLE dim_genres(sk_genre_id TEXT PRIMARY KEY, nome_genero TEXT);
    CREATE TABLE dim_people(sk_person_id TEXT PRIMARY KEY, nome_pessoa TEXT, tipo_pessoa TEXT);
    CREATE TABLE dim_companies(sk_company_id TEXT PRIMARY KEY, nome_produtora TEXT);
    CREATE TABLE bridge_movie_genre(sk_movie_id TEXT, sk_genre_id TEXT);
    CREATE TABLE bridge_movie_person(sk_movie_id TEXT, sk_person_id TEXT);
    CREATE TABLE bridge_movie_company(sk_movie_id TEXT, sk_company_id TEXT);
    CREATE TABLE dim_reviews(sk_movie_id TEXT PRIMARY KEY,
        qtd_avaliacoes_usuarios INTEGER, nota_media_usuarios REAL);
    CREATE TABLE movie_reviews(id INTEGER PRIMARY KEY, sk_movie_id TEXT, rating REAL);
    INSERT INTO dim_genres VALUES ('g1','Action'),('g2','Drama');
    INSERT INTO dim_people VALUES ('a','Alice','Ator'),('d','Davi','Diretor');
    INSERT INTO dim_companies VALUES ('c','Cine');
    INSERT INTO dim_movies VALUES
      ('1','A','2021-10-05',2021), ('2','B','2026-10-05',2026),
      ('3','C','2026-10-06',2026), ('4','D','2021-10-04',2021),
      ('5','E',NULL,NULL), ('6','F','2024-01-01',2024);
    INSERT INTO fact_movies_performance VALUES
      ('1',100,50,50,10,8,9), ('2',200,50,150,20,7,8),
      ('3',NULL,NULL,0,5,6,7), ('4',100,NULL,0,4,NULL,7),
      ('5',0,50,-50,3,0,5), ('6',50,100,-50,2,5,NULL);
    INSERT INTO dim_reviews VALUES ('1',3,9),('2',1,4);
    INSERT INTO bridge_movie_genre SELECT sk_movie_id,'g1' FROM dim_movies;
    INSERT INTO bridge_movie_genre VALUES ('1','g2');
    INSERT INTO bridge_movie_company SELECT sk_movie_id,'c' FROM dim_movies;
    INSERT INTO bridge_movie_person SELECT sk_movie_id,'a' FROM dim_movies;
    INSERT INTO bridge_movie_person SELECT sk_movie_id,'d' FROM dim_movies;
    """)
    connection.close()
    return Database(path)

