from typing import Any
from src.tools.abstraction.base_tool import BaseTool, ToolMetadata, ToolParameter


class DocumentReaderTool(BaseTool):

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="document_reader",
            description="Read and extract text content from documents at a given URL, supporting PDF, TXT, and DOCX file formats",
            category="information",
            tags=["document", "pdf", "reader", "file", "text", "extract", "url"],
            parameters=[
                ToolParameter(name="url", type="string", description="URL of the document to read"),
                ToolParameter(name="format", type="string", description="Document format: 'pdf', 'txt', or 'docx'", required=False, default="pdf"),
            ],
        )

    def execute(self, **kwargs) -> dict[str, Any]:
        url = kwargs.get("url", "")
        doc_format = kwargs.get("format", "pdf")
        return {
            "status": "success",
            "url": url,
            "format": doc_format,
            "content": f"[Extracted content from {doc_format.upper()} document at {url}]\n\nLorem ipsum dolor sit amet, consectetur adipiscing elit. This is a simulated document extraction result.",
            "page_count": 3,
        }
