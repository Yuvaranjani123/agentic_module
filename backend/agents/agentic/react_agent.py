"""
ReAct Agent - Reasoning + Acting with iterative thought-action-observation loop
Implements the ReAct (Reason + Act) paradigm for dynamic multi-step task execution.

ReAct Flow:
1. Thought: Reason about what to do next
2. Action: Execute a tool/agent
3. Observation: Observe the result
4. Repeat until task complete
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

# Import ReAct prompts from config
from config.prompts import (
    REACT_SYSTEM_PROMPT,
    REACT_USER_PROMPT_TEMPLATE,
    format_react_user_prompt
)

logger = logging.getLogger(__name__)


class ReActStepType(Enum):
    """Types of ReAct steps"""
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    FINAL_ANSWER = "final_answer"


@dataclass
class ReActStep:
    """
    Single step in ReAct reasoning chain.
    Each step has: Thought → Action → Observation
    """
    step_number: int
    step_type: ReActStepType
    content: str
    tool_used: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Any] = None
    timestamp: float = field(default_factory=lambda: __import__('time').time())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'step_number': self.step_number,
            'step_type': self.step_type.value,
            'content': self.content,
            'tool_used': self.tool_used,
            'tool_input': self.tool_input,
            'tool_output': str(self.tool_output)[:200] if self.tool_output else None,
            'timestamp': self.timestamp
        }


@dataclass
class ReActTrace:
    """
    Complete ReAct reasoning trace for a query.
    Contains all thoughts, actions, and observations.
    """
    query: str
    steps: List[ReActStep] = field(default_factory=list)
    final_answer: Optional[str] = None
    success: bool = False
    max_iterations: int = 10
    current_iteration: int = 0
    
    def add_step(self, step: ReActStep):
        """Add a step to the trace."""
        self.steps.append(step)
        self.current_iteration = len([s for s in self.steps if s.step_type == ReActStepType.THOUGHT])
    
    def get_context_summary(self) -> str:
        """Get summary of reasoning so far for context."""
        summary = f"Query: {self.query}\n\n"
        summary += f"Reasoning trace ({len(self.steps)} steps):\n"
        
        for step in self.steps:
            if step.step_type == ReActStepType.THOUGHT:
                summary += f"\nThought {step.step_number}: {step.content}\n"
            elif step.step_type == ReActStepType.ACTION:
                summary += f"Action: {step.tool_used}({step.tool_input})\n"
            elif step.step_type == ReActStepType.OBSERVATION:
                obs = str(step.tool_output)[:100] if step.tool_output else "None"
                summary += f"Observation: {obs}\n"
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'query': self.query,
            'steps': [s.to_dict() for s in self.steps],
            'final_answer': self.final_answer,
            'success': self.success,
            'iterations': self.current_iteration,
            'max_iterations': self.max_iterations
        }


class ReActAgent:
    """
    ReAct Agent implementing Reasoning + Acting paradigm.
    
    Features:
    - Iterative thought-action-observation loop
    - Dynamic tool selection based on reasoning
    - Multi-step task decomposition
    - Reflection and self-correction
    - Handles complex queries like "calculate then compare"
    
    Tools available:
    - premium_calculator: Calculate insurance premiums
    - policy_comparator: Compare insurance policies
    - document_retriever: Retrieve policy information
    - finish: Complete task with final answer
    
    Note: System and user prompts are now centralized in config/prompts/react_prompts.py
    """
    
    def __init__(self, llm: AzureChatOpenAI, tools: Dict[str, Any]):
        """
        Initialize ReAct agent.
        
        Args:
            llm: Language model for reasoning
            tools: Dictionary of available tools (agents)
        """
        self.llm = llm
        self.tools = tools
        self.reasoning_history: List[ReActTrace] = []
        
        logger.info(f"ReAct Agent initialized with {len(tools)} tools: {list(tools.keys())}")
    
    def run(self, query: str, context: Dict[str, Any], max_iterations: int = 10) -> Dict[str, Any]:
        """
        Run ReAct loop for a query.
        
        Args:
            query: User query
            context: Conversation context
            max_iterations: Maximum reasoning iterations
            
        Returns:
            Result with reasoning trace and final answer
        """
        logger.info(f"=== ReAct Agent Processing: {query[:100]} ===")
        
        trace = ReActTrace(query=query, max_iterations=max_iterations)
        
        try:
            # Run iterative ReAct loop
            while trace.current_iteration < max_iterations:
                # Generate next reasoning step
                thought, action, action_input = self._generate_step(trace, context)
                
                # Add thought step
                trace.add_step(ReActStep(
                    step_number=trace.current_iteration,
                    step_type=ReActStepType.THOUGHT,
                    content=thought
                ))
                
                logger.info(f"Thought {trace.current_iteration}: {thought[:100]}...")
                
                # Check if finished
                if action == "finish":
                    trace.final_answer = action_input.get('answer', '')
                    trace.success = True
                    trace.add_step(ReActStep(
                        step_number=trace.current_iteration,
                        step_type=ReActStepType.FINAL_ANSWER,
                        content=trace.final_answer,
                        tool_used='finish'
                    ))
                    logger.info("ReAct: Task completed")
                    break
                
                # Execute action
                observation = self._execute_action(action, action_input, context)
                
                # Add action and observation steps
                trace.add_step(ReActStep(
                    step_number=trace.current_iteration,
                    step_type=ReActStepType.ACTION,
                    content=f"{action}({action_input})",
                    tool_used=action,
                    tool_input=action_input
                ))
                
                trace.add_step(ReActStep(
                    step_number=trace.current_iteration,
                    step_type=ReActStepType.OBSERVATION,
                    content=str(observation)[:500],
                    tool_output=observation
                ))
                
                logger.info(f"Action: {action}, Observation: {str(observation)[:100]}...")
            
            # Check if max iterations reached
            if trace.current_iteration >= max_iterations and not trace.success:
                trace.final_answer = "Maximum reasoning iterations reached. Could not complete task."
                trace.success = False
                logger.warning("ReAct: Max iterations reached")
            
        except Exception as e:
            logger.error(f"ReAct error: {e}", exc_info=True)
            trace.final_answer = f"Error during reasoning: {str(e)}"
            trace.success = False
        
        # Store trace
        self.reasoning_history.append(trace)
        
        # Return result
        return {
            'query': query,
            'reasoning_trace': trace.to_dict(),
            'final_answer': trace.final_answer,
            'success': trace.success,
            'iterations': trace.current_iteration,
            'tools_used': list(set(s.tool_used for s in trace.steps if s.tool_used and s.tool_used != 'finish'))
        }
    
    def _generate_step(self, trace: ReActTrace, context: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        """
        Generate next Thought-Action-Action Input step.
        
        Returns:
            (thought, action, action_input)
        """
        # Build context from previous steps
        context_summary = trace.get_context_summary() if trace.steps else ""
        
        # Create prompt using centralized config
        prompt = format_react_user_prompt(
            query=trace.query,
            context_str=context_summary
        )
        
        # Get LLM response
        messages = [
            SystemMessage(content=REACT_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        response_text = response.content.strip()
        
        logger.debug(f"LLM Response:\n{response_text}")
        
        # Parse response
        thought, action, action_input = self._parse_react_response(response_text)
        
        return thought, action, action_input
    
    def _parse_react_response(self, response: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Parse ReAct format response.
        
        Expected format:
        Thought: [reasoning]
        Action: [tool_name]
        Action Input: {"key": "value"}
        
        Returns:
            (thought, action, action_input)
        """
        thought = ""
        action = ""
        action_input = {}
        
        lines = response.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if line.startswith('Thought:'):
                thought = line.replace('Thought:', '').strip()
            elif line.startswith('Action:'):
                action = line.replace('Action:', '').strip()
            elif line.startswith('Action Input:'):
                # Parse JSON input
                json_str = line.replace('Action Input:', '').strip()
                try:
                    action_input = json.loads(json_str)
                except json.JSONDecodeError:
                    # Try to find JSON in next lines
                    json_str = '\n'.join(lines[i:]).replace('Action Input:', '').strip()
                    try:
                        # Find first { and last }
                        start = json_str.find('{')
                        end = json_str.rfind('}') + 1
                        if start >= 0 and end > start:
                            action_input = json.loads(json_str[start:end])
                    except:
                        logger.warning(f"Could not parse action input: {json_str}")
                        action_input = {"query": json_str}
        
        # Validate
        if not thought:
            thought = "Continue with next step"
        if not action:
            action = "finish"
            action_input = {"answer": "No clear action determined"}
        
        return thought, action, action_input
    
    def _execute_action(self, action: str, action_input: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """
        Execute an action using the appropriate tool.
        
        Args:
            action: Tool name
            action_input: Input parameters for tool
            context: Execution context
            
        Returns:
            Tool output (observation)
        """
        if action not in self.tools:
            logger.warning(f"Unknown action: {action}, available: {list(self.tools.keys())}")
            return f"Error: Unknown action '{action}'. Available tools: {list(self.tools.keys())}"
        
        tool = self.tools[action]
        
        try:
            # Convert action_input dict to JSON string for tools that expect it
            import json
            action_input_str = json.dumps(action_input)
            
            # Execute tool with JSON string
            result = tool.execute(action_input_str, context)
            
            # Extract relevant observation
            if isinstance(result, dict):
                if result.get('success'):
                    return result.get('data', result.get('response', result))
                else:
                    return f"Error: {result.get('error', 'Tool execution failed')}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing {action}: {e}")
            return f"Error executing {action}: {str(e)}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ReAct agent statistics."""
        if not self.reasoning_history:
            return {
                'total_queries': 0,
                'avg_iterations': 0,
                'success_rate': 0,
                'tools_usage': {}
            }
        
        total = len(self.reasoning_history)
        successful = sum(1 for t in self.reasoning_history if t.success)
        avg_iterations = sum(t.current_iteration for t in self.reasoning_history) / total
        
        # Count tool usage
        tools_usage = {}
        for trace in self.reasoning_history:
            for step in trace.steps:
                if step.tool_used and step.tool_used != 'finish':
                    tools_usage[step.tool_used] = tools_usage.get(step.tool_used, 0) + 1
        
        return {
            'total_queries': total,
            'successful_queries': successful,
            'success_rate': successful / total if total > 0 else 0,
            'avg_iterations': avg_iterations,
            'avg_steps_per_query': sum(len(t.steps) for t in self.reasoning_history) / total,
            'tools_usage': tools_usage,
            'max_iterations_reached': sum(1 for t in self.reasoning_history if t.current_iteration >= t.max_iterations)
        }
