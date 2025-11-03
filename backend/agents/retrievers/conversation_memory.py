"""
Conversation Memory Manager

Handles conversation history and context building for follow-up questions.
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Manages conversation history and context for follow-up questions.
    
    Maintains a history of questions and answers, and builds context
    for the LLM to understand follow-up queries.
    """
    
    def __init__(self, max_history: int = 5):
        """
        Initialize conversation memory.
        
        Args:
            max_history: Maximum number of turns to keep in history
            
        Example:
            >>> memory = ConversationMemory(max_history=5)
            >>> memory.add_turn("What is maternity coverage?", "Maternity...")
        """
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = max_history
        logger.info(f"ConversationMemory initialized with max_history={max_history}")
    
    def add_turn(self, question: str, answer: str):
        """
        Add a conversation turn to history.
        
        Args:
            question: User's question
            answer: Agent's answer
            
        Example:
            >>> memory.add_turn(
            ...     question="What is the waiting period?",
            ...     answer="The waiting period is 30 days..."
            ... )
        """
        self.conversation_history.append({
            "role": "user",
            "content": question
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": answer
        })
        
        # Trim history if it exceeds max_history
        max_messages = self.max_history * 2  # Each turn is 2 messages
        if len(self.conversation_history) > max_messages:
            self.conversation_history = self.conversation_history[-max_messages:]
        
        logger.info(f"Added turn to history. Total turns: {len(self.conversation_history) // 2}")
    
    def get_history(self) -> List[Dict[str, str]]:
        """
        Get full conversation history.
        
        Returns:
            List of message dicts with role and content
            
        Example:
            >>> history = memory.get_history()
            >>> len(history)
            4  # 2 turns = 4 messages
        """
        return self.conversation_history.copy()
    
    def build_context(self, max_turns: int = 3) -> str:
        """
        Build conversation context string for LLM.
        
        Args:
            max_turns: Maximum number of recent turns to include
            
        Returns:
            Formatted conversation context string
            
        Example:
            >>> context = memory.build_context(max_turns=2)
            >>> "Previous conversation:" in context
            True
        """
        if not self.conversation_history:
            return ""
        
        # Get last N turns (each turn = 2 messages)
        recent_messages = self.conversation_history[-(max_turns * 2):]
        
        context = "\n\nPrevious conversation:\n"
        for msg in recent_messages:
            if msg["role"] == "user":
                context += f"User: {msg['content']}\n"
            else:
                context += f"Assistant: {msg['content']}\n"
        
        return context
    
    def build_context_if_relevant(
        self, 
        current_query: str, 
        max_turns: int = 2
    ) -> str:
        """
        Build context only if current query seems to be a follow-up.
        
        Args:
            current_query: Current user query
            max_turns: Maximum turns to include
            
        Returns:
            Context string if relevant, empty string otherwise
            
        Example:
            >>> context = memory.build_context_if_relevant(
            ...     "What about the premium?"  # Follow-up indicator
            ... )
            >>> len(context) > 0
            True
        """
        if not self.conversation_history:
            return ""
        
        # Check if query contains follow-up indicators
        query_lower = current_query.lower()
        follow_up_indicators = [
            'what about', 'how about', 'and', 'also', 'additionally',
            'furthermore', 'moreover', 'besides', 'in addition',
            'it', 'that', 'this', 'these', 'those', 'they',
            'same', 'above', 'previous', 'earlier', 'mentioned'
        ]
        
        # Check for pronouns and references that suggest follow-up
        is_followup = any(indicator in query_lower for indicator in follow_up_indicators)
        
        # Also check if query is very short (likely a follow-up)
        word_count = len(current_query.split())
        is_short = word_count < 5
        
        if is_followup or is_short:
            return self.build_context(max_turns=max_turns)
        
        return ""
    
    def clear(self):
        """
        Clear all conversation history.
        
        Example:
            >>> memory.clear()
            >>> len(memory.get_history())
            0
        """
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_turn_count(self) -> int:
        """
        Get number of conversation turns.
        
        Returns:
            Number of complete turns (question-answer pairs)
            
        Example:
            >>> memory.get_turn_count()
            2
        """
        return len(self.conversation_history) // 2
    
    def get_last_question(self) -> Optional[str]:
        """
        Get the last question asked.
        
        Returns:
            Last question or None if no history
            
        Example:
            >>> memory.get_last_question()
            'What is the waiting period?'
        """
        for msg in reversed(self.conversation_history):
            if msg["role"] == "user":
                return msg["content"]
        return None
    
    def get_last_answer(self) -> Optional[str]:
        """
        Get the last answer given.
        
        Returns:
            Last answer or None if no history
            
        Example:
            >>> memory.get_last_answer()
            'The waiting period is 30 days...'
        """
        for msg in reversed(self.conversation_history):
            if msg["role"] == "assistant":
                return msg["content"]
        return None
