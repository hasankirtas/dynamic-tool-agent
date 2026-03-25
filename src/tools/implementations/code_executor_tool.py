from typing import Any
from src.tools.abstraction.base_tool import BaseTool, ToolMetadata, ToolParameter


class CodeExecutorTool(BaseTool):

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="code_executor",
            description="Execute Python code for complex mathematical calculations, data analysis and numerical computations",
            category="computation",
            tags=["math", "calculator", "python", "code", "computation", "analysis"],
            parameters=[
                ToolParameter(name="code", type="string", description="Python code to execute for the calculation"),
            ],
        )

    def execute(self, **kwargs) -> dict[str, Any]:
        code = kwargs.get("code", "")
        try:
            local_vars = {}
            exec(code, {"__builtins__": {}}, local_vars)
            return {"status": "success", "result": str(local_vars.get("result", "No 'result' variable defined")), "code": code}
        except Exception as e:
            return {"status": "error", "error": str(e), "code": code}
