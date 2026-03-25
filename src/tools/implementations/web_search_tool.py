from typing import Any
from src.tools.abstraction.base_tool import BaseTool, ToolMetadata, ToolParameter


class WebSearchTool(BaseTool):

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="web_search",
            description="Search the internet for current and up-to-date information on any topic",
            category="information",
            tags=["search", "internet", "web", "google", "browse", "query"],
            parameters=[
                ToolParameter(name="query", type="string", description="Search query string"),
                ToolParameter(name="num_results", type="integer", description="Number of results to return", required=False, default=5),
            ],
        )

    def execute(self, **kwargs) -> dict[str, Any]:
        query = kwargs.get("query", "")
        num_results = kwargs.get("num_results", 5)
        return {
            "status": "success",
            "query": query,
            "results": [
                {"title": f"Result {i+1} for '{query}'", "url": f"https://example.com/result{i+1}", "snippet": f"This is a relevant snippet about {query}..."}
                for i in range(min(num_results, 5))
            ],
        }
