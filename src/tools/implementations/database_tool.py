from typing import Any
from src.tools.abstraction.base_tool import BaseTool, ToolMetadata, ToolParameter


class DatabaseQueryTool(BaseTool):

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="database_query",
            description="Execute SQL queries against a database to retrieve, filter, and aggregate structured data from tables",
            category="data",
            tags=["database", "sql", "query", "table", "select", "data", "records"],
            parameters=[
                ToolParameter(name="query", type="string", description="SQL query to execute (SELECT only)"),
                ToolParameter(name="database", type="string", description="Target database name", required=False, default="main"),
            ],
        )

    def execute(self, **kwargs) -> dict[str, Any]:
        query = kwargs.get("query", "")
        if not query.strip().upper().startswith("SELECT"):
            return {"status": "error", "error": "Only SELECT queries are allowed"}
        return {
            "status": "success",
            "query": query,
            "rows": [
                {"id": 1, "name": "Alice", "department": "Engineering"},
                {"id": 2, "name": "Bob", "department": "Marketing"},
                {"id": 3, "name": "Charlie", "department": "Engineering"},
            ],
            "row_count": 3,
        }
