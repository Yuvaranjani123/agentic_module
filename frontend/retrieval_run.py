"""
Insurance Document Retrieval - Clean Professional Interface

A minimalist, professional UI for document retrieval with conversation support.
"""
import os
import streamlit as st
import requests
from dotenv import load_dotenv
from components.retrieval import (
    QueryInterface,
    ResultsDisplay,
    SettingsPanel,
    ConversationPanel
)

load_dotenv()

# Configuration
DJANGO_API = os.getenv("API_BASE")

# Page configuration
st.set_page_config(
    page_title="Insurance RAG - Retrieval",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'conversation_id' not in st.session_state:
    import uuid
    st.session_state.conversation_id = str(uuid.uuid4())

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Initialize components
query_interface = QueryInterface()
results_display = ResultsDisplay()
settings_panel = SettingsPanel()
conversation_panel = ConversationPanel()

# Render settings sidebar
config = settings_panel.render_sidebar()

# Main content area
st.title("🔍 Document Retrieval")
st.caption("Ask questions about insurance documents with AI-powered search")

# Query interface
st.divider()
query, is_submitted = query_interface.render_with_button(
    placeholder_text="Ask about coverage, benefits, exclusions, claims..."
)

# Process query
if is_submitted and query:
    if not config.get('chroma_db_dir'):
        results_display.render_error(
            "No product database found. Please run ingestion first."
        )
    else:
        with st.spinner("Searching documents..."):
            try:
                # Build API payload
                payload = {
                    "query": query,
                    "chroma_db_dir": config['chroma_db_dir'],
                    "k": config['k_results'],
                    "evaluate_retrieval": config['enable_evaluation'],
                    "conversation_id": st.session_state.conversation_id
                }
                
                # Add filters if set
                if config.get('doc_type_filter'):
                    payload['doc_type_filter'] = config['doc_type_filter']
                if config.get('exclude_doc_types'):
                    payload['exclude_doc_types'] = config['exclude_doc_types']
                
                # Call API
                response = requests.post(
                    f"{DJANGO_API}/agents/query/",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Display answer
                    results_display.render_answer(
                        data['answer'],
                        data.get('evaluation')
                    )
                    
                    # Display sources
                    results_display.render_sources(data.get('sources', []))
                    
                    # Update conversation history
                    st.session_state.conversation_history.append({
                        'question': query,
                        'answer': data['answer']
                    })
                
                else:
                    results_display.render_error(
                        f"API error: {response.status_code}"
                    )
            
            except requests.Timeout:
                results_display.render_error(
                    "Request timed out. Please try again."
                )
            except Exception as e:
                results_display.render_error(f"Error: {str(e)}")

# Conversation history (in expandable section)
if st.session_state.conversation_history:
    st.divider()
    with st.expander("💬 Conversation History", expanded=False):
        conversation_panel.render(st.session_state.conversation_history)

# Footer
st.divider()
st.caption(
    "💡 Tip: Use the sidebar to adjust settings, switch products, "
    "or start a new conversation"
)
