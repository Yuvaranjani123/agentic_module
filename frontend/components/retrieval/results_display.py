"""
Results Display Component

Professional display of retrieval results with clean formatting.
"""
import streamlit as st


class ResultsDisplay:
    """Clean, professional results display."""
    
    def render_answer(self, answer: str, evaluation: dict = None):
        """
        Display the answer with optional evaluation metrics.
        
        Args:
            answer: Generated answer text
            evaluation: Optional evaluation metrics dict
        """
        st.subheader("💡 Answer")
        st.markdown(answer)
        
        # Show evaluation metrics in a clean expandable section
        if evaluation and evaluation.get('avg_semantic_similarity'):
            with st.expander("📊 Quality Metrics", expanded=False):
                self._render_evaluation_metrics(evaluation)
    
    def render_sources(self, sources: list, max_visible: int = 3):
        """
        Display source documents in a clean, expandable format.
        
        Args:
            sources: List of source documents
            max_visible: Number of sources to show initially
        """
        if not sources:
            return
        
        st.divider()
        st.subheader(f"📚 Sources ({len(sources)})")
        
        # Show first few sources
        for i, source in enumerate(sources[:max_visible], 1):
            self._render_source_card(source, i)
        
        # Expand to show all sources
        if len(sources) > max_visible:
            with st.expander(
                f"📄 View All {len(sources)} Sources", 
                expanded=False
            ):
                for i, source in enumerate(sources[max_visible:], max_visible + 1):
                    self._render_source_card(source, i)
    
    def _render_source_card(self, source: dict, index: int):
        """Render a single source as a clean card."""
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"**Source {index}**")
            
            with col2:
                if source.get('page'):
                    st.caption(f"Page {source['page']}")
            
            # Show content
            content = source.get('content', source.get('text', ''))
            st.markdown(f"> {content[:300]}...")
            
            # Metadata in expander
            if source.get('metadata'):
                with st.expander("Details", expanded=False):
                    self._render_metadata(source['metadata'])
            
            st.divider()
    
    def _render_metadata(self, metadata: dict):
        """Render metadata in a clean format."""
        cols = st.columns(3)
        
        with cols[0]:
            if metadata.get('type'):
                st.caption(f"**Type:** {metadata['type']}")
        
        with cols[1]:
            if metadata.get('chunking_method'):
                st.caption(f"**Method:** {metadata['chunking_method']}")
        
        with cols[2]:
            if metadata.get('chunk_idx'):
                st.caption(f"**Chunk:** {metadata['chunk_idx']}")
    
    def _render_evaluation_metrics(self, evaluation: dict):
        """Render evaluation metrics in a clean grid."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_sim = evaluation.get('avg_semantic_similarity', 0)
            st.metric(
                "Relevance",
                f"{avg_sim:.2%}",
                help="Average semantic similarity"
            )
        
        with col2:
            term_cov = evaluation.get('avg_term_coverage', 0)
            st.metric(
                "Coverage",
                f"{term_cov:.2%}",
                help="Query term coverage"
            )
        
        with col3:
            diversity = evaluation.get('diversity_score', 0)
            st.metric(
                "Diversity",
                f"{diversity:.2f}",
                help="Source diversity"
            )
    
    def render_error(self, message: str):
        """Display error message with professional styling."""
        st.error(f"❌ {message}")
    
    def render_info(self, message: str):
        """Display info message with professional styling."""
        st.info(f"ℹ️ {message}")
    
    def render_success(self, message: str):
        """Display success message with professional styling."""
        st.success(f"✅ {message}")
