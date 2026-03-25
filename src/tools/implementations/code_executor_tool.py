import math
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
            # Minimal, whitelist-only execution.
            allowed_modules: dict[str, Any] = {"math": math}

            def safe_import(name: str, globals=None, locals=None, fromlist=(), level: int = 0):
                if name in allowed_modules:
                    return allowed_modules[name]
                raise ImportError(f"Module '{name}' is not allowed")

            printed: list[str] = []

            def safe_print(*args, **kwargs):
                # Capture print output (do not print to stdout).
                printed.append(" ".join(str(a) for a in args))

            safe_builtins = {"__import__": safe_import, "print": safe_print}

            exec_globals = {"__builtins__": safe_builtins, "math": math}
            local_vars: dict[str, Any] = {}

            exec(code, exec_globals, local_vars)

            if "result" not in local_vars:
                return {
                    "status": "error",
                    "error": "No 'result' variable defined by executed code",
                    "code": code,
                }

            return {
                "status": "success",
                "result": str(local_vars.get("result")),
                "code": code,
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "code": code}
