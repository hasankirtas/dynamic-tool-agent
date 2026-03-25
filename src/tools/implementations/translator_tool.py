from typing import Any
from src.tools.abstraction.base_tool import BaseTool, ToolMetadata, ToolParameter


class TranslatorTool(BaseTool):

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="translator",
            description="Translate text from one language to another, supporting major world languages",
            category="language",
            tags=["translate", "language", "text", "localization", "multilingual"],
            parameters=[
                ToolParameter(name="text", type="string", description="Text to translate"),
                ToolParameter(name="source_language", type="string", description="Source language code (e.g. 'en', 'tr', 'de')", required=False, default="auto"),
                ToolParameter(name="target_language", type="string", description="Target language code (e.g. 'en', 'tr', 'fr')"),
            ],
        )

    def execute(self, **kwargs) -> dict[str, Any]:
        text = kwargs.get("text", "")
        source = kwargs.get("source_language", "auto")
        target = kwargs.get("target_language", "en")
        mock_translations = {"en": "Hello, how are you?", "tr": "Merhaba, nasılsınız?", "fr": "Bonjour, comment allez-vous?", "de": "Hallo, wie geht es Ihnen?"}
        return {
            "status": "success",
            "original_text": text,
            "translated_text": mock_translations.get(target, f"[Translated to {target}]: {text}"),
            "source_language": source,
            "target_language": target,
        }
