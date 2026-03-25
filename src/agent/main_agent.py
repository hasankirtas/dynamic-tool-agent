import json
from typing import Any, Callable, Generator
from src.agent.prompts import (
    build_intent_messages,
    build_tool_selection_messages,
    build_final_answer_messages,
)
from src.tools.registry import ToolRegistry
from src.utils.llm import LLMClient
from src.utils.logger import AgentLogger, AgentStep


class MainAgent:
    """
    Orchestrates the dynamic tool selection and execution flow.
    Follows a zero-knowledge approach where tools are discovered and loaded on-demand.
    """

    def __init__(self, registry: ToolRegistry):
        """Initializes the agent with a central tool registry and LLM client."""
        self.registry = registry
        self.llm = LLMClient()
        self.logger = AgentLogger()
        self.conversation_history: list[dict] = []

    def run(self, user_message: str) -> str:
        """
        Synchronous execution entry point for backward compatibility.
        Consumes the run_stream generator and returns the full response.
        """
        return "".join(list(self.run_stream(user_message)))

    def run_stream(self, user_message: str, status_cb: Callable[[str], None] | None = None) -> Generator[str, None, None]:
        """
        Main execution pipeline supporting real-time status updates and streaming output.
        Pipeline: Intent Detection -> Tool Retrieval -> Selection -> Execution -> Synthesis.
        """
        self.logger.clear()

        def update_status(msg: str):
            if status_cb:
                status_cb(msg)

        # Stage 1: Intent Detection and Query Transformation
        update_status("🔍 Analyzing intent and deciding tool requirement...")
        self.logger.log(AgentStep.INTENT, f"Analyzing user request: '{user_message}'")

        intent_response = self.llm.chat_with_json(
            build_intent_messages(user_message)
        )

        try:
            intent = json.loads(intent_response)
        except json.JSONDecodeError:
            intent = {"requires_tool": False, "small_talk_response": intent_response}

        requires_tool = intent.get("requires_tool", False)
        search_query = intent.get("search_query")
        small_talk_response = intent.get("small_talk_response")

        self.logger.log(
            AgentStep.INTENT,
            "Intent analysis complete.",
            {"requires_tool": requires_tool, "search_query": search_query},
        )

        if not requires_tool:
            update_status("💬 Task resolved as conversation. Generating reply...")
            final_response = small_talk_response or "Hello! I'm an AI assistant with access to multiple tools. How can I help you today?"
            self._update_history(user_message, final_response)
            self.logger.log(AgentStep.DONE, "Responded with small talk (no tool required).")
            # For small talk, we didn't use streaming initially, so we just yield the whole block
            # To be fancy, we could yield char by char, but just yielding the string is fine.
            yield final_response
            return

        # Stage 2: Tool Retrieval
        update_status(f"📚 Querying ChromaDB Vector Engine for: '{search_query}'...")
        self.logger.log(AgentStep.RETRIEVAL, f"Searching tool registry with query: '{search_query}'")

        candidate_tools = self.registry.search(query=search_query, top_k=5)

        self.logger.log(
            AgentStep.RETRIEVAL,
            f"Retrieved {len(candidate_tools)} candidate tool(s).",
            {"candidates": [t["name"] for t in candidate_tools]},
        )

        # Stage 3: Tool Selection (LLM-based Routing)
        update_status("🧠 Reasoning over retrieved tools and building execution plan...")
        self.logger.log(AgentStep.SELECTION, "Evaluating candidate tools for task fit...")

        slim_candidates = [
            {"name": t["name"], "description": t["description"], "relevance_score": t["relevance_score"], "schema": t["schema"]}
            for t in candidate_tools
        ]

        selection_response = self.llm.chat_with_json(
            build_tool_selection_messages(user_message, slim_candidates)
        )

        try:
            selection = json.loads(selection_response)
        except json.JSONDecodeError:
            selection = {"can_fulfill": False, "cannot_fulfill_response": "I was unable to plan the tool execution."}

        can_fulfill = selection.get("can_fulfill", False)
        cannot_fulfill_response = selection.get("cannot_fulfill_response")

        self.logger.log(
            AgentStep.SELECTION,
            "Tool selection complete.",
            {"can_fulfill": can_fulfill, "reasoning": selection.get("reasoning", "")},
        )

        if not can_fulfill:
            update_status("🛡️ Hallucination Guard engaged. Gracefully rejecting task...")
            final_response = cannot_fulfill_response or "I don't have the capability to handle this request with my current tools."
            self._update_history(user_message, final_response)
            self.logger.log(AgentStep.DONE, "No suitable tool found — responding gracefully.")
            yield final_response
            return

        # Stage 4: Tool Execution
        selected_tools = selection.get("selected_tools", [])
        if can_fulfill and not selected_tools:
            update_status("🛡️ Tool plan missing. Gracefully rejecting task...")
            final_response = cannot_fulfill_response or "I don't have a valid execution plan for this request with my current tools."
            self._update_history(user_message, final_response)
            self.logger.log(AgentStep.DONE, "can_fulfill=true but selected_tools is empty.")
            yield final_response
            return

        tool_results = []

        def coerce_param_value(raw_value: Any, expected_type: str) -> tuple[bool, Any, str]:
            # Best-effort type coercion for tool parameters.
            if raw_value is None:
                return False, None, "Parameter value is null"

            if expected_type == "string":
                if isinstance(raw_value, str):
                    return True, raw_value, ""
                return True, str(raw_value), ""

            if expected_type == "integer":
                if isinstance(raw_value, bool):
                    return False, None, "Expected integer, got boolean"
                if isinstance(raw_value, int):
                    return True, raw_value, ""
                if isinstance(raw_value, str) and raw_value.strip().isdigit():
                    return True, int(raw_value.strip()), ""
                return False, None, f"Expected integer, got {type(raw_value).__name__}"

            if expected_type == "number":
                if isinstance(raw_value, (int, float)) and not isinstance(raw_value, bool):
                    return True, float(raw_value), ""
                if isinstance(raw_value, str):
                    try:
                        return True, float(raw_value), ""
                    except ValueError:
                        return False, None, f"Expected number, got string '{raw_value}'"
                return False, None, f"Expected number, got {type(raw_value).__name__}"

            if expected_type == "boolean":
                if isinstance(raw_value, bool):
                    return True, raw_value, ""
                if isinstance(raw_value, str):
                    v = raw_value.strip().lower()
                    if v in {"true", "1", "yes", "y"}:
                        return True, True, ""
                    if v in {"false", "0", "no", "n"}:
                        return True, False, ""
                return False, None, f"Expected boolean, got {type(raw_value).__name__}"

            # Unknown type: pass-through to avoid breaking prototypes.
            return True, raw_value, ""

        def validate_and_prepare_params(tool_name: str, tool: Any, params: dict[str, Any]) -> tuple[bool, dict[str, Any], str]:
            # Validate required params and coerce basic types.
            try:
                metadata = tool.metadata
            except Exception:
                return False, {}, f"Tool '{tool_name}' does not expose metadata"

            clean_params: dict[str, Any] = dict(params or {})

            for p in metadata.parameters:
                param_name = p.name
                expected_type = p.type
                is_required = bool(p.required)
                has_value = param_name in clean_params and clean_params[param_name] is not None

                if not has_value:
                    if is_required:
                        return False, {}, f"Missing required parameter '{param_name}' for tool '{tool_name}'"
                    if p.default is not None:
                        clean_params[param_name] = p.default
                    continue

                ok, coerced, err = coerce_param_value(clean_params[param_name], expected_type)
                if not ok:
                    return False, {}, f"Invalid parameter '{param_name}': {err}"
                clean_params[param_name] = coerced

            return True, clean_params, ""

        for tool_call in selected_tools:
            tool_name = tool_call.get("name")
            parameters = tool_call.get("parameters", {})

            update_status(f"⚙️ Action triggered! Activating tool: {tool_name}...")
            self.logger.log(
                AgentStep.EXECUTION,
                f"Executing tool: '{tool_name}'",
                {"parameters": parameters},
            )

            if not tool_name:
                tool_results.append({"tool": None, "result": {"status": "error", "error": "Tool name is missing"}})
                continue

            tool = self.registry.get_tool(tool_name)
            if tool:
                ok, prepared_params, err = validate_and_prepare_params(tool_name, tool, parameters)
                if not ok:
                    result = {"status": "error", "error": err}
                    tool_results.append({"tool": tool_name, "result": result})
                    self.logger.log(AgentStep.EXECUTION, f"Tool '{tool_name}' parameter validation failed.", {"result": result})
                    continue

                try:
                    result = tool.execute(**prepared_params)
                except Exception as e:
                    result = {"status": "error", "error": str(e)}

                tool_results.append({"tool": tool_name, "result": result})
                self.logger.log(AgentStep.EXECUTION, f"Tool '{tool_name}' executed.", {"result": result})
            else:
                self.logger.log(AgentStep.EXECUTION, f"Tool '{tool_name}' not found in registry.")
                tool_results.append({"tool": tool_name, "result": {"status": "error", "error": "Tool not found in registry"}})

        # Stage 5: Response Synthesis (STREAMING)
        update_status("✍️ Formulating natural language response streams...")
        self.logger.log(AgentStep.SYNTHESIS, "Synthesizing final response from tool results...")

        messages = build_final_answer_messages(user_message, tool_results, self.conversation_history)
        
        full_response = ""
        for chunk in self.llm.chat_stream(messages):
            full_response += chunk
            yield chunk

        self._update_history(user_message, full_response)
        self.logger.log(AgentStep.DONE, "Response delivered to user.")

    def _update_history(self, user_message: str, assistant_response: str) -> None:
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": assistant_response})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
