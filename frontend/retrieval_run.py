import os
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

# Django API base URL
DJANGO_API = os.getenv("API_BASE")

st.set_page_config(page_title="Insurance RAG - Retrieval", page_icon="🔍")

st.title("🔍 Insurance Document Retrieval")

# Initialize session state
if 'selected_query' not in st.session_state:
    st.session_state.selected_query = ""

# Configuration sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Auto-detect ChromaDB directories (relative path for portability)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)  # Go up from frontend to project root
    base_output_dir = os.path.join(project_root, "media", "output")
    chroma_base_dir = os.path.join(base_output_dir, "chroma_db")
    print("ChromaDB base directory:", chroma_base_dir)
    # Get available ChromaDB directories
    available_dirs = []
    if os.path.exists(chroma_base_dir):
        for item in os.listdir(chroma_base_dir):
            item_path = os.path.join(chroma_base_dir, item)
            if os.path.isdir(item_path):
                available_dirs.append(item)
    
    if available_dirs:
        selected_doc = st.selectbox(
            "Select Document Collection",
            available_dirs,
            help="Choose which document collection to query"
        )
        chroma_db_dir = os.path.join(chroma_base_dir, selected_doc)
    else:
        st.warning("⚠️ No ChromaDB collections found")
        chroma_db_dir = st.text_input(
            "ChromaDB Directory (Manual)",
            value="",
            help="Manually enter the path to your ChromaDB directory"
        )
    
    k_results = st.slider("Number of results", min_value=1, max_value=20, value=5)
    
    # Document type filtering
    st.subheader("🏷️ Document Filtering")
    doc_type_options = {
        "All Documents": None,
        "Policy Documents": "policy", 
        "Brochures": "brochure",
        "Prospectus": "prospectus",
        "Terms & Conditions": "terms"
    }
    selected_doc_type = st.selectbox(
        "Document Type",
        options=list(doc_type_options.keys()),
        help="Filter results by document type for more relevant answers"
    )
    doc_type_filter = doc_type_options[selected_doc_type]
    
    # Evaluation options
    st.subheader("📊 Evaluation")
    enable_evaluation = st.checkbox(
        "Enable Retrieval Evaluation",
        value=True,  # Changed to True by default
        help="Get detailed metrics about retrieval quality (may slow down responses)"
    )
    
    # if st.button("📈 View Evaluation Summary"):
    #     try:
    #         eval_resp = requests.get(f"{DJANGO_API}/retriever/evaluation-summary/", timeout=10)
    #         if eval_resp.status_code == 200:
    #             eval_data = eval_resp.json()
    #             st.success("✅ Evaluation data loaded")
                
    #             # Display evaluation metrics in sidebar
    #             if "total_evaluations" in eval_data:
    #                 st.metric("Total Evaluations", eval_data["total_evaluations"])
    #             if "avg_term_coverage" in eval_data:
    #                 st.metric("Avg Term Coverage", f"{eval_data['avg_term_coverage']:.1%}")
    #             if "avg_diversity" in eval_data:
    #                 st.metric("Avg Diversity", f"{eval_data['avg_diversity']:.3f}")
    #         else:
    #             st.warning("⚠️ No evaluation data available yet")
    #     except Exception as e:
    #         st.error(f"❌ Error loading evaluation: {str(e)}")
    
    # Django API Status
    st.subheader("🔗 Django API Status")
    try:
        resp = requests.get(f"{DJANGO_API}/retriever/query/", timeout=5)
        if resp.status_code in [200, 405]:  # 405 means endpoint exists but wrong method
            st.success("✅ Django API accessible")
        else:
            st.error(f"❌ Django API error: {resp.status_code}")
    except Exception as e:
        st.error(f"❌ Django API not accessible: {str(e)}")

# Main query interface
query = st.text_input(
    "Ask a question about the insurance document:",
    value=st.session_state.selected_query,
    placeholder="e.g., What vaccinations are covered for children?"
)

