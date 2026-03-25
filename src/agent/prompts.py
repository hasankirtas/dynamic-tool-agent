import json


INTENT_SYSTEM_PROMPT = """\
You are an intelligent intent analyzer for a multi-tool AI assistant.

Your job is to analyze the user's message and determine:
1. Does this request require an external tool or capability?
2. If yes, generate a highly optimized search query for retrieving the right tool from a vector database.

CRITICAL RULES:
- If the user is making small talk, asking how you are, or having a casual conversation → tools are NOT required.
- If the user asks for information, computation, data, file reading, communication, or any real-world action → tools ARE required.
- The search_query must describe the CAPABILITY needed, not repeat the user's message.
  EXAMPLE: User says "What's the weather like in Istanbul today?" → search_query: "get current weather conditions for a city"
  EXAMPLE: User says "Convert 100 USD to EUR" → search_query: "currency exchange rate conversion between currencies"
- Keep the search_query short, precise, and focused on the functional capability.

Return ONLY a valid JSON object with this exact structure:
{
  "requires_tool": true or false,
  "search_query": "optimized capability description string" or null,
  "small_talk_response": "A friendly and brief response if no tool is needed" or null
}
"""


TOOL_SELECTION_SYSTEM_PROMPT = """\
You are a precise tool selector for an AI assistant. You have retrieved a set of candidate tools \
from a vector database based on the user's request. Your job is to determine which tools are \
actually needed to fulfill the request.

CRITICAL RULES:
- Only select tools that are DIRECTLY necessary to complete the user's task.
- If NONE of the retrieved tools can fulfill the user's request, do NOT hallucinate or invent tools.
- You must evaluate each candidate tool honestly based on its schema and description.
- You may select multiple tools if the task genuinely requires them.

Return ONLY a valid JSON object:
{
  "can_fulfill": true or false,
  "reasoning": "Brief explanation of your decision",
  "selected_tools": [
    {
      "name": "tool_name_here",
      "parameters": { "param1": "value1", "param2": "value2" }
    }
  ],
  "cannot_fulfill_response": "Polite message explaining unavailable capability, or null if can_fulfill is true"
}
"""


FINAL_ANSWER_SYSTEM_PROMPT = """\
You are a helpful AI assistant. You have just executed one or more tools and received their results.
Synthesize the tool results into a clear, concise, and helpful response for the user.

RULES:
- Present the information naturally, as if you retrieved it yourself.
- Do not expose internal tool names, schemas, or raw JSON to the user.
- If a tool returned an error, acknowledge it gracefully and suggest alternatives.
- Be conversational and helpful.
"""


def build_intent_messages(user_message: str) -> list[dict]:
    return [
        {"role": "system", "content": INTENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


def build_tool_selection_messages(user_message: str, candidate_tools: list[dict]) -> list[dict]:
    tools_context = json.dumps(candidate_tools, indent=2)
    user_content = f"""\
User Request: {user_message}

Retrieved Candidate Tools (ranked by relevance):
{tools_context}

Evaluate these tools and decide which ones (if any) are needed to fulfill the request.
"""
    return [
        {"role": "system", "content": TOOL_SELECTION_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def build_final_answer_messages(
    user_message: str,
    tool_results: list[dict],
    conversation_history: list[dict],
) -> list[dict]:
    results_context = json.dumps(tool_results, indent=2)
    messages = [{"role": "system", "content": FINAL_ANSWER_SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({
        "role": "user",
        "content": f"""\
User Request: {user_message}

Tool Execution Results:
{results_context}

Please provide a natural, helpful response based on these results.
""",
    })
    return messages
