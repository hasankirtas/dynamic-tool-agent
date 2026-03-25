import json
from typing import Callable, Generator
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
        tool_results = []

        for tool_call in selected_tools:
            tool_name = tool_call.get("name")
            parameters = tool_call.get("parameters", {})

            update_status(f"⚙️ Action triggered! Activating tool: {tool_name}...")
            self.logger.log(
                AgentStep.EXECUTION,
                f"Executing tool: '{tool_name}'",
                {"parameters": parameters},
            )

            tool = self.registry.get_tool(tool_name)
            if tool:
                result = tool.execute(**parameters)
                tool_results.append({"tool": tool_name, "result": result})
                self.logger.log(AgentStep.EXECUTION, f"Tool '{tool_name}' executed successfully.", {"result": result})
            else:
                self.logger.log(AgentStep.EXECUTION, f"Tool '{tool_name}' not found in registry.")

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
