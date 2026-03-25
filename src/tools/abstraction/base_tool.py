from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """
    Schema definition for a single tool input parameter.
    Used for automated validation and generating LLM instructions.
    """
    name: str
    type: str # e.g., 'string', 'number', 'boolean'
    description: str
    required: bool = True
    default: Any = None


class ToolMetadata(BaseModel):
    """
    Core metadata for a tool, utilized for vector search and intent matching.
    Includes classification and parameter schema definitions.
    """
    name: str
    description: str
    category: str
    tags: list[str] = Field(default_factory=list)
    parameters: list[ToolParameter] = Field(default_factory=list)

    def to_search_text(self) -> str:
        """Generates a text index for the vector database to optimize retrieval."""
        return f"{self.name}: {self.description}. Category: {self.category}. Tags: {', '.join(self.tags)}"

    def to_schema(self) -> dict:
        """Generates a JSON schema compatible with LLM tool selection logic."""
        properties = {}
        required_fields = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description,
            }
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.required:
                required_fields.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required_fields,
            },
        }


class BaseTool(ABC):
    """
    Abstract Base Class for all tools.
    Provides a standardized interface for execution and metadata generation.
    """

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        pass

    @abstractmethod
    def execute(self, **kwargs) -> dict[str, Any]:
        pass

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def description(self) -> str:
        return self.metadata.description

    @property
    def category(self) -> str:
        return self.metadata.category

    @property
    def schema(self) -> dict:
        return self.metadata.to_schema()
