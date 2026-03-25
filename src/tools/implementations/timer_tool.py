from typing import Any
from src.tools.abstraction.base_tool import BaseTool, ToolMetadata, ToolParameter


class TimerTool(BaseTool):

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="timer_alarm",
            description="Set a timer, alarm, or reminder for a specific duration or future time",
            category="productivity",
            tags=["timer", "alarm", "reminder", "countdown", "schedule", "notification"],
            parameters=[
                ToolParameter(name="action", type="string", description="Action type: 'timer', 'alarm', or 'reminder'"),
                ToolParameter(name="duration_minutes", type="integer", description="Duration in minutes (for timer)", required=False),
                ToolParameter(name="time", type="string", description="Target time in HH:MM format (for alarm)", required=False),
                ToolParameter(name="message", type="string", description="Reminder message", required=False, default="Time is up!"),
            ],
        )

    def execute(self, **kwargs) -> dict[str, Any]:
        action = kwargs.get("action", "timer")
        message = kwargs.get("message", "Time is up!")

        if action == "timer":
            duration = kwargs.get("duration_minutes", 5)
            return {"status": "success", "type": "timer", "duration_minutes": duration, "message": f"Timer set for {duration} minutes. Message: {message}"}
        elif action == "alarm":
            time = kwargs.get("time", "08:00")
            return {"status": "success", "type": "alarm", "time": time, "message": f"Alarm set for {time}. Message: {message}"}
        else:
            return {"status": "success", "type": "reminder", "message": message}
