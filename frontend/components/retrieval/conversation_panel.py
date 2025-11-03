"""
Conversation Panel Component

Displays conversation history in a clean, professional format.
"""
import streamlit as st


class ConversationPanel:
    """Clean conversation history display."""
    
    def render(self, history: list):
        """
        Render conversation history.
        
        Args:
            history: List of conversation exchanges
        """
        if not history:
            st.info("No conversation history yet. Ask a question to start!")
            return
        
        st.subheader(f"💬 History ({len(history)} messages)")
        
        # Display in reverse chronological order
        for i, exchange in enumerate(reversed(history), 1):
            self._render_exchange(exchange, len(history) - i + 1)
    
    def _render_exchange(self, exchange: dict, index: int):
        """Render a single conversation exchange."""
        with st.container():
            # Question
            st.markdown(f"**Q{index}:** {exchange['question']}")
            
            # Answer (truncated with expand option)
            answer = exchange['answer']
            if len(answer) > 200:
                st.markdown(f"> {answer[:200]}...")
                with st.expander("Show full answer"):
                    st.markdown(answer)
            else:
                st.markdown(f"> {answer}")
            
            st.divider()
    
    def render_in_sidebar(self, history: list, max_show: int = 3):
        """
        Render compact history in sidebar.
        
        Args:
            history: List of conversation exchanges
            max_show: Maximum exchanges to show
        """
        if not history:
            return
        
        st.subheader(f"💬 Recent ({len(history)})")
        
        # Show most recent exchanges
        recent = list(reversed(history))[:max_show]
        
        for exchange in recent:
            with st.container():
                st.caption(f"Q: {exchange['question'][:50]}...")
                st.caption(f"A: {exchange['answer'][:50]}...")
                st.divider()
        
        if len(history) > max_show:
            st.caption(f"+ {len(history) - max_show} more...")
