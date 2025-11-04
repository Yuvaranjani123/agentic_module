"""
Prompts Configuration Package

Contains all prompt templates and configurations for agents.
"""

# Comparison prompts
from .comparison_prompts import (
    ASPECT_COMPARISON_TEMPLATE,
    CUSTOM_COMPARISON_TEMPLATE,
    PREMIUM_COMPARISON_TEMPLATE,
    ASPECT_REFINEMENT_KEYWORDS,
    DEFAULT_COMPARISON_ASPECTS,
    build_aspect_sections,
    build_product_contexts,
    build_premium_data_section,
    build_member_info,
    refine_query_for_aspect
)

# Orchestrator prompts
from .orchestrator_prompts import (
    INTENT_CLASSIFICATION_PROMPT,
    PREMIUM_PARAMETER_EXTRACTION_PROMPT,
    get_comparison_parameter_extraction_prompt,
    VALID_INTENTS,
    DEFAULT_INTENT
)

# ReAct Agent prompts
from .react_prompts import (
    REACT_SYSTEM_PROMPT,
    REACT_USER_PROMPT_TEMPLATE,
    TOOL_DESCRIPTIONS,
    get_tool_list_for_prompt,
    format_react_user_prompt
)

# Intent Learning prompts
from .intent_prompts import (
    INTENT_CLASSIFICATION_PROMPT_TEMPLATE,
    DEFAULT_INTENT as INTENT_DEFAULT,
    VALID_INTENTS as INTENT_VALID_INTENTS,
    INTENT_PATTERN_EXAMPLES,
    format_intent_classification_prompt,
    get_pattern_examples_for_intent
)

__all__ = [
    # Comparison prompts
    'ASPECT_COMPARISON_TEMPLATE',
    'CUSTOM_COMPARISON_TEMPLATE',
    'PREMIUM_COMPARISON_TEMPLATE',
    'ASPECT_REFINEMENT_KEYWORDS',
    'DEFAULT_COMPARISON_ASPECTS',
    'build_aspect_sections',
    'build_product_contexts',
    'build_premium_data_section',
    'build_member_info',
    'refine_query_for_aspect',
    # Orchestrator prompts
    'INTENT_CLASSIFICATION_PROMPT',
    'PREMIUM_PARAMETER_EXTRACTION_PROMPT',
    'get_comparison_parameter_extraction_prompt',
    'VALID_INTENTS',
    'DEFAULT_INTENT',
    # ReAct prompts
    'REACT_SYSTEM_PROMPT',
    'REACT_USER_PROMPT_TEMPLATE',
    'TOOL_DESCRIPTIONS',
    'get_tool_list_for_prompt',
    'format_react_user_prompt',
    # Intent Learning prompts
    'INTENT_CLASSIFICATION_PROMPT_TEMPLATE',
    'INTENT_DEFAULT',
    'INTENT_VALID_INTENTS',
    'INTENT_PATTERN_EXAMPLES',
    'format_intent_classification_prompt',
    'get_pattern_examples_for_intent',
]
