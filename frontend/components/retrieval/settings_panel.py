"""
Settings Panel Component

Clean, collapsible settings panel for retrieval configuration.
"""
import streamlit as st
import os


class SettingsPanel:
    """Professional settings panel with progressive disclosure."""
    
    def __init__(self):
        """Initialize settings panel."""
        self.available_products = []
        self.chroma_db_dir = None
    
    def render_sidebar(self):
        """
        Render settings sidebar with clean, minimal design.
        
        Returns:
            Dict with configuration settings
        """
        with st.sidebar:
            st.header("⚙️ Settings")
            
            # Product selection
            config = self._render_product_selection()
            
            # Basic settings
            config['k_results'] = st.slider(
                "Results to retrieve",
                min_value=1,
                max_value=20,
                value=5,
                help="Number of document chunks to retrieve"
            )
            
            # Advanced settings (collapsed by default)
            with st.expander("🔧 Advanced", expanded=False):
                advanced_config = self._render_advanced_settings()
                config.update(advanced_config)
            
            # Evaluation toggle
            config['enable_evaluation'] = st.checkbox(
                "Show quality metrics",
                value=False,
                help="Display retrieval quality metrics with results"
            )
            
            # Conversation controls
            self._render_conversation_controls()
            
            # API status
            self._render_api_status()
            
            return config
    
    def _render_product_selection(self):
        """Render clean product selection UI."""
        config = {}
        
        # Auto-detect products
        self.available_products, base_dir = self._detect_products()
        
        if not self.available_products:
            st.error("No product databases found")
            st.info("Run ingestion first")
            config['chroma_db_dir'] = None
            config['selected_product'] = None
            return config
        
        # Initialize selection
        if 'selected_product' not in st.session_state:
            st.session_state.selected_product = self.available_products[0]
        
        # Single product - just show info
        if len(self.available_products) == 1:
            product = self.available_products[0]
            st.success(f"📦 {product}")
            config['chroma_db_dir'] = os.path.join(base_dir, product)
            config['selected_product'] = product
        
        # Multiple products - show selector
        else:
            product = st.selectbox(
                "Product Database",
                self.available_products,
                index=self.available_products.index(
                    st.session_state.selected_product
                ),
                help="Select product to query"
            )
            st.session_state.selected_product = product
            config['chroma_db_dir'] = os.path.join(base_dir, product)
            config['selected_product'] = product
        
        return config
    
    def _render_advanced_settings(self):
        """Render advanced settings in collapsed section."""
        config = {}
        
        # Document type filtering
        st.caption("**Document Type Filtering**")
        filter_mode = st.radio(
            "Filter Mode",
            ["All Documents", "Include Types", "Exclude Types"],
            help="Filter by document type",
            label_visibility="collapsed"
        )
        
        doc_types = [
            "policy", "brochure", "prospectus", "terms",
            "premium-calculation", "claim-form"
        ]
        
        if filter_mode == "Include Types":
            selected = st.multiselect(
                "Include",
                doc_types,
                help="Only search these types"
            )
            config['doc_type_filter'] = selected if selected else None
            config['exclude_doc_types'] = []
        
        elif filter_mode == "Exclude Types":
            excluded = st.multiselect(
                "Exclude",
                doc_types,
                help="Exclude these types"
            )
            config['doc_type_filter'] = None
            config['exclude_doc_types'] = excluded
        
        else:
            config['doc_type_filter'] = None
            config['exclude_doc_types'] = []
        
        return config
    
    def _render_conversation_controls(self):
        """Render conversation memory controls."""
        st.divider()
        st.subheader("💬 Conversation")
        
        if 'conversation_id' not in st.session_state:
            import uuid
            st.session_state.conversation_id = str(uuid.uuid4())
        
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
        
        # Show history count
        hist_count = len(st.session_state.conversation_history)
        st.caption(f"Messages: {hist_count}")
        
        # Clear button
        if st.button("🔄 New Conversation", use_container_width=True):
            import uuid
            st.session_state.conversation_id = str(uuid.uuid4())
            st.session_state.conversation_history = []
            st.success("New conversation started")
            st.rerun()
    
    def _render_api_status(self):
        """Render API status indicator."""
        st.divider()
        
        try:
            import requests
            api_base = os.getenv("API_BASE")
            resp = requests.get(f"{api_base}/agents/query/", timeout=5)
            
            if resp.status_code in [200, 405]:
                st.caption("🟢 API Online")
            else:
                st.caption("🔴 API Error")
        except:
            st.caption("🔴 API Offline")
    
    def _detect_products(self):
        """
        Detect available product databases.
        
        Returns:
            Tuple of (products_list, base_directory)
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up from components/retrieval to frontend, then to project root
        frontend_dir = os.path.dirname(os.path.dirname(current_dir))
        project_root = os.path.dirname(frontend_dir)
        
        base_output = os.path.join(project_root, "media", "output")
        chroma_base = os.path.join(base_output, "chroma_db")
        
        products = []
        if os.path.exists(chroma_base):
            for item in os.listdir(chroma_base):
                item_path = os.path.join(chroma_base, item)
                if os.path.isdir(item_path):
                    db_file = os.path.join(item_path, "chroma.sqlite3")
                    if os.path.exists(db_file):
                        products.append(item)
        
        return products, chroma_base
