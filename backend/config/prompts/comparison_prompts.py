"""
Comparison Prompts Configuration
Version: 1.0
Last Updated: October 31, 2025

All prompt templates used by the PolicyComparisonAgent for comparing insurance products.
"""

# ============================================================================
# ASPECT-BASED COMPARISON PROMPT
# ============================================================================

ASPECT_COMPARISON_TEMPLATE = """You are an insurance policy comparison expert. Compare the following insurance products based on the provided information.

Create a detailed, structured comparison covering each aspect. Use tables where appropriate.

{aspect_sections}

Based on the above information, create a comprehensive comparison:

1. **Summary Table**: Create a comparison table showing key differences
2. **Detailed Analysis**: For each aspect, explain the differences
3. **Strengths & Weaknesses**: Highlight what each product excels at
4. **Recommendations**: Suggest which product might be better for different customer profiles

Be factual and only use information from the provided context. If information is missing, clearly state it.
"""


# ============================================================================
# CUSTOM COMPARISON PROMPT
# ============================================================================

CUSTOM_COMPARISON_TEMPLATE = """You are an insurance policy comparison expert. 

User Question: {query}

Compare the following insurance products SPECIFICALLY based on this question. Focus ONLY on the aspect mentioned in the question.

{product_contexts}

Based on the information above, answer the user's question: "{query}"

IMPORTANT:
- Focus ONLY on the specific aspect mentioned in the question
- Do NOT provide a general comparison of all features
- If the question asks about a specific benefit (e.g., "annual health checkup"), compare ONLY that benefit
- Create a comparison table showing the specific aspect for each product
- Highlight the key differences in this specific area
- If information is missing for this specific aspect, clearly state it

Provide a clear, structured comparison that directly addresses ONLY what was asked.
"""


# ============================================================================
# PREMIUM COMPARISON PROMPT
# ============================================================================

PREMIUM_COMPARISON_TEMPLATE = """You are an insurance policy comparison expert with access to both policy documents and calculated premium amounts.

User Question: {query}

## Document Information

{document_contexts}

## Calculated Premiums

{premium_data}

{member_info}

Based on the above information (both documents and calculated premiums), answer: "{query}"

Create a comprehensive comparison that includes:
1. **Premium Comparison Table** (if premiums calculated)
2. **Coverage & Benefits** comparison
3. **Value Analysis**: Which offers better value for money?
4. **Recommendation**: Which product is better for the given scenario?

Be factual and use both the document context and calculated premiums.
"""


# ============================================================================
# ASPECT REFINEMENT KEYWORDS
# ============================================================================

ASPECT_REFINEMENT_KEYWORDS = {
    'annual health checkup': 'annual health checkup benefits',
    'health checkup': 'annual health checkup benefits',
    'vaccination': 'vaccination coverage and benefits',
    'maternity': 'maternity benefits and coverage',
    'ambulance': 'ambulance coverage',
    'pre-existing': 'pre-existing disease coverage',
    'waiting period': 'waiting periods',
    'claim': 'claim process and settlement',
    'network hospital': 'network hospitals and cashless facility',
    'room rent': 'room rent limits and coverage',
    'co-payment': 'co-payment requirements',
    'restoration': 'sum insured restoration benefits',
    'no claim bonus': 'no claim bonus benefits',
    'daycare': 'daycare procedures coverage',
}


# ============================================================================
# DEFAULT COMPARISON ASPECTS
# ============================================================================

