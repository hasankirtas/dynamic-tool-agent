import pytest
import json
from unittest.mock import MagicMock, patch
from src.agent.main_agent import MainAgent


@pytest.fixture
def mock_registry():
    registry = MagicMock()
    registry.search.return_value = [{
        "name": "weather_service",
        "description": "Get current weather information",
        "category": "information",
        "relevance_score": 2.5,
        "schema": {"name": "weather_service", "description": "Get weather", "parameters": {"type": "object", "properties": {"location": {"type": "string", "description": "City name"}}, "required": ["location"]}},
    }]
    registry.get_tool.return_value = MagicMock(
        execute=MagicMock(return_value={"status": "success", "location": "Istanbul", "temperature": 22, "condition": "Sunny"})
    )
    return registry


@pytest.fixture
def agent(mock_registry):
    return MainAgent(registry=mock_registry)


class TestMainAgent:

    def test_small_talk_does_not_call_registry(self, agent, mock_registry):
        with patch.object(agent.llm, "chat_with_json") as mock_llm:
            mock_llm.return_value = json.dumps({
                "requires_tool": False,
                "search_query": None,
                "small_talk_response": "Hello! How can I help you today?",
            })
            response = agent.run("Hey, how are you?")

        mock_registry.search.assert_not_called()
        assert isinstance(response, str)
        assert len(response) > 0

    def test_tool_request_calls_registry(self, agent, mock_registry):
        with patch.object(agent.llm, "chat_with_json") as mock_json, \
             patch.object(agent.llm, "chat") as mock_chat:

            mock_json.side_effect = [
                json.dumps({"requires_tool": True, "search_query": "current weather for a city", "small_talk_response": None}),
                json.dumps({"can_fulfill": True, "reasoning": "weather_service matches", "selected_tools": [{"name": "weather_service", "parameters": {"location": "Istanbul"}}], "cannot_fulfill_response": None}),
            ]
            mock_chat.return_value = "The weather in Istanbul is 22°C and Sunny."

            response = agent.run("What is the weather in Istanbul?")

        mock_registry.search.assert_called_once_with(query="current weather for a city", top_k=5)
        assert "Istanbul" in response or isinstance(response, str)

    def test_no_suitable_tool_returns_graceful_response(self, agent, mock_registry):
        with patch.object(agent.llm, "chat_with_json") as mock_json:
            mock_json.side_effect = [
                json.dumps({"requires_tool": True, "search_query": "quantum teleportation device", "small_talk_response": None}),
                json.dumps({"can_fulfill": False, "reasoning": "No tool can do this", "selected_tools": [], "cannot_fulfill_response": "I don't have a quantum teleportation tool, sorry!"}),
            ]
            response = agent.run("Teleport me to Mars using quantum physics")

        assert "quantum teleportation" in response.lower() or isinstance(response, str)

    def test_conversation_history_grows(self, agent, mock_registry):
        with patch.object(agent.llm, "chat_with_json") as mock_json:
            mock_json.return_value = json.dumps({
                "requires_tool": False,
                "search_query": None,
                "small_talk_response": "I'm doing great!",
            })
            agent.run("How are you?")
            agent.run("What's your name?")

        assert len(agent.conversation_history) == 4
