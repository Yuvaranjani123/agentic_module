"""
Reasoning Display Component

Visualizes ReAct reasoning traces with Thought-Action-Observation steps.
"""
import streamlit as st
import json


class ReasoningDisplay:
    """Display component for ReAct reasoning traces."""
    
    def render_reasoning_trace(self, trace: dict):
        """
        Render ReAct reasoning trace with expandable steps.
        
        Args:
            trace: Reasoning trace dictionary with steps
        """
        st.markdown("### 🧠 Reasoning Trace")
        
        steps = trace.get('steps', [])
        if not steps:
            st.info("No reasoning steps recorded")
            return
        
        for i, step in enumerate(steps, 1):
            with st.expander(f"**Step {i}** - {step.get('step_type', 'unknown').title()}", expanded=True):
                step_type = step.get('step_type', '')
                
                if step_type == 'thought':
                    self._render_thought_step(step)
                elif step_type == 'action':
                    self._render_action_step(step)
                elif step_type == 'observation':
                    self._render_observation_step(step)
                elif step_type == 'final_answer':
                    self._render_final_answer_step(step)
    
    def _render_thought_step(self, step: dict):
        """Render thought step with blue styling."""
        st.markdown(f"""
        <div class="thought-box">
            <strong>💭 Thought:</strong><br/>
            {step.get('content', 'N/A')}
        </div>
        """, unsafe_allow_html=True)
    
    def _render_action_step(self, step: dict):
        """Render action step with orange styling."""
        st.markdown(f"""
        <div class="action-box">
            <strong>⚡ Action:</strong> {step.get('tool_name', 'N/A')}<br/>
            <strong>Input:</strong> <code>{json.dumps(step.get('tool_input', {}), indent=2)}</code>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_observation_step(self, step: dict):
        """Render observation step with green styling."""
        st.markdown(f"""
        <div class="observation-box">
            <strong>👁️ Observation:</strong><br/>
            {step.get('content', 'N/A')}
        </div>
        """, unsafe_allow_html=True)
    
    def _render_final_answer_step(self, step: dict):
        """Render final answer step."""
        st.success(f"**✓ Final Answer:** {step.get('content', 'N/A')}")
    
    def render_intent_classification(self, intent_data: dict):
        """
        Render intent classification section.
        
        Args:
            intent_data: Intent classification dictionary
        """
        st.markdown("### 🎯 Intent Classification")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Intent", intent_data.get('intent', 'N/A'))
        with col2:
            confidence = intent_data.get('confidence', 0)
            st.metric("Confidence", f"{confidence:.2%}")
        with col3:
            st.metric("Learning", "✅ Enabled" if intent_data.get('learning_active') else "❌ Disabled")
        
        if intent_data.get('reasoning'):
            with st.expander("💡 Classification Reasoning"):
                st.write(intent_data['reasoning'])
    
    def render_final_answer(self, answer: str):
        """
        Render final answer section.
        
        Args:
            answer: Final answer text
        """
        st.markdown("### ✅ Final Answer")
        st.success(answer if answer else 'No answer provided')
    
    def render_metadata(self, metadata: dict):
        """
        Render execution metadata.
        
        Args:
            metadata: Metadata dictionary with execution details
        """
        with st.expander("📋 Execution Metadata"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Steps", metadata.get('total_steps', 0))
            with col2:
                st.metric("Tools Used", metadata.get('tools_used_count', 0))
            with col3:
                st.metric("Success", "✅" if metadata.get('reasoning_success') else "❌")
            
            if metadata.get('tools_used'):
                st.write("**Tools Used:**", ", ".join(metadata['tools_used']))
    
    def render_complete_response(self, response: dict):
        """
        Render complete agentic response with final answer first, reasoning trace separate.
        
        Args:
            response: Complete response dictionary from API
        """
        # ===== PRIMARY SECTION: Final Answer (Always Visible) =====
        st.markdown("### ✅ Final Answer")
        
        final_answer = response.get('final_answer', 'No answer provided')
        st.success(final_answer)
        
        # Quick metadata summary
        metadata = response.get('agentic_metadata', {})
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔄 Iterations", metadata.get('reasoning_iterations', 0))
        with col2:
            tools_count = len(metadata.get('tools_used', []))
            st.metric("🔧 Tools Used", tools_count)
        with col3:
            st.metric("⏱️ Mode", "ReAct")
        with col4:
            success_icon = "✅" if metadata.get('react_enabled') else "❌"
            st.metric("Status", success_icon)
        
        st.divider()
        
        # ===== SECONDARY SECTION: Detailed Reasoning (Collapsible Tabs) =====
        st.markdown("### 🔍 Detailed Analysis")
        
        # Create tabs for different sections
        tab1, tab2, tab3 = st.tabs(["📊 Intent & Metadata", "🧠 Reasoning Trace", "⚙️ Technical Details"])
        
        with tab1:
            # Intent classification
            if response.get('intent_classification'):
                st.markdown("#### 🎯 Intent Classification")
                intent_data = response['intent_classification']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Detected Intent", intent_data.get('intent', 'N/A'))
                with col2:
                    confidence = intent_data.get('confidence', 0)
                    st.metric("Confidence", f"{confidence:.2%}")
                with col3:
                    learning_status = "✅ Active" if intent_data.get('learning_active') else "❌ Inactive"
                    st.metric("Learning", learning_status)
                
                if intent_data.get('reasoning'):
                    with st.expander("💡 Why this intent?"):
                        st.write(intent_data['reasoning'])
            
            # Execution summary
            st.markdown("#### 📈 Execution Summary")
            if metadata:
                summary_col1, summary_col2 = st.columns(2)
                with summary_col1:
                    st.write(f"**Total Reasoning Steps:** {metadata.get('total_steps', 'N/A')}")
                    st.write(f"**Dynamic Routing:** {'Yes' if metadata.get('dynamic_routing') else 'No'}")
                    st.write(f"**Learning Applied:** {'Yes' if metadata.get('learning_applied') else 'No'}")
                with summary_col2:
                    if metadata.get('tools_used'):
                        st.write("**Tools Executed:**")
                        for tool in metadata['tools_used']:
                            st.write(f"  • {tool}")
        
        with tab2:
            # Detailed reasoning trace
            st.markdown("#### 🧠 Step-by-Step Reasoning Process")
            st.caption("See how the ReAct agent thought through your query")
            
            if response.get('reasoning_trace'):
                trace = response['reasoning_trace']
                steps = trace.get('steps', [])
                
                if not steps:
                    st.info("No reasoning steps recorded")
                else:
                    # Group steps by iteration
                    current_iteration = 0
                    iteration_steps = []
                    
                    for step in steps:
                        step_iteration = step.get('iteration', current_iteration)
                        if step_iteration != current_iteration:
                            # Render previous iteration
                            if iteration_steps:
                                self._render_iteration_group(current_iteration, iteration_steps)
                            # Start new iteration
                            current_iteration = step_iteration
                            iteration_steps = [step]
                        else:
                            iteration_steps.append(step)
                    
                    # Render last iteration
                    if iteration_steps:
                        self._render_iteration_group(current_iteration, iteration_steps)
            else:
                st.info("No reasoning trace available")
        
        with tab3:
            # Technical details
            st.markdown("#### ⚙️ Technical Execution Details")
            
            with st.expander("📋 Complete Metadata", expanded=False):
                st.json(metadata)
            
            with st.expander("🔍 Raw Response Data", expanded=False):
                st.json(response)
    
    def _render_iteration_group(self, iteration: int, steps: list):
        """
        Render a group of steps from a single iteration.
        
        Args:
            iteration: Iteration number
            steps: List of steps in this iteration
        """
        with st.expander(f"**Iteration {iteration + 1}**", expanded=(iteration < 2)):  # Auto-expand first 2 iterations
            for step in steps:
                step_type = step.get('step_type', '')
                
                if step_type == 'thought':
                    self._render_thought_step(step)
                elif step_type == 'action':
                    self._render_action_step(step)
                elif step_type == 'observation':
                    self._render_observation_step(step)
                elif step_type == 'final_answer':
                    self._render_final_answer_step(step)
                
                # Add some spacing between steps
                st.markdown("<br/>", unsafe_allow_html=True)
