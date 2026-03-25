import pytest
from unittest.mock import patch, MagicMock
from src.utils.llm import LLMClient


class TestLLMConnection:

    @pytest.fixture
    def llm_client(self):
        return LLMClient()

    def test_client_initialization(self, llm_client):
        assert llm_client.client is not None
        assert llm_client.model == "deepseek-ai/DeepSeek-V3.2-fast"

    def test_chat_returns_string(self, llm_client):
        response = llm_client.chat([
            {"role": "user", "content": "What is the capital of France? Answer in one word."}
        ], max_tokens=50)

        assert isinstance(response, str)

    def test_chat_with_json_returns_string(self, llm_client):
        response = llm_client.chat_with_json([
            {"role": "user", "content": 'Return a JSON object with a single key "status" and value "ok".'}
        ], max_tokens=100)

        assert isinstance(response, str)
        assert "status" in response