DEFAULT_COMPARISON_ASPECTS = [
    'coverage and benefits',
    'premium and pricing',
    'exclusions and limitations',
    'claim process',
    'eligibility criteria'
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_aspect_sections(product_data: dict, aspects: list) -> str:
    """
    Build aspect sections for the comparison prompt.
    
    Args:
        product_data: Dictionary mapping products to their aspect data
        aspects: List of aspects being compared
        
    Returns:
        Formatted string with all aspect sections
        
    Example:
        >>> product_data = {
        ...     'ProductA': {'coverage': [{'content': 'Covers X'}]},
        ...     'ProductB': {'coverage': [{'content': 'Covers Y'}]}
        ... }
        >>> build_aspect_sections(product_data, ['coverage'])
        '## COVERAGE\\n\\n### ProductA\\n- Covers X\\n...'
    """
    sections = []
    
    for aspect in aspects:
        section = f"\n## {aspect.upper()}\n\n"
        for product, data in product_data.items():
            section += f"### {product}\n"
            chunks = data.get(aspect, [])
            if chunks:
                for i, chunk in enumerate(chunks[:3], 1):  # Top 3 chunks per aspect
                    content = chunk.get('content', '')[:300]
                    section += f"- {content}...\n"
            else:
                section += "- No information available\n"
            section += "\n"
        sections.append(section)
    
    return ''.join(sections)


def build_product_contexts(product_contexts: dict, max_chunks: int = 5) -> str:
    """
    Build product context sections for custom comparison.
    
    Args:
        product_contexts: Dictionary mapping products to their chunks
        max_chunks: Maximum number of chunks to include per product
        
    Returns:
        Formatted string with product contexts
        
    Example:
        >>> contexts = {'ProductA': [{'content': 'Feature X'}]}
        >>> build_product_contexts(contexts)
        '### ProductA\\n- Feature X\\n'
    """
    sections = []
    
    for product, chunks in product_contexts.items():
        section = f"\n### {product}\n"
        if chunks:
            for chunk in chunks[:max_chunks]:
                section += f"- {chunk.get('content', '')}\n"
        else:
            section += "- No relevant information found\n"
        section += "\n"
        sections.append(section)
    
    return ''.join(sections)


def build_premium_data_section(premium_results: dict) -> str:
    """
    Build premium data section for premium comparison.
    
    Args:
        premium_results: Dictionary mapping products to their premium calculations
        
    Returns:
        Formatted string with premium data
        
    Example:
        >>> results = {'ProductA': {'success': True, 'total_premium': 10000}}
        >>> build_premium_data_section(results)
        '### ProductA\\n- **Total Premium**: ₹10,000.00\\n...'
    """
    sections = []
    
    for product, premium_data in premium_results.items():
        section = f"### {product}\n"
        if not premium_data.get('success', False) or 'error' in premium_data:
            error_msg = premium_data.get('error', 'Unknown error')
            section += f"- Premium calculation not available: {error_msg}\n"
        else:
            total = premium_data.get('total_premium', 0)
            base = premium_data.get('base_premium', 0)
            gst_amt = premium_data.get('gst_amount', 0)
            gst_rate = premium_data.get('gst_rate', 0)
            
            section += f"- **Total Premium (incl. GST)**: ₹{total:,.2f}\n"
            section += f"- **Base Premium**: ₹{base:,.2f}\n"
            section += f"- **GST Amount**: ₹{gst_amt:,.2f}\n"
            section += f"- **GST Rate**: {gst_rate:.0f}%\n"
        section += "\n"
        sections.append(section)
    
    return ''.join(sections)


def build_member_info(premium_params: dict) -> str:
    """
    Build member information section for premium comparison.
    
    Args:
        premium_params: Dictionary with members and sum_insured
        
    Returns:
        Formatted string with member information
        
    Example:
        >>> params = {'members': [{'age': 30}, {'age': 28}], 'sum_insured': 500000}
        >>> build_member_info(params)
        '**Calculated for**: 2 members (ages: [30, 28]), Sum Insured: ₹5,00,000\\n'
    """
    if not premium_params.get('members'):
        return ""
    
    ages = [m.get('age') for m in premium_params['members']]
    sum_insured = premium_params.get('sum_insured', 0)
    
    return f"\n**Calculated for**: {len(ages)} members (ages: {ages}), Sum Insured: ₹{sum_insured:,}\n"


def refine_query_for_aspect(query: str) -> str:
    """
    Refine a comparison query to focus on specific aspects.
    
    Args:
        query: Original user query
        
    Returns:
        Refined query focusing on detected aspect
        
    Example:
        >>> refine_query_for_aspect("compare annual health checkup")
        'What are the annual health checkup benefits details?'
    """
    query_lower = query.lower()
    
    for keyword, refined_aspect in ASPECT_REFINEMENT_KEYWORDS.items():
        if keyword in query_lower:
            return f"What are the {refined_aspect} details?"
    
    return query
