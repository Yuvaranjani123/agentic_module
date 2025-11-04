"""
Learning Intent Classifier - Adaptive intent classification without manual training
Implements: LLM-based learning, User feedback, Historical analysis
"""

import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict
import time
import json

from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Import intent classification prompts from config
from config.prompts import (
    format_intent_classification_prompt,
    INTENT_VALID_INTENTS,
    get_pattern_examples_for_intent
)

logger = logging.getLogger(__name__)


class LearningIntentClassifier:
    """
    Intent classifier that learns from interactions without manual training.
    
    Key Features:
    - LLM-based classification (leverages GPT understanding)
    - Learns from user feedback and corrections
    - Analyzes historical patterns
    - Confidence-based routing
    - Improves over time through interaction history
    
    NO manual ML model training required!
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        """
        Initialize learning classifier.
        
        Args:
            llm: Azure OpenAI LLM instance
        """
        self.llm = llm
        self.interaction_history = []
        self.feedback_history = []
        self.intent_patterns = defaultdict(list)  # Learned patterns per intent
        
        logger.info("Learning Intent Classifier initialized")
    
    def classify(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify query intent using LLM + learned patterns.
        
        Args:
            query: User query
            context: Conversation context, previous interactions
            
        Returns:
            {
                'intent': str,
                'confidence': float,
                'reasoning': str,
                'alternative_intents': List[Dict]
            }
        """
        logger.info(f"Classifying: {query[:100]}...")
        
        # Build classification prompt with learned patterns
        prompt = self._build_classification_prompt(query, context)
        
        # Get LLM classification
        try:
            response = self.llm.invoke(prompt)
            classification = self._parse_classification(response.content)
            
            # Enhance with learned patterns
            classification = self._apply_learned_patterns(query, classification)
            
            # Log interaction for learning
            self._log_interaction(query, classification, context)
            
            return classification
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return self._fallback_classification(query)
    
    def learn_from_feedback(self, query: str, predicted_intent: str, 
                           actual_intent: str, context: Dict[str, Any]):
        """
        Learn from user feedback/corrections.
        Critical for adaptive learning without manual training.
        
        Args:
            query: Original query
            predicted_intent: What system predicted
            actual_intent: Correct intent (from user or execution result)
            context: Context when classification happened
        """
        logger.info(f"Learning: {predicted_intent} → {actual_intent} for: {query[:50]}")
        
        feedback = {
            'timestamp': time.time(),
            'query': query,
            'predicted': predicted_intent,
            'actual': actual_intent,
            'context': context,
            'was_correct': predicted_intent == actual_intent
        }
        
        self.feedback_history.append(feedback)
        
        # Update learned patterns
        if not feedback['was_correct']:
            # Extract pattern from incorrectly classified query
            pattern = self._extract_pattern(query, actual_intent)
            self.intent_patterns[actual_intent].append(pattern)
            
            logger.info(f"Learned new pattern for {actual_intent}: {pattern}")
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning and improvement statistics."""
        if not self.interaction_history:
            return {'classifications': 0, 'learning_active': True}
        
        total = len(self.interaction_history)
        
        # Calculate accuracy improvement over time
        if len(self.feedback_history) >= 10:
            early_feedback = self.feedback_history[:10]
            recent_feedback = self.feedback_history[-10:]
            
            early_accuracy = sum(1 for f in early_feedback if f['was_correct']) / len(early_feedback)
            recent_accuracy = sum(1 for f in recent_feedback if f['was_correct']) / len(recent_feedback)
            
            improvement = recent_accuracy - early_accuracy
        else:
            early_accuracy = recent_accuracy = improvement = 0.0
        
        # Patterns learned per intent
        patterns_learned = {
            intent: len(patterns) 
            for intent, patterns in self.intent_patterns.items()
        }
        
        return {
            'total_classifications': total,
            'feedback_received': len(self.feedback_history),
            'early_accuracy': early_accuracy,
            'recent_accuracy': recent_accuracy,
            'improvement': improvement,
            'patterns_learned': patterns_learned,
            'learning_active': True
        }
    
    def _build_classification_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Build classification prompt using centralized config."""
        
        # Get conversation history
        conv_history = context.get('conversation_history', [])
        recent_conv = json.dumps(conv_history[-3:], indent=2) if len(conv_history) > 3 else (
            json.dumps(conv_history, indent=2) if conv_history else "No previous conversation"
        )
        
        # Get relevant learned patterns
        pattern_hints = self._get_pattern_hints()
        
        # Use centralized prompt formatter
        return format_intent_classification_prompt(
            query=query,
            conversation_context=recent_conv,
            learned_patterns=pattern_hints
        )
    
    def _parse_classification(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into classification dict."""
        try:
            # Try to extract JSON from response
            if '{' in response:
                json_start = response.index('{')
                json_end = response.rindex('}') + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON in response")
                
        except Exception as e:
            logger.error(f"Parse error: {e}, Response: {response}")
            return self._fallback_classification("")
    
    def _apply_learned_patterns(self, query: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance classification with learned patterns."""
        
        query_lower = query.lower()
        
        # Check if query matches any learned patterns
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern['keywords']:
                    # Check keyword match
                    matches = sum(1 for kw in pattern['keywords'] if kw in query_lower)
                    
                    if matches >= len(pattern['keywords']) * 0.6:  # 60% keyword match
                        # Boost confidence for this intent
                        if classification['intent'] == intent:
                            classification['confidence'] = min(
                                classification['confidence'] + 0.15,
                                1.0
                            )
                            classification['reasoning'] += " (Reinforced by learned patterns)"
                            
                            logger.debug(f"Pattern match boosted {intent} confidence")
                            break
        
        return classification
    
    def _extract_pattern(self, query: str, intent: str) -> Dict[str, Any]:
        """Extract pattern from query for future learning."""
        
        # Extract key terms (simple approach)
        words = query.lower().split()
        
        # Filter meaningful words (remove common words)
        stop_words = {'the', 'a', 'an', 'is', 'are', 'what', 'how', 'can', 'does', 'do'}
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        
        return {
            'keywords': keywords[:5],  # Top 5 keywords
            'query_length': len(words),
            'has_question': '?' in query,
            'timestamp': time.time()
        }
    
    def _get_pattern_hints(self) -> str:
        """Get formatted pattern hints for prompt."""
        if not self.intent_patterns:
            return "No patterns learned yet."
        
        hints = []
        for intent, patterns in list(self.intent_patterns.items())[:3]:  # Top 3 intents
            recent_patterns = patterns[-3:] if len(patterns) > 3 else patterns
            
            keywords = set()
            for pattern in recent_patterns:
                keywords.update(pattern['keywords'])
            
            if keywords:
                hints.append(f"- {intent}: Often contains words like {', '.join(list(keywords)[:5])}")
        
        return '\n'.join(hints) if hints else "No patterns learned yet."
    
    def _fallback_classification(self, query: str) -> Dict[str, Any]:
        """Fallback classification when LLM fails."""
        
        query_lower = query.lower()
        
        # Simple heuristics
        if any(kw in query_lower for kw in ['calculate', 'premium', 'cost', 'price']):
            intent = 'PREMIUM_CALCULATION'
            confidence = 0.6
        elif any(kw in query_lower for kw in ['compare', 'difference', 'better']):
            intent = 'POLICY_COMPARISON'
            confidence = 0.6
        else:
            intent = 'DOCUMENT_RETRIEVAL'
            confidence = 0.5
        
        return {
            'intent': intent,
            'confidence': confidence,
            'reasoning': 'Fallback heuristic classification',
            'alternative_intents': []
        }
    
    def _log_interaction(self, query: str, classification: Dict[str, Any], 
                        context: Dict[str, Any]):
        """Log classification interaction."""
        log_entry = {
            'timestamp': time.time(),
            'query': query[:200],
            'intent': classification['intent'],
            'confidence': classification['confidence'],
            'context_size': len(context.get('conversation_history', []))
        }
        self.interaction_history.append(log_entry)
