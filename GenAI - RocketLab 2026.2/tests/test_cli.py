from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from cinedata import cli
from cinedata.agent import create_agent


def test_cli_single_question_end_to_end(database, monkeypatch, capsys):
    def model(messages, info):
        if len(messages) == 1:
            return ModelResponse(parts=[ToolCallPart("consultar_sql", {
                "sql": "SELECT COUNT(*) AS total FROM dim_movies"})])
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, {
            "status": "resposta", "texto": "Existem 6 filmes."})])

    monkeypatch.setattr(cli, "create_agent", lambda key: create_agent(model=FunctionModel(model)))
    assert cli.main(["--db", str(database.path), "Quantos filmes?"]) == 0
    output = capsys.readouterr().out
    assert "Existem 6 filmes." in output
    assert "SELECT COUNT(*)" in output
    assert '"total"' in output


def test_cli_missing_key(database, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert cli.main(["--db", str(database.path), "Quantos filmes?"]) == 1
    assert "OPENROUTER_API_KEY" in capsys.readouterr().err


def test_cli_missing_database(tmp_path, capsys):
    assert cli.main(["--db", str(tmp_path / "missing.db"), "Quantos filmes?"]) == 1
    assert "Banco não encontrado" in capsys.readouterr().err


def test_interactive_questions_have_no_history(database, monkeypatch, capsys):
    first_requests = []

    def model(messages, info):
        first_requests.append(len(messages))
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, {
            "status": "esclarecimento", "texto": "Informe a pergunta sobre filmes."})])

    entries = iter(["", "Ajuda", "Ajuda novamente", "sair"])
    monkeypatch.setattr("builtins.input", lambda _: next(entries))
    monkeypatch.setattr(cli, "create_agent", lambda key: create_agent(model=FunctionModel(model)))
    assert cli.main(["--db", str(database.path)]) == 0
    assert first_requests == [1, 1]

