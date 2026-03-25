from typing import Any
from src.tools.abstraction.base_tool import BaseTool, ToolMetadata, ToolParameter


class CalendarTool(BaseTool):

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="calendar_manager",
            description="Manage calendar events: create new events, list upcoming events, or check availability for a specific date and time",
            category="productivity",
            tags=["calendar", "schedule", "event", "meeting", "appointment", "date", "time"],
            parameters=[
                ToolParameter(name="action", type="string", description="Action to perform: 'create', 'list', or 'check'"),
                ToolParameter(name="date", type="string", description="Date in YYYY-MM-DD format"),
                ToolParameter(name="time", type="string", description="Time in HH:MM format", required=False),
                ToolParameter(name="title", type="string", description="Event title (required for 'create' action)", required=False),
            ],
        )

    def execute(self, **kwargs) -> dict[str, Any]:
        action = kwargs.get("action", "list")
        date = kwargs.get("date", "2026-03-25")

        if action == "create":
            return {"status": "success", "message": f"Event '{kwargs.get('title', 'Untitled')}' created on {date} at {kwargs.get('time', '09:00')}"}
        elif action == "check":
            return {"status": "success", "date": date, "available": True, "message": f"You are available on {date}"}
        else:
            return {
                "status": "success",
                "date": date,
                "events": [
                    {"title": "Team Standup", "time": "09:00", "duration": "30min"},
                    {"title": "Lunch Break", "time": "12:00", "duration": "1h"},
                ],
            }
