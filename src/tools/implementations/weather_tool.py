from typing import Any
from src.tools.abstraction.base_tool import BaseTool, ToolMetadata, ToolParameter


class WeatherTool(BaseTool):

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="weather_service",
            description="Get current weather information for a specific location including temperature, humidity, wind speed and general conditions",
            category="information",
            tags=["weather", "temperature", "forecast", "climate", "location"],
            parameters=[
                ToolParameter(name="location", type="string", description="City name or coordinates (e.g. 'Istanbul' or '41.0082,28.9784')"),
                ToolParameter(name="unit", type="string", description="Temperature unit: 'celsius' or 'fahrenheit'", required=False, default="celsius"),
            ],
        )

    def execute(self, **kwargs) -> dict[str, Any]:
        location = kwargs.get("location", "Unknown")
        unit = kwargs.get("unit", "celsius")
        temp = 22 if unit == "celsius" else 72
        return {
            "status": "success",
            "location": location,
            "temperature": temp,
            "unit": unit,
            "humidity": 45,
            "wind_speed": "15 km/h",
            "condition": "Partly Cloudy",
        }
