from datetime import date

from pydantic_ai.messages import ModelResponse, ToolCallPart, ToolReturnPart, RetryPromptPart
from pydantic_ai.models.function import FunctionModel

from cinedata.agent import ask, create_agent


def test_openrouter_configuration():
    agent = create_agent("test-key")
    assert agent.model.model_name == "nvidia/nemotron-3-super-120b-a12b:free"
    assert agent.model.system == "openrouter"


def test_openrouter_tool_roundtrip(database, monkeypatch):
    import json
    import httpx
    from pydantic_ai import models
    from pydantic_ai.models.openrouter import OpenRouterModel
    from pydantic_ai.providers.openrouter import OpenRouterProvider

    requests = []

    def handler(request):
        assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-key"
        body = json.loads(request.content)
        assert body["model"] == "nvidia/nemotron-3-super-120b-a12b:free"
        requests.append(body)
        if len(requests) == 1:
            name = "consultar_sql"
            arguments = {"sql": "SELECT COUNT(*) AS filmes FROM dim_movies"}
        else:
            tool_message = next(m for m in body["messages"] if m["role"] == "tool")
            assert json.loads(tool_message["content"])["rows"] == [[6]]
            name = next(t["function"]["name"] for t in body["tools"]
                        if t["function"]["name"] != "consultar_sql")
            arguments = {"status": "resposta", "texto": "Existem 6 filmes."}
        return httpx.Response(200, json={
            "id": "test-completion", "object": "chat.completion", "created": 0,
            "model": "nvidia/nemotron-3-super-120b-a12b:free", "provider": "Google",
            "choices": [{"index": 0, "finish_reason": "tool_calls", "message": {
                "role": "assistant", "content": None, "tool_calls": [{
                    "id": f"call-{len(requests)}", "type": "function",
                    "function": {"name": name, "arguments": json.dumps(arguments)},
                }],
            }}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        })

    # Only the local mock transport is used; this test cannot contact OpenRouter.
    monkeypatch.setattr(models, "ALLOW_MODEL_REQUESTS", True)
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenRouterProvider(api_key="test-key", http_client=client)
    model = OpenRouterModel("nvidia/nemotron-3-super-120b-a12b:free", provider=provider)
    try:
        answer, queries = ask(create_agent(model=model), database, "Quantos filmes?")
        assert answer.texto == "Existem 6 filmes."
        assert queries[0].rows == [[6]]
        assert len(requests) == 2
    finally:
        import asyncio
        asyncio.run(client.aclose())


def test_agent_executes_tool_before_answer(database):
    calls = []

    def model(messages, info):
        calls.append(messages)
        if len(calls) == 1:
            return ModelResponse(parts=[ToolCallPart("consultar_sql", {"sql": "SELECT COUNT(*) AS filmes FROM dim_movies"})])
        tool_results = [p for m in messages for p in m.parts if isinstance(p, ToolReturnPart)]
        assert tool_results[-1].content.rows == [[6]]
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name,
            {"status": "resposta", "texto": "Existem 6 filmes."})])

    answer, queries = ask(create_agent(model=FunctionModel(model)), database,
                          "Quantos filmes existem?", date(2026, 10, 5))
    assert answer.texto == "Existem 6 filmes."
    assert len(queries) == 1
    assert queries[0].rows == [[6]]


def test_agent_retries_invalid_sql(database):
    calls = 0

    def model(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(parts=[ToolCallPart("consultar_sql", {"sql": "DELETE FROM dim_movies"})])
        if calls == 2:
            assert any(isinstance(p, RetryPromptPart) for m in messages for p in m.parts)
            return ModelResponse(parts=[ToolCallPart("consultar_sql", {"sql": "SELECT COUNT(*) FROM dim_movies"})])
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name,
            {"status": "resposta", "texto": "6 filmes."})])

    _, queries = ask(create_agent(model=FunctionModel(model)), database, "Quantos filmes?")
    assert calls == 3
    assert queries[0].rows == [[6]]


def test_answer_without_query_is_retried(database):
    calls = 0

    def model(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name,
                {"status": "resposta", "texto": "42 filmes."})])
        assert any(isinstance(p, RetryPromptPart) for m in messages for p in m.parts)
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name,
            {"status": "esclarecimento", "texto": "Qual informação do catálogo você deseja?"})])

    answer, queries = ask(create_agent(model=FunctionModel(model)), database, "Ajuda")
    assert answer.status == "esclarecimento"
    assert not queries

