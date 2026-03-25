import streamlit as st
import time
from src.tools.registry import ToolRegistry
from src.agent.main_agent import MainAgent


# --- PAGE CONFIG ---
st.set_page_config(
    page_title="UtaiSOFT Case Study - Hasan Kırtaş",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM CSS FOR PREMIUM LOOK ---
st.markdown("""
<style>
    .log-entry { font-family: 'Courier New', monospace; font-size: 0.85em; background-color: #1e1e1e; padding: 10px; border-radius: 5px; margin-bottom: 5px; }
    .log-step { color: #f39c12; font-weight: bold; }
    .log-data { color: #2ecc71; margin-left: 20px; }
    .tool-card { border-left: 4px solid #3498db; padding: 10px; background-color: #2c3e50; border-radius: 4px; margin-bottom: 5px; }
    .tool-name { font-weight: bold; color: #ecf0f1; }
    .tool-cat { font-size: 0.8em; color: #bdc3c7; background: #34495e; padding: 2px 6px; border-radius: 10px; }
    .branding { font-size: 0.8em; color: #95a5a6; text-align: center; margin-top: 50px; }
</style>
""", unsafe_allow_html=True)


# --- INITIALIZATION ---
@st.cache_resource
def get_or_create_registry():
    """Cache the registry to avoid re-initializing ChromaDB on every render"""
    registry = ToolRegistry(db_path="./app_chroma_db")
    count = registry.register_all()
    return registry, count

registry, initial_tool_count = get_or_create_registry()

if "agent" not in st.session_state:
    st.session_state.agent = MainAgent(registry=registry)
if "messages" not in st.session_state:
    st.session_state.messages = []


# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Orchestrator Status")
    st.success("DeepSeek-V3.2 Engine: **ONLINE**")
    st.success(f"ChromaDB Registry: **ONLINE**")
    
    st.divider()
    st.subheader(f"🛠️ Discovered Tools ({initial_tool_count})")
    
    tools = sorted(registry._tools.values(), key=lambda t: t.category)
    categories = {}
    for t in tools:
        categories.setdefault(t.category, []).append(t)
        
    for cat, items in categories.items():
        with st.expander(cat.upper(), expanded=False):
            for t in items:
                st.markdown(f"""
                <div class="tool-card">
                    <span class="tool-name">{t.name}</span><br/>
                    <small style='color: #95a5a6;'>{t.description[:60]}...</small>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<div class='branding'>🤖 Dynamic Agent Architecture<br/>Developed by <b>Hasan Kırtaş</b><br/>for <i>UtaiSOFT AI Case Study</i></div>", unsafe_allow_html=True)

# --- MAIN CHAT AREA ---
st.title("🚀 UtaiSOFT Agent Interface")
st.markdown("*Dynamic Tool Selection & Capability Discovery for AI Agents*")

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "logs" in msg and msg["logs"]:
            with st.expander("👁️ View Internal Reasoning (Execution Detail)", expanded=False):
                for log in msg["logs"]:
                    st.markdown(f"**[{log['step']}]**: {log['message']}")
                    if log['data']:
                        st.json(log['data'])

# User input
if prompt := st.chat_input("Ask a question, request a task, or test hallucination guard..."):
    # 1. Show user message
    st.session_state.messages.append({"role": "user", "content": prompt, "logs": []})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Process Assistant Response
    with st.chat_message("assistant"):
        # UI Placeholder for dynamic thinking steps
        status_text = st.empty()
        
        def status_callback(msg: str):
            status_text.markdown(f"*{msg}*")
            
        try:
            start_time = time.time()
            
            # This calls the generator function which streams the execution process
            stream_generator = st.session_state.agent.run_stream(prompt, status_cb=status_callback)
            
            # Streamlit writes the generator content dynamically just like ChatGPT
            response_container = st.empty()
            full_response = ""
            for chunk in stream_generator:
                full_response += chunk
                response_container.markdown(full_response + "▌")
            
            # Remove cursor once streaming is done
            response_container.markdown(full_response)
            
            # Clear the loading text
            status_text.empty()
            
            duration = time.time() - start_time
            
            # Extract logs generated during this run
            run_logs = st.session_state.agent.logger.get_logs()
            
            with st.expander(f"👁️ View Internal Reasoning ({duration:.1f}s)", expanded=False):
                for log in run_logs:
                    st.markdown(f"**[{log['step'].upper()}]**: {log['message']}")
                    if log['data']:
                        st.json(log['data'])
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "logs": run_logs
            })
            
        except Exception as e:
            status_text.error(f"Execution sequence failed: {str(e)}")
