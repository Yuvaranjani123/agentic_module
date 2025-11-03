"""
Orchestrator Prompts Configuration
Version: 1.0
Last Updated: November 3, 2025

All prompt templates used by the AgentOrchestrator for intent classification
and parameter extraction.
"""

# ============================================================================
# INTENT CLASSIFICATION PROMPT
# ============================================================================

INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for an insurance assistant system.
Analyze the user's query and classify it into ONE of these categories:

1. PREMIUM_CALCULATION - User wants to calculate insurance premium/cost
   Keywords: calculate premium, how much, cost, price, what will i pay, premium for, quote
   
2. POLICY_COMPARISON - User wants to compare different insurance products/policies
   Keywords: compare, difference between, which is better, vs, versus, contrast, similar to
   
3. DOCUMENT_RETRIEVAL - User wants information from policy documents
   Keywords: what is covered, explain, benefits, terms, conditions, eligibility, coverage details
   
4. GENERAL_INSURANCE - General insurance questions that need document search
   Default category if not premium calculation or comparison

Examples:
- "Calculate premium for 2 adults aged 35 and 40 with 5L cover" → PREMIUM_CALCULATION
- "Compare ActivAssure with HealthShield" → POLICY_COMPARISON
- "What are the differences between these two policies?" → POLICY_COMPARISON
- "What are the vaccination benefits for children?" → DOCUMENT_RETRIEVAL
- "How much will I pay for family floater with 10L cover?" → PREMIUM_CALCULATION
- "Explain the claim process" → DOCUMENT_RETRIEVAL
- "Which policy has better maternity coverage?" → POLICY_COMPARISON

User Query: {query}

Classification (respond with only the category name):"""


# ============================================================================
# PREMIUM PARAMETER EXTRACTION PROMPT
# ============================================================================

PREMIUM_PARAMETER_EXTRACTION_PROMPT = """Extract premium calculation parameters from the user's query.

Return a JSON object with these fields:
- policy_type: "individual" or "family_floater"
- members: list of member ages (integers) - e.g., [35, 40, 7] for 2 adults and 1 child
- sum_insured: coverage amount in lakhs (convert to number) - e.g., "5L" → 500000, "10L" → 1000000
- composition: family composition if specified - e.g., "2 Adults + 1 Child"
- plan: plan name if mentioned (e.g., "Diamond")

If information is missing, set field to null.

Examples:
Query: "Calculate premium for 35 year old with 5L cover"
Output: {{"policy_type": "individual", "members": [35], "sum_insured": 500000, "composition": null, "plan": null}}

Query: "Premium for family floater 2 adults aged 35, 40 and 1 child aged 7 with 10L Diamond plan"
Output: {{"policy_type": "family_floater", "members": [35, 40, 7], "sum_insured": 1000000, "composition": "2 Adults + 1 Child", "plan": "Diamond"}}

User Query: {query}

JSON Output:"""


# ============================================================================
# COMPARISON PARAMETER EXTRACTION PROMPT
# ============================================================================

def get_comparison_parameter_extraction_prompt(available_products: list) -> str:
    """
    Get the comparison parameter extraction prompt with available products.
    
    Args:
        available_products: List of available product names
        
    Returns:
        Formatted prompt template string
    """
    return f"""Extract policy comparison parameters from the user's query.

Available products in the system: {available_products}

Return a JSON object with these fields:
- products: list of product names mentioned (match with available products, null if not specified)
- aspects: list of specific aspects to compare if mentioned (e.g., ["coverage", "premium", "exclusions"])
- comparison_type: "specific" if products are mentioned, "general" if asking about all products

Examples:
Query: "Compare ActivAssure with HealthShield"
Output: {{"products": ["ActivAssure", "HealthShield"], "aspects": null, "comparison_type": "specific"}}

Query: "What are the differences in maternity coverage between all policies?"
Output: {{"products": null, "aspects": ["maternity coverage"], "comparison_type": "general"}}

Query: "Which policy has better claim process and premium?"
Output: {{"products": null, "aspects": ["claim process", "premium"], "comparison_type": "general"}}

User Query: {{query}}

JSON Output:"""


# ============================================================================
# VALID INTENT CATEGORIES
# ============================================================================

VALID_INTENTS = [
    'PREMIUM_CALCULATION',
    'POLICY_COMPARISON',
    'DOCUMENT_RETRIEVAL',
    'GENERAL_INSURANCE'
]


# ============================================================================
# DEFAULT INTENT
# ============================================================================

DEFAULT_INTENT = 'DOCUMENT_RETRIEVAL'
