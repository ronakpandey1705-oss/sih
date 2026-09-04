from unittest.mock import AsyncMock, patch

from app.config import settings


def test_chat_requires_api_key(client, monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    response = client.post("/api/chat", json={"message": "What is MRP?"})
    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]


def test_chat_calls_groq(client, monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")

    mock_complete = AsyncMock(return_value="MRP is the maximum retail price declared on the pack.")
    with patch("app.api.chat.GroqChatService.complete", mock_complete):
        response = client.post(
            "/api/chat",
            json={
                "message": "What is MRP?",
                "history": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello."}],
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "MRP" in data["reply"]
    assert data["model"] == "llama-3.3-70b-versatile"
    mock_complete.assert_awaited_once()
