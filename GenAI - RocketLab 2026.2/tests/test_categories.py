"""SQLs de referência para verificar as cinco categorias, sem chamadas de LLM.

Não são respostas pré-programadas: o agente gera seu próprio SQL em execução.
"""

from pathlib import Path

import pytest

from cinedata.database import Database

QUERIES = {
    "receita": """SELECT m.titulo, f.receita_brl FROM dim_movies m
        JOIN fact_movies_performance f USING(sk_movie_id)
        WHERE f.receita_brl IS NOT NULL ORDER BY f.receita_brl DESC, m.sk_movie_id LIMIT 10""",
    "lucro_genero": """SELECT g.nome_genero, AVG(f.receita_brl-f.orcamento_brl)
        FROM dim_genres g JOIN bridge_movie_genre b USING(sk_genre_id)
        JOIN fact_movies_performance f USING(sk_movie_id)
        WHERE f.receita_brl IS NOT NULL AND f.orcamento_brl IS NOT NULL
        GROUP BY g.sk_genre_id ORDER BY g.sk_genre_id""",
    "margem": """SELECT m.titulo,100.0*(f.receita_brl-f.orcamento_brl)/f.receita_brl AS margem
        FROM dim_movies m JOIN fact_movies_performance f USING(sk_movie_id)
        WHERE f.receita_brl>0 AND f.orcamento_brl IS NOT NULL
        ORDER BY margem DESC,m.sk_movie_id LIMIT 10""",
    "popularidade": """SELECT m.titulo,f.popularidade FROM dim_movies m
        JOIN fact_movies_performance f USING(sk_movie_id) WHERE f.popularidade IS NOT NULL
        ORDER BY f.popularidade DESC,m.sk_movie_id LIMIT 5""",
    "divergencia": """SELECT m.titulo,ABS(f.nota_tmdb-f.nota_imdb) AS divergencia
        FROM dim_movies m JOIN fact_movies_performance f USING(sk_movie_id)
        WHERE f.nota_tmdb IS NOT NULL AND f.nota_imdb IS NOT NULL
        ORDER BY divergencia DESC,m.sk_movie_id LIMIT 10""",
    "nota_ano": """SELECT m.ano_lancamento,AVG(f.nota_imdb) FROM dim_movies m
        JOIN fact_movies_performance f USING(sk_movie_id)
        WHERE m.ano_lancamento IS NOT NULL AND f.nota_imdb IS NOT NULL
        GROUP BY m.ano_lancamento ORDER BY m.ano_lancamento""",
    "ator": """WITH contagens AS (
        SELECT p.sk_person_id,p.nome_pessoa,COUNT(DISTINCT m.sk_movie_id) AS filmes
        FROM dim_movies m CROSS JOIN bridge_movie_person b ON b.sk_movie_id=m.sk_movie_id
        CROSS JOIN dim_people p ON p.sk_person_id=b.sk_person_id WHERE p.tipo_pessoa='Ator'
        AND m.data_lancamento BETWEEN '2021-10-05' AND '2026-10-05'
        GROUP BY p.sk_person_id)
        SELECT nome_pessoa,filmes FROM contagens
        WHERE filmes=(SELECT MAX(filmes) FROM contagens) ORDER BY sk_person_id""",
    "diretor": """SELECT p.nome_pessoa,AVG(f.nota_imdb) AS nota,
        COUNT(DISTINCT b.sk_movie_id) AS filmes FROM dim_people p
        JOIN bridge_movie_person b USING(sk_person_id)
        JOIN fact_movies_performance f USING(sk_movie_id)
        WHERE p.tipo_pessoa='Diretor' AND f.nota_imdb IS NOT NULL
        GROUP BY p.sk_person_id HAVING COUNT(DISTINCT b.sk_movie_id)>=5
        ORDER BY nota DESC,p.sk_person_id LIMIT 10""",
    "dupla": """WITH pares AS (
        SELECT a.sk_person_id AS aid,d.sk_person_id AS did,a.nome_pessoa AS ator,
        d.nome_pessoa AS diretor,COUNT(DISTINCT ba.sk_movie_id) AS filmes
        FROM dim_people d CROSS JOIN bridge_movie_person bd ON bd.sk_person_id=d.sk_person_id
        CROSS JOIN bridge_movie_person ba ON ba.sk_movie_id=bd.sk_movie_id
        CROSS JOIN dim_people a ON a.sk_person_id=ba.sk_person_id
        WHERE a.tipo_pessoa='Ator' AND d.tipo_pessoa='Diretor'
        GROUP BY a.sk_person_id,d.sk_person_id)
        SELECT ator,diretor,filmes FROM pares
        WHERE filmes=(SELECT MAX(filmes) FROM pares) ORDER BY aid,did""",
    "generos": """SELECT g.nome_genero,COUNT(DISTINCT b.sk_movie_id) FROM dim_genres g
        LEFT JOIN bridge_movie_genre b USING(sk_genre_id) GROUP BY g.sk_genre_id
        ORDER BY g.sk_genre_id""",
    "produtora": """WITH lucros AS (
        SELECT c.sk_company_id,c.nome_produtora,SUM(f.receita_brl-f.orcamento_brl) AS lucro
        FROM dim_companies c JOIN bridge_movie_company b USING(sk_company_id)
        JOIN fact_movies_performance f USING(sk_movie_id)
        WHERE f.receita_brl IS NOT NULL AND f.orcamento_brl IS NOT NULL
        GROUP BY c.sk_company_id)
        SELECT nome_produtora,lucro FROM lucros
        WHERE lucro=(SELECT MAX(lucro) FROM lucros) ORDER BY sk_company_id""",
    "margem_genero": """WITH margens AS (
        SELECT g.sk_genre_id,g.nome_genero,
        AVG(100.0*(f.receita_brl-f.orcamento_brl)/f.receita_brl) AS margem
        FROM dim_genres g JOIN bridge_movie_genre b USING(sk_genre_id)
        JOIN fact_movies_performance f USING(sk_movie_id)
        WHERE f.receita_brl>0 AND f.orcamento_brl IS NOT NULL GROUP BY g.sk_genre_id)
        SELECT nome_genero,margem FROM margens
        WHERE margem=(SELECT MAX(margem) FROM margens) ORDER BY sk_genre_id""",
    "avaliacoes": """SELECT m.titulo,r.qtd_avaliacoes_usuarios FROM dim_movies m
        JOIN dim_reviews r USING(sk_movie_id) WHERE r.qtd_avaliacoes_usuarios>0
        ORDER BY r.qtd_avaliacoes_usuarios DESC,m.sk_movie_id LIMIT 10""",
    "divergencia_usuarios": """SELECT m.titulo,
        ABS(r.nota_media_usuarios-f.nota_imdb) AS divergencia FROM dim_movies m
        JOIN dim_reviews r USING(sk_movie_id) JOIN fact_movies_performance f USING(sk_movie_id)
        WHERE r.nota_media_usuarios IS NOT NULL AND f.nota_imdb IS NOT NULL
        AND r.qtd_avaliacoes_usuarios>0 ORDER BY divergencia DESC,m.sk_movie_id LIMIT 10""",
}


