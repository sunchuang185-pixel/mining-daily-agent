import httpx
import pytest

from mining_daily.models import ChatModel, ModelConfig, ProviderError, ResponseError


def test_model_json_and_usage():
    def handler(request):
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": '{"records": []}'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 3},
            },
        )

    model = ChatModel(
        ModelConfig("test", "https://example.org/v1", "test-key"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )
    assert model.complete("Return JSON", {}) == {"records": []}
    assert model.usage["prompt_tokens"] == 10


def test_retry_is_bounded_and_secret_not_in_error(monkeypatch):
    monkeypatch.setattr("mining_daily.models.time.sleep", lambda _: None)
    model = ChatModel(
        ModelConfig("test", "https://example.org", "private-secret", max_attempts=2),
        httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(429, text="private-secret"))
        ),
    )
    with pytest.raises(ProviderError) as exc:
        model.complete("JSON", {})
    assert "private-secret" not in str(exc.value)
    assert model.usage["calls"] == 2


def test_invalid_model_json_is_rejected():
    model = ChatModel(
        ModelConfig("test", "https://example.org", "test"),
        httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200, json={"choices": [{"message": {"content": "not JSON"}}]}
                )
            )
        ),
    )
    with pytest.raises(ResponseError):
        model.complete("JSON", {})
