import pytest
import shutil
from src.tools.registry import ToolRegistry


class TestToolRegistry:

    @pytest.fixture(scope="class")
    def registry(self):
        test_db_path = "./test_chroma_db"
        reg = ToolRegistry(db_path=test_db_path)
        reg.register_all()
        yield reg
        shutil.rmtree(test_db_path, ignore_errors=True)

    def test_auto_discover_finds_all_tools(self, registry):
        tools = registry.list_tools()
        assert len(tools) == 10

    def test_all_tools_registered_in_chromadb(self, registry):
        count = registry.collection.count()
        assert count == 10

    def test_search_weather_returns_weather_tool(self, registry):
        results = registry.search("What is the weather like in Istanbul?")
        assert len(results) > 0
        tool_names = [r["name"] for r in results]
        assert "weather_service" in tool_names

    def test_search_email_returns_email_tool(self, registry):
        results = registry.search("Send an email to my colleague")
        assert len(results) > 0
        tool_names = [r["name"] for r in results]
        assert "email_sender" in tool_names

    def test_search_returns_schema(self, registry):
        results = registry.search("Calculate 2+2")
        assert len(results) > 0
        first = results[0]
        assert "schema" in first
        assert first["schema"] is not None
        assert "parameters" in first["schema"]

    def test_reranker_sorts_by_relevance(self, registry):
        results = registry.search("What is the weather in Ankara?", top_k=5)
        assert results[0]["name"] == "weather_service"

    def test_search_with_category_filter(self, registry):
        results = registry.search("help me with something", category="finance")
        for r in results:
            assert r["category"] == "finance"

    def test_get_tool_by_name(self, registry):
        tool = registry.get_tool("weather_service")
        assert tool is not None
        assert tool.name == "weather_service"

    def test_get_schema_by_name(self, registry):
        schema = registry.get_schema("translator")
        assert schema is not None
        assert schema["name"] == "translator"