@pytest.mark.parametrize("category", QUERIES)
def test_category_sql_on_fixture(database, category):
    assert database.query(QUERIES[category]).rows


def test_financial_rules_and_date_boundaries(database):
    assert database.query(QUERIES["lucro_genero"]).rows == [["Action",25.0],["Drama",50.0]]
    assert database.query(QUERIES["margem"]).rows == [["B",75.0],["A",50.0],["F",-100.0]]
    assert database.query(QUERIES["ator"]).rows == [["Alice",3]]
    assert database.query(QUERIES["diretor"]).rows == [["Davi",5.2,5]]
    assert database.query(QUERIES["dupla"]).rows == [["Alice","Davi",6]]
    assert database.query(QUERIES["produtora"]).rows == [["Cine",100.0]]
    assert database.query(QUERIES["margem_genero"]).rows == [["Drama",50.0]]
    assert database.query(QUERIES["divergencia_usuarios"]).rows == [["B",3.0],["A",1.0]]


@pytest.mark.parametrize("category", QUERIES)
def test_category_sql_on_supplied_gold(category):
    path = Path(__file__).resolve().parents[1] / "cinerocket-db" / "cinerocket (1).db"
    if not path.exists():
        pytest.skip("Base Gold original não está disponível")
    result = Database(path).query(QUERIES[category])
    assert result.rows

