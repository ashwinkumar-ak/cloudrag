import json

from backend.llm import LLMService


class FakeResponse:
    def __init__(self, lines):
        self.lines = lines

    def raise_for_status(self):
        return None

    def iter_lines(self, decode_unicode=True):
        return iter(self.lines)

    def close(self):
        return None


def test_generate_stream_yields_text_chunks(monkeypatch):
    payloads = [
        {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Hello"}]
                    }
                }
            ]
        },
        {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": " world"}]
                    }
                }
            ]
        },
    ]

    response = FakeResponse(
        [f"data: {json.dumps(item)}" for item in payloads]
    )

    def fake_post(*args, **kwargs):
        assert kwargs["stream"] is True
        assert "streamGenerateContent?alt=sse" in args[0]
        return response

    monkeypatch.setattr(
        "backend.llm.requests.post",
        fake_post,
    )

    service = LLMService(
        model="test-model",
        api_key="test-key",
    )

    assert list(service.generate_stream("test prompt")) == [
        "Hello",
        " world",
    ]
