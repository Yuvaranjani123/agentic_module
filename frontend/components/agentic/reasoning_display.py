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
        Render complete agentic response.
        
        Args:
            response: Complete response dictionary from API
        """
        st.divider()
        
        # Intent classification
        if response.get('intent_classification'):
            self.render_intent_classification(response['intent_classification'])
        
        # Reasoning trace
        st.divider()
        if response.get('reasoning_trace'):
            self.render_reasoning_trace(response['reasoning_trace'])
        
        # Final answer
        st.divider()
        self.render_final_answer(response.get('final_answer'))
        
        # Metadata
        if response.get('agentic_metadata'):
            self.render_metadata(response['agentic_metadata'])
