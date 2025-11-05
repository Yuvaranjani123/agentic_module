"""
Agentic Settings Panel Component

Settings panel for agentic system configuration including product selection,
policy comparison, and system statistics.
"""
import streamlit as st
import os
import requests


class AgenticSettings:
    """Settings panel for agentic system."""
    
    def __init__(self, api_base: str):
        """
        Initialize settings panel.
        
        Args:
            api_base: Base URL for API calls
        """
        self.api_base = api_base
    
    def render_sidebar(self):
        """
        Render complete settings sidebar.
        
        Returns:
            Dict with configuration settings
        """
        with st.sidebar:
            st.header("⚙️ Settings")
            
            # Product and policy selection
            config = self._render_product_policy_selection()
            
            st.divider()
            
            # System statistics
            self._render_statistics()
            
            st.divider()
            
            # Example queries
            self._render_example_queries()
        
        return config
    
    def _render_product_policy_selection(self):
        """Render policy selection for comparison (no product database selector)."""
        # Detect available products
        available_products, chroma_base = self._detect_available_products()
        
        if not available_products:
            st.warning("⚠️ No product databases found")
            st.info("💡 Run ingestion first to create product databases")
            return {
                'chroma_db_dir': None,
                'selected_product': None,
                'policy_selections': st.session_state.get('policy_selections', {
                    'policy1': 'ActivAssure',
                    'policy2': 'ActivFit'
                })
            }
        
        # Show auto-detection info
        st.info("🎯 **Smart Product Detection Enabled!**\n\nJust mention product name in your query (e.g., 'ActivFit') and the agent will auto-detect it.")
        
        st.divider()
        
        # Policy selections for comparison
        st.subheader("🔀 Policy Comparison Settings")
        st.caption("Default policies for comparison queries")
        
        if 'policy_selections' not in st.session_state:
            st.session_state.policy_selections = {
                'policy1': available_products[0] if len(available_products) > 0 else 'ActivAssure',
                'policy2': available_products[1] if len(available_products) > 1 else available_products[0]
            }
        
        policy1 = st.selectbox(
            "Primary Policy",
            available_products,
            index=available_products.index(st.session_state.policy_selections['policy1']) if st.session_state.policy_selections['policy1'] in available_products else 0,
            key="policy1_select",
            help="Default primary policy for comparisons"
        )
        
        policy2 = st.selectbox(
            "Compare With",
            available_products,
            index=available_products.index(st.session_state.policy_selections['policy2']) if st.session_state.policy_selections['policy2'] in available_products else (1 if len(available_products) > 1 else 0),
            key="policy2_select",
            help="Default secondary policy for comparisons"
        )
        
        st.session_state.policy_selections = {
            'policy1': policy1,
            'policy2': policy2
        }
        
        # Use first available product as default (but auto-detection will override)
        default_product = available_products[0]
        default_chroma_dir = os.path.join(chroma_base, default_product)
        
        return {
            'chroma_db_dir': default_chroma_dir,
            'selected_product': default_product,
            'policy_selections': st.session_state.policy_selections
        }
    
    def _render_statistics(self):
        """Render system statistics section."""
        st.header("📊 Statistics")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Stats", use_container_width=True):
                stats = self._get_system_stats()
                if stats and stats.get('success'):
                    st.session_state.stats = stats
        
        with col2:
            if st.button("🗑️ Reset Stats", use_container_width=True):
                if self._reset_system_stats():
                    st.success("✅ Statistics reset!")
                    # Clear cached stats
                    if 'stats' in st.session_state:
                        del st.session_state.stats
                    st.rerun()
        
        if 'stats' in st.session_state and st.session_state.stats:
            stats_data = st.session_state.stats.get('statistics', {})
            
            # Use tabs for better organization
            tab1, tab2, tab3 = st.tabs(["🤖 ReAct", "🧠 Learning", "🛠️ Tools"])
            
            with tab1:
                # ReAct metrics
                st.markdown("**ReAct System**")
                react_stats = stats_data.get('react', {})
                st.metric("Total Queries", react_stats.get('total_queries', 0))
                st.metric("Avg Steps", f"{react_stats.get('avg_steps', 0):.1f}")
                st.metric("Success Rate", f"{react_stats.get('success_rate', 0):.1%}")
            
            with tab2:
                # Learning metrics
                st.markdown("**Intent Learning**")
                learning = st.session_state.stats.get('learning_evidence', {})
                st.metric("Total Classifications", learning.get('total_interactions', 0))
                st.metric("Patterns Learned", len(learning.get('patterns_learned', {})))
                improvement = learning.get('accuracy_improvement', 0)
                st.metric("Accuracy Improvement", f"{improvement:+.1%}")
            
            with tab3:
                # Tool usage
                st.markdown("**Tool Usage**")
                tools = st.session_state.stats.get('tool_usage', {})
                if tools:
                    for tool_name, tool_data in tools.items():
                        # Handle both dict and int formats
                        if isinstance(tool_data, dict):
                            count = tool_data.get('usage_count', 0)
                        else:
                            count = tool_data
                        
                        # Format tool name nicely
                        display_name = tool_name.replace('_', ' ').title()
                        st.metric(display_name, count)
                else:
                    st.info("No tool usage data yet")
        else:
            st.info("Click 'Refresh Stats' to load system statistics")
    
    def _render_example_queries(self):
        """Render example queries section."""
        st.markdown("**💡 Example Queries**")
        st.caption("💡 Tip: Mention product name for auto-detection!")
        examples = [
            "Calculate premium for ActivAssure age 32",
            "What is maternity coverage in ActivFit?",
            "Compare ActivAssure with ActivFit",
            "Calculate premium age 32, then compare with ActivFit"
        ]
        
        for idx, example in enumerate(examples):
            if st.button(example, key=f"example_{idx}", use_container_width=True):
                st.session_state.example_query = example
    
    def _detect_available_products(self):
        """
        Detect available product databases from chroma_db directory.
        
        Returns:
            Tuple of (products_list, base_directory)
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up from components/agentic to frontend, then to project root
        frontend_dir = os.path.dirname(os.path.dirname(current_dir))
        project_root = os.path.dirname(frontend_dir)
        chroma_base = os.path.join(project_root, "media", "output", "chroma_db")
        
        products = []
        if os.path.exists(chroma_base):
            for item in os.listdir(chroma_base):
                item_path = os.path.join(chroma_base, item)
                if os.path.isdir(item_path):
                    db_file = os.path.join(item_path, "chroma.sqlite3")
                    if os.path.exists(db_file):
                        products.append(item)
        
        return products, chroma_base
    
    def _get_system_stats(self):
        """Get system statistics from API."""
        try:
            response = requests.get(f"{self.api_base}/agents/agentic/stats/", timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error fetching stats: {str(e)}")
            return None
    
    def _reset_system_stats(self):
        """Reset system statistics via API."""
        try:
            response = requests.post(f"{self.api_base}/agents/agentic/reset-stats/", timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get('success', False)
        except Exception as e:
            st.error(f"Error resetting stats: {str(e)}")
            return False
