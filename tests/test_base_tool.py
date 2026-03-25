from typing import Any
from src.tools.abstraction.base_tool import BaseTool, ToolMetadata, ToolParameter


class MockWeatherTool(BaseTool):

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="weather_service",
            description="Get current weather information for a specific location",
            category="information",
            tags=["weather", "temperature", "forecast", "location"],
            parameters=[
                ToolParameter(
                    name="location",
                    type="string",
                    description="City name or coordinates",
                    required=True,
                ),
                ToolParameter(
                    name="unit",
                    type="string",
                    description="Temperature unit (celsius/fahrenheit)",
                    required=False,
                    default="celsius",
                ),
            ],
        )

    def execute(self, **kwargs) -> dict[str, Any]:
        return {"temperature": 22, "condition": "Sunny", "location": kwargs.get("location")}


class TestToolMetadata:

    def test_search_text_contains_all_fields(self):
        tool = MockWeatherTool()
        search_text = tool.metadata.to_search_text()

        assert "weather_service" in search_text
        assert "weather" in search_text
        assert "information" in search_text
        assert "forecast" in search_text

    def test_schema_structure(self):
        tool = MockWeatherTool()
        schema = tool.schema

        assert schema["name"] == "weather_service"
        assert schema["description"] == "Get current weather information for a specific location"
        assert schema["category"] == "information"
        assert "parameters" in schema
        assert schema["parameters"]["type"] == "object"

    def test_schema_parameters(self):
        tool = MockWeatherTool()
        schema = tool.schema
        properties = schema["parameters"]["properties"]
        required = schema["parameters"]["required"]

        assert "location" in properties
        assert "unit" in properties
        assert properties["location"]["type"] == "string"
        assert properties["unit"]["default"] == "celsius"
        assert "location" in required
        assert "unit" not in required

    def test_tool_convenience_properties(self):
        tool = MockWeatherTool()

        assert tool.name == "weather_service"
        assert tool.category == "information"
        assert "weather" in tool.description.lower()


class TestToolExecution:

    def test_execute_returns_dict(self):
        tool = MockWeatherTool()
        result = tool.execute(location="Istanbul")

        assert isinstance(result, dict)
        assert result["location"] == "Istanbul"
        assert result["temperature"] == 22

    def test_execute_without_optional_params(self):
        tool = MockWeatherTool()
        result = tool.execute(location="Ankara")

        assert result["location"] == "Ankara"
