"""
Intent Learning Prompts Configuration

Prompts for learning-based intent classification system.
"""

# Intent Classification Prompt Template
INTENT_CLASSIFICATION_PROMPT_TEMPLATE = """Classify the user's insurance query into one of these intents:

**Available Intents:**

1. PREMIUM_CALCULATION - User wants to calculate insurance premiums
   - Examples: "Calculate premium for age 32", "How much for family floater?", "Premium for 2 adults"
   
2. POLICY_COMPARISON - User wants to compare insurance policies or options
   - Examples: "Compare ActivAssure with ActivFit", "Which is better?", "Difference between plans"
   
3. DOCUMENT_RETRIEVAL - User wants information from insurance documents
   - Examples: "What is maternity coverage?", "Show me benefits", "Explain waiting period"
   
4. COMPLEX_QUERY - Multi-step query combining multiple intents
   - Examples: "Calculate premium then compare", "Show benefits and calculate cost"
   
5. GENERAL_INSURANCE - General insurance advice or questions
   - Examples: "What is sum insured?", "How does insurance work?", "Should I buy insurance?"

**User Query:** "{query}"

**Recent Conversation:**
{conversation_context}

**Learned Patterns (from past interactions):**
{learned_patterns}

**Your Task:**
Analyze the query carefully and classify it into the most appropriate intent.

**Response Format (JSON):**
{{
    "intent": "<INTENT_NAME>",
    "confidence": <0.0-1.0>,
    "reasoning": "<brief explanation of why you chose this intent>",
    "keywords_detected": ["keyword1", "keyword2"],
    "alternative_intents": [
        {{"intent": "<name>", "confidence": <0.0-1.0>}}
    ]
}}

**Important Notes:**
- If query mentions multiple actions (calculate AND compare), classify as COMPLEX_QUERY
- Use learned patterns to improve accuracy
- Consider conversation context for ambiguous queries
- Confidence should reflect how certain you are (0.0-1.0)"""


# Fallback Intent Configuration
DEFAULT_INTENT = 'DOCUMENT_RETRIEVAL'
VALID_INTENTS = [
    'PREMIUM_CALCULATION',
    'POLICY_COMPARISON',
    'DOCUMENT_RETRIEVAL',
    'COMPLEX_QUERY',
    'GENERAL_INSURANCE'
]

# Intent Pattern Examples (for bootstrapping)
INTENT_PATTERN_EXAMPLES = {
    'PREMIUM_CALCULATION': [
        'calculate premium',
        'how much',
        'cost for',
        'price for',
        'premium for',
        'calculate for',
        'annual premium'
    ],
    'POLICY_COMPARISON': [
        'compare',
        'difference between',
        'which is better',
        'vs',
        'versus',
        'comparison',
        'cheaper'
    ],
    'DOCUMENT_RETRIEVAL': [
        'what is',
        'explain',
        'tell me about',
        'coverage for',
        'benefits',
        'show me',
        'details of'
    ],
    'COMPLEX_QUERY': [
        'then',
        'and then',
        'after that',
        'also',
        'calculate and compare',
        'first ... then'
    ],
    'GENERAL_INSURANCE': [
        'what is insurance',
        'how does insurance work',
        'should i',
        'is it worth',
        'general question'
    ]
}


def format_intent_classification_prompt(
    query: str,
    conversation_context: str = "No previous conversation",
    learned_patterns: str = "No learned patterns yet"
) -> str:
    """
    Format the intent classification prompt.
    
    Args:
        query: User's query to classify
        conversation_context: Recent conversation history
        learned_patterns: Learned patterns from past interactions
        
    Returns:
        Formatted prompt for LLM
    """
    return INTENT_CLASSIFICATION_PROMPT_TEMPLATE.format(
        query=query,
        conversation_context=conversation_context,
        learned_patterns=learned_patterns
    )


def get_pattern_examples_for_intent(intent: str) -> list:
    """
    Get example patterns for a specific intent.
    
    Args:
        intent: Intent name
        
    Returns:
        List of example patterns
    """
    return INTENT_PATTERN_EXAMPLES.get(intent, [])
