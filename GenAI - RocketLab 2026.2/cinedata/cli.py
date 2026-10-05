"""Interface de terminal; cada pergunta inicia uma execução independente."""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded, UnexpectedModelBehavior

from .agent import ask, create_agent
from .database import Database

ROOT = Path(__file__).resolve().parent.parent


def print_answer(answer, queries):
    print("\n" + answer.texto)
    for index, result in enumerate(queries, 1):
        print(f"\nSQL {index}:\n{result.sql}")
        print("Resultado (colunas e linhas):")
        print(json.dumps({"colunas": result.columns, "linhas": result.rows},
                         ensure_ascii=False, indent=2))
        if result.truncated:
            print("Exibição limitada a 100 linhas; existem mais resultados.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="CineData: perguntas em linguagem natural sobre filmes.")
    parser.add_argument("pergunta", nargs="?", help="Sem pergunta, inicia o modo interativo.")
    parser.add_argument("--db", type=Path, help="Caminho do SQLite; prevalece sobre DATABASE_PATH.")
    args = parser.parse_args(argv)
    load_dotenv(ROOT / ".env")
    try:
        path = args.db or Path(os.getenv("DATABASE_PATH", "cinerocket-db/cinerocket (1).db"))
        database = Database(path if path.is_absolute() else ROOT / path)
        database.schema()
        agent = create_agent(os.getenv("OPENROUTER_API_KEY"))
    except (OSError, ValueError) as exc:
        print(f"Erro de configuração: {exc}", file=sys.stderr)
        return 1

    def execute(question):
        try:
            answer, queries = ask(agent, database, question)
            print_answer(answer, queries)
            return 0
        except KeyboardInterrupt:
            print("\nConsulta interrompida.", file=sys.stderr)
            return 130
        except ModelHTTPError as exc:
            print(f"Erro da API do OpenRouter (HTTP {exc.status_code}). Verifique a chave, "
                  "a disponibilidade do modelo e o saldo/limites no OpenRouter.", file=sys.stderr)
            return 1
        except (UsageLimitExceeded, UnexpectedModelBehavior):
            print("O agente não conseguiu concluir dentro dos limites de execução. "
                  "Tente uma pergunta mais específica.", file=sys.stderr)
            return 1
        except Exception:
            # Não exibe payloads de API, chaves ou respostas brutas do provedor.
            print("Não foi possível concluir a consulta. Verifique a conexão, a chave, "
                  "a cota da API e tente simplificar a pergunta. Consulte o README.", file=sys.stderr)
            return 1

    if args.pergunta is not None:
        if not args.pergunta.strip():
            parser.error("A pergunta não pode ser vazia.")
        return execute(args.pergunta)

    print("CineData | Nemotron 3 Super (free) via OpenRouter | digite sair para encerrar")
    print("Cada pergunta é independente; repita os filtros desejados.")
    while True:
        try:
            question = input("\nPergunta> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if question.lower() in {"sair", "exit", "quit"}:
            return 0
        if question:
            execute(question)

