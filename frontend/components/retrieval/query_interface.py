"""
Query Interface Component

Provides a clean, professional query interface for document retrieval.
"""
import streamlit as st


class QueryInterface:
    """Clean query interface with minimal, professional design."""
    
    def __init__(self):
        """Initialize query interface."""
        self.selected_query = ""
    
    def render(self, placeholder_text: str = None) -> str:
        """
        Render the query interface.
        
        Args:
            placeholder_text: Optional placeholder for the query input
            
        Returns:
            User's query text or empty string
        """
        # Use session state for selected query
        if 'selected_query' not in st.session_state:
            st.session_state.selected_query = ""
        
        default_placeholder = (
            "Ask a question about the insurance document... "
            "(e.g., What are the maternity benefits?)"
        )
        
        # Main query input with clean styling
        query = st.text_input(
            "Your Question",
            value=st.session_state.selected_query,
            placeholder=placeholder_text or default_placeholder,
            label_visibility="collapsed"
        )
        
        return query
    
    def render_with_button(self, placeholder_text: str = None):
        """
        Render query interface with search button.
        
        Args:
            placeholder_text: Optional placeholder
            
        Returns:
            Tuple of (query, is_submitted)
        """
        query = self.render(placeholder_text)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            is_submitted = st.button(
                "🔍 Search", 
                type="primary",
                use_container_width=True
            )
        
        with col2:
            if st.button("Clear", use_container_width=True):
                st.session_state.selected_query = ""
                st.rerun()
        
        return query, is_submitted
