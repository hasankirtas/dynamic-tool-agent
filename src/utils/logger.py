import enum


class AgentStep(str, enum.Enum):
    INTENT = "Intent Detection & Query Transform"
    RETRIEVAL = "Tool Retrieval"
    SELECTION = "Tool Selection & Planning"
    EXECUTION = "Tool Execution"
    SYNTHESIS = "Response Synthesis"
    DONE = "Done"


class AgentLogger:

    def __init__(self):
        self._logs: list[dict] = []

    def log(self, step: AgentStep, message: str, data: dict | None = None) -> None:
        entry = {"step": step.value, "message": message, "data": data or {}}
        self._logs.append(entry)
        self._print(entry)

    def _print(self, entry: dict) -> None:
        print(f"\n[{entry['step']}] {entry['message']}")
        if entry["data"]:
            for key, value in entry["data"].items():
                print(f"  {key}: {value}")

    def get_logs(self) -> list[dict]:
        return self._logs.copy()

    def clear(self) -> None:
        self._logs.clear()
