from typing import Any
from src.tools.abstraction.base_tool import BaseTool, ToolMetadata, ToolParameter


class EmailSenderTool(BaseTool):

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="email_sender",
            description="Send an email to a specified recipient with subject and body content",
            category="communication",
            tags=["email", "send", "message", "mail", "notification", "contact"],
            parameters=[
                ToolParameter(name="to", type="string", description="Recipient email address"),
                ToolParameter(name="subject", type="string", description="Email subject line"),
                ToolParameter(name="body", type="string", description="Email body content"),
            ],
        )

    def execute(self, **kwargs) -> dict[str, Any]:
        to = kwargs.get("to", "")
        subject = kwargs.get("subject", "")
        return {
            "status": "success",
            "message": f"Email sent successfully to {to}",
            "to": to,
            "subject": subject,
            "timestamp": "2026-03-24T21:30:00Z",
        }