if st.button("🔍 Search", type="primary") and query:
    if not chroma_db_dir:
        st.error("Please provide a ChromaDB directory path")
    else:
        with st.spinner("Retrieving answer..."):
            try:
                # Call enhanced Django API
                api_payload = {
                    "query": query,
                    "chroma_db_dir": chroma_db_dir,
                    "k": k_results,
                    "evaluate": enable_evaluation
                }
                
                # Add document type filter if selected
                if doc_type_filter:
                    api_payload["doc_type"] = doc_type_filter
                    
                response = requests.post(
                    f"{DJANGO_API}/retriever/query/",
                    json=api_payload,
                    timeout=60 if enable_evaluation else 30  # Longer timeout for evaluation
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.subheader("📌 Answer")
                    st.write(result["answer"])
                    
                    st.subheader("📑 Sources")
                    
                    # Display evaluation metrics if available
                    if enable_evaluation and "evaluation" in result:
                        st.subheader("📊 Retrieval Evaluation")
                        eval_data = result["evaluation"]
                        
                        if not eval_data.get("error"):
                            # Create metrics columns
                            eval_col1, eval_col2, eval_col3 = st.columns(3)
                            
                            with eval_col1:
                                if "term_coverage" in eval_data:
                                    st.metric("Term Coverage", f"{eval_data['term_coverage']:.1%}")
                                if "avg_semantic_similarity" in eval_data:
                                    st.metric("Avg Similarity", f"{eval_data['avg_semantic_similarity']:.3f}")
                            
                            with eval_col2:
                                if "query_coverage" in eval_data:
                                    st.metric("Query Coverage", f"{eval_data['query_coverage']:.1%}")
                                if "diversity" in eval_data:
                                    st.metric("Diversity", f"{eval_data['diversity']:.3f}")
                            
                            with eval_col3:
                                if "covered_terms" in eval_data:
                                    st.metric("Covered Terms", f"{len(eval_data['covered_terms'])}/{eval_data.get('total_terms', 0)}")
                            
                            # Show covered terms if available
                            if eval_data.get("covered_terms"):
                                with st.expander("🔍 Query Term Analysis"):
                                    st.write("**Covered Terms:**", ", ".join(eval_data["covered_terms"]))
                                    
                            # Show semantic similarities if available
                            if eval_data.get("semantic_similarities"):
                                with st.expander("🧠 Semantic Similarity Scores"):
                                    similarities = eval_data["semantic_similarities"]
                                    for i, sim in enumerate(similarities, 1):
                                        st.write(f"Source {i}: {sim:.3f}")
                        else:
                            st.error(f"Evaluation Error: {eval_data['error']}")
                    
                    if result["sources"]:
                        for i, source in enumerate(result["sources"], 1):
                            # Enhanced source header with type and filtering info
                            source_type = source.get('type', 'Unknown')
                            source_header = f"Source {i} - {source_type.title()}"
                            if doc_type_filter:
                                source_header += f" [Filtered: {selected_doc_type}]"
                                
                            with st.expander(source_header):
                                # Source metadata
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    if source.get('page'):
                                        st.write(f"**Page:** {source['page']}")
                                    if source.get('table'):
                                        st.write(f"**Table:** {source['table']}")
                                    if source.get('row_index') is not None:
                                        st.write(f"**Row:** {source['row_index']}")
                                
                                with col2:
                                    st.write(f"**Type:** {source.get('type', 'Unknown')}")
                                    if source.get('chunking_method'):
                                        st.write(f"**Chunking:** {source['chunking_method'].upper()}")
                                    if source.get('chunk_idx') is not None:
                                        st.write(f"**Chunk ID:** {source['chunk_idx']}")
                                
                                # Content
                                st.write("**Content:**")
                                content = source.get('content', '')
                                if len(content) > 500:
                                    st.write(content[:500] + "...")
                                    # Show full content in a text area instead of nested expander
                                    if st.button(f"Show full content {i}", key=f"show_full_{i}"):
                                        st.text_area("Full Content", content, height=200, key=f"full_content_{i}")
                                else:
                                    st.write(content)
                    else:
                        st.info("No sources found")
                        
                else:
                    error_msg = response.json().get("error", "Unknown error") if response.headers.get('content-type') == 'application/json' else response.text
                    st.error(f"API Error ({response.status_code}): {error_msg}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Connection Error: {str(e)}")
                st.info("Make sure the Django server is running on the configured URL")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Sample queries section
st.divider()
st.subheader("💡 Sample Queries")

sample_queries = [
    "What vaccinations are covered for children?",
    "What is the claim process for hospitalization?", 
    "What are the annual check-up benefits?",
    "What is the family floater coverage?",
    "What are the premium payment options?",
    "What documents are required for claims?",
    "What is the waiting period for pre-existing conditions?",
    "What are the exclusions in the policy?"
]

cols = st.columns(3)
for i, sample in enumerate(sample_queries):
    with cols[i % 3]:
        if st.button(f"📝 {sample}", key=f"sample_{i}"):
            st.session_state.selected_query = sample
            st.rerun()
