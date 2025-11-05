"""
Query Interface Component

Query input and submission interface for agentic system.
"""
import streamlit as st


class QueryInterface:
    """Query input interface for agentic system."""
    
    def render_query_input(self):
        """
        Render query input area with help text.
        
        Returns:
            Tuple of (query_text, None) - compatible with button rendering
        """
        query = st.text_area(
            "**Enter your insurance query:**",
            placeholder="Example: What is maternity coverage in ActivFit? OR Calculate premium for ActivAssure age 32",
            height=100,
            help="💡 Smart Tip: Mention product name (ActivAssure, ActivFit, etc.) and agent auto-detects! Try: 'Calculate X, then compare with Y'"
        )
        
        return query, None
    
    def render_action_buttons(self):
        """
        Render action buttons (Run Query, Clear History).
        
        Returns:
            Tuple of (run_clicked, clear_clicked)
        """
        col1, col2, col3 = st.columns([2, 2, 3])
        
        with col1:
            run_query = st.button("🚀 Run Query", type="primary", use_container_width=True)
        with col2:
            clear = st.button("🗑️ Clear History", use_container_width=True)
        with col3:
            st.empty()
        
        return run_query, clear
    
    def render_with_buttons(self):
        """
        Render complete query interface with input and buttons.
        
        Returns:
            Tuple of (query_text, run_clicked, clear_clicked)
        """
        query, _ = self.render_query_input()
        run_query, clear = self.render_action_buttons()
        
        return query, run_query, clear
