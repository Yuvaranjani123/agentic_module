"""
Agentic System Interface - ReAct Reasoning

Modular frontend showcasing ReAct-based agentic system.
"""
import os
import streamlit as st
import requests
from dotenv import load_dotenv
import uuid
from components.agentic import AgenticSettings, ReasoningDisplay, QueryInterface

load_dotenv()

# Configuration
DJANGO_API = os.getenv("API_BASE")

# Page configuration
st.set_page_config(
    page_title="Insurance RAG - Agentic System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for reasoning visualization
st.markdown("""
<style>
    .thought-box {
        background-color: #e3f2fd;
        border-left: 4px solid #2196F3;
        padding: 10px;
        margin: 6px 0;
        border-radius: 4px;
    }
    .action-box {
        background-color: #fff3e0;
        border-left: 4px solid #FF9800;
        padding: 10px;
        margin: 6px 0;
        border-radius: 4px;
    }
    .observation-box {
        background-color: #f1f8e9;
        border-left: 4px solid #8BC34A;
        padding: 10px;
        margin: 6px 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'react_response' not in st.session_state:
    st.session_state.react_response = None


def call_react_system(query: str, config: dict) -> dict:
    """Call ReAct agentic system API."""
    try:
        payload = {
            'query': query,
            'conversation_history': st.session_state.conversation_history,
            'enable_learning': True,
            **{k: v for k, v in config.items() if v is not None}
        }
        
        response = requests.post(
            f"{DJANGO_API}/agents/agentic/query/",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


# Initialize components
settings = AgenticSettings(DJANGO_API)
display = ReasoningDisplay()
query_interface = QueryInterface()

# Sidebar - Settings
config = settings.render_sidebar()

# Main content
st.title("🤖 Insurance RAG - Agentic System")
st.caption("Advanced multi-step reasoning with transparent decision-making")

# Expandable info section (not prominent)
with st.expander("ℹ️ About the Agentic System", expanded=False):
    st.markdown("""
    **ReAct Agentic System Features:**
    - 🧠 **Iterative Reasoning**: Thought-Action-Observation loop
    - 🔧 **Dynamic Tool Selection**: Chooses right tools based on reasoning
    - 📚 **Multi-Step Queries**: Handles complex, sequential tasks
    - 🎯 **Intent Learning**: Improves from user feedback
    - 👁️ **Full Transparency**: See complete reasoning process
    - 🎯 **Auto Product Detection**: Mention product name in query (e.g., "ActivFit") and agent auto-switches!
    
    **Best for queries like:**
    - "Calculate premium for age 35, then compare with ActivFit"
    - "Find coverage details for diabetes, then calculate premium for age 45"
    - "Compare premiums across all products and show the cheapest option"
    """)

st.info("💡 **Tip**: Ask complex questions that need multiple steps. The system will show you how it thinks!", icon="💡")

# Query interface
query, run_query, clear = query_interface.render_with_buttons()

# Handle actions
if clear:
    st.session_state.conversation_history = []
    st.session_state.react_response = None
    st.rerun()

if run_query and query:
    with st.spinner("🧠 ReAct agent thinking..."):
        result = call_react_system(query, config)
        if result and result.get('success'):
            st.session_state.react_response = result
            # Update conversation history
            st.session_state.conversation_history.extend([
                {'role': 'user', 'content': query},
                {'role': 'assistant', 'content': result.get('final_answer', '')}
            ])
            st.rerun()

# Display results
if st.session_state.react_response:
    st.divider()
    display.render_complete_response(st.session_state.react_response)

# Footer
st.divider()
st.caption("🤖 Agentic System | ReAct Reasoning + Learning + Dynamic Tool Selection")
