"""
ReAct Tool Wrappers
Wraps existing agents as tools for ReAct agent to use.
"""
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json
import re
from functools import wraps

logger = logging.getLogger(__name__)


# ==========================================
# Common Utilities (DRY - Don't Repeat Yourself)
# ==========================================

def get_project_paths() -> Dict[str, Path]:
    """
    Get commonly used project paths.
    
    Returns:
        dict: Dictionary with keys: backend_dir, project_root, media_dir, chroma_base_dir
    """
    backend_dir = Path(__file__).parent.parent.parent
    project_root = backend_dir.parent
    media_dir = project_root / "media"
    chroma_base_dir = media_dir / "output" / "chroma_db"
    
    return {
        'backend_dir': backend_dir,
        'project_root': project_root,
        'media_dir': media_dir,
        'chroma_base_dir': chroma_base_dir
    }


def load_json_file(file_path: Path) -> Optional[Dict]:
    """
    Load JSON file with error handling.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        dict if successful, None if failed
    """
    try:
        if not file_path.exists():
            logger.error(f"JSON file not found: {file_path}")
            return None
        
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return None


def get_premium_registry() -> Optional[Dict]:
    """
    Load premium workbooks registry.
    
    Returns:
        dict: Registry data if successful, None otherwise
    """
    paths = get_project_paths()
    registry_path = paths['media_dir'] / "premium_workbooks" / "premium_workbooks_registry.json"
    return load_json_file(registry_path)


def handle_tool_errors(func):
    """
    Decorator for common error handling in tool execute() methods.
    Catches exceptions, logs them, and returns formatted error messages.
    """
    @wraps(func)
    def wrapper(self, action_input: str, context: Dict[str, Any]) -> str:
        self.usage_count += 1
        logger.info(f"[ReAct Tool] {self.name}: {action_input[:100]}")
        
        try:
            return func(self, action_input, context)
        except json.JSONDecodeError as e:
            logger.error(f"{self.name} - Invalid JSON: {e}")
            return f"Error: Invalid JSON format in action_input"
        except Exception as e:
            logger.error(f"{self.name} error: {e}", exc_info=True)
            return f"Error in {self.name}: {str(e)}"
    
    return wrapper
class ReActTool:
    """Base class for ReAct tools."""
    
    def __init__(self, name: str, description: str, agent=None):
        """
        Initialize tool.
        
        Args:
            name: Tool identifier
            description: What the tool does
            agent: Underlying agent/component (optional for some tools)
        """
        self.name = name
        self.description = description
        self.agent = agent
        self.usage_count = 0
    
    def execute(self, action_input: str, context: Dict[str, Any]) -> str:
        """
        Execute tool.
        
        Args:
            action_input: JSON string with tool-specific parameters
            context: Execution context
            
        Returns:
            Observation string for ReAct agent
        """
        raise NotImplementedError("Subclasses must implement execute()")


class ProductListTool(ReActTool):
    """Tool for listing available insurance products."""
    
    def __init__(self):
        super().__init__(
            name="list_products",
            description="List all available insurance products in the system",
            agent=None
        )
    
    @handle_tool_errors
    def execute(self, action_input: str, context: Dict[str, Any]) -> str:
        """List all available products."""
        paths = get_project_paths()
        base_dir = paths['chroma_base_dir']
        
        if not base_dir.exists():
            return "Error: No products available. ChromaDB directory not found."
        
        # List all product directories
        available_products = [
            d.name for d in base_dir.iterdir()
            if d.is_dir() and (d / "chroma.sqlite3").exists()
        ]
        
        if not available_products:
            return "Error: No products available. Please run ingestion first."
        
        logger.info(f"Available products: {available_products}")
        
        return f"Available insurance products in the system: {', '.join(available_products)}. " \
               f"Total: {len(available_products)} products."


class PremiumCalculatorTool(ReActTool):
    """Tool for premium calculations."""
    
    def __init__(self, calculator):
        super().__init__(
            name="premium_calculator",
            description="Calculate insurance premiums based on age, plan, family composition",
            agent=calculator
        )
    
    @handle_tool_errors
    def execute(self, action_input: str, context: Dict[str, Any]) -> str:
        """Execute premium calculation."""
        params = json.loads(action_input)
        
        # Validate parameters
        validation_error = self._validate_params(params)
        if validation_error:
            return validation_error
        
        # Find matching doc_name and create calculator
        calculator, error = self._create_calculator(params['policy_name'])
        if error:
            return error
        
        # Calculate premium
        result = self._perform_calculation(calculator, params)
        
        # Format result
        return self._format_result(result, params['policy_name'])
    
    def _validate_params(self, params: Dict) -> Optional[str]:
        """Validate input parameters."""
        if not params.get('policy_name'):
            return "Error: policy_name is required"
        
        if not params.get('members'):
            return "Error: members list is required with age information"
        
        return None
    
    def _create_calculator(self, policy_name: str):
        """Create product-specific calculator."""
        doc_name = self._find_doc_name_for_policy(policy_name)
        
        if not doc_name:
            available_products = self._get_available_products()
            return None, f"Error: Unknown policy '{policy_name}'. Available products: {', '.join(available_products)}"
        
        try:
            from agents.calculators import PremiumCalculator
            calculator = PremiumCalculator(doc_name=doc_name)
            logger.info(f"Created calculator for {policy_name} using doc_name '{doc_name}'")
            return calculator, None
        except FileNotFoundError as e:
            return None, f"Error: Premium data not available for {policy_name}. {str(e)}"
        except Exception as e:
            logger.error(f"Failed to create calculator for {policy_name}: {e}", exc_info=True)
            return None, f"Error: Failed to load premium data for {policy_name}. {str(e)}"
    
    def _perform_calculation(self, calculator, params: Dict) -> Dict:
        """Perform the actual premium calculation."""
        return calculator.calculate_premium(
            policy_type=params.get('policy_type', 'individual'),
            members=params.get('members', []),
            sum_insured=params.get('sum_insured', 500000),
            include_gst=True
        )
    
    def _format_result(self, result: Dict, policy_name: str) -> str:
        """Format calculation result as observation string."""
        if 'error' in result:
            return f"Error calculating premium: {result['error']}"
        
        total = result.get('total_premium', 0)
        gross = result.get('gross_premium', 0)
        gst = result.get('gst_amount', 0)
        
        return f"Premium calculated for {policy_name}: ₹{total:,.2f} annually. " \
               f"Base premium: ₹{gross:,.2f}, GST: ₹{gst:,.2f}"
    
    def _find_doc_name_for_policy(self, policy_name: str) -> Optional[str]:
        """Find registry doc_name for a policy name."""
        registry = get_premium_registry()
        if not registry:
            return None
        
        policy_lower = policy_name.lower()
        
        # Strategy 1: Exact match (case-insensitive)
        for doc_name in registry.keys():
            if doc_name.lower() == policy_lower:
                logger.info(f"Exact match: {policy_name} -> {doc_name}")
                return doc_name
        
        # Strategy 2: Pattern matching
        normalized_policy = policy_lower.replace('activ', '').replace('_', '').replace('-', '')
        
        for doc_name in registry.keys():
            normalized_doc = doc_name.lower().replace('activ', '').replace('_', '').replace('-', '').replace('premium', '').replace('chart', '')
            
            if normalized_policy in normalized_doc or normalized_doc in normalized_policy:
                logger.info(f"Pattern match: {policy_name} -> {doc_name}")
                return doc_name
        
        logger.warning(f"No registry match found for policy: {policy_name}")
        return None
    
    def _get_available_products(self) -> list:
        """Get list of available product names from registry."""
        registry = get_premium_registry()
        if not registry:
            return []
        
        products = []
        for doc_name in registry.keys():
            # Remove 'premium_chart' suffix and convert to PascalCase
            name = doc_name.replace('_premium_chart', '')
            name_parts = name.split('_')
            friendly_name = ''.join(word.capitalize() for word in name_parts)
            products.append(friendly_name)
        
        return products


class PolicyComparatorTool(ReActTool):
    """Tool for policy comparisons."""
    
    def __init__(self, comparator):
        super().__init__(
            name="policy_comparator",
            description="Compare insurance policies, plans, premiums, coverage details",
            agent=comparator
        )
    
    @handle_tool_errors
    def execute(self, action_input: str, context: Dict[str, Any]) -> str:
        """Execute policy comparison."""
        params = json.loads(action_input)
        
        policy1 = params.get('policy1')
        policy2 = params.get('policy2')
        members = params.get('members', [])
        sum_insured = params.get('sum_insured', 500000)
        
        if not policy1 or not policy2:
            return "Error: Both policy1 and policy2 are required"
        
        if not members:
            return "Error: members list is required for comparison"
        
        # Check if premium calculator is available
        if not self.agent.is_available():
            return "Error: Premium calculator not available for comparison"
        
        # Calculate premiums for both policies
        policy_type = 'individual' if len(members) == 1 else 'family_floater'
        
        result1 = self.agent.premium_calculator.calculate_premium(
            policy_type=policy_type,
            members=members,
            sum_insured=sum_insured,
            include_gst=True
        )
        
        result2 = self.agent.premium_calculator.calculate_premium(
            policy_type=policy_type,
            members=members,
            sum_insured=sum_insured,
            include_gst=True
        )
        
        if result1.get('success') and result2.get('success'):
            premium1 = result1['premium'].get('total_with_gst', 0)
            premium2 = result2['premium'].get('total_with_gst', 0)
            diff = abs(premium1 - premium2)
            cheaper = policy1 if premium1 < premium2 else policy2
            
            return f"Comparison: {policy1} costs ₹{premium1:,.2f} vs {policy2} costs ₹{premium2:,.2f}. " \
                   f"{cheaper} is cheaper by ₹{diff:,.2f}"
        else:
            error1 = result1.get('error', 'Unknown error')
            error2 = result2.get('error', 'Unknown error')
            return f"Error comparing policies. {policy1}: {error1}, {policy2}: {error2}"


class DocumentRetrieverTool(ReActTool):
    """Tool for document retrieval."""
    
    def __init__(self, retriever):
        super().__init__(
            name="document_retriever",
            description="Retrieve policy information, coverage details, terms and conditions",
            agent=retriever
        )
    
    @handle_tool_errors
    def execute(self, action_input: str, context: Dict[str, Any]) -> str:
        """Execute document retrieval."""
        params = json.loads(action_input)
        
        query = params.get('query')
        k = params.get('k', 5)
        doc_type_filter = params.get('doc_type_filter')
        
        if not query:
            return "Error: query parameter is required"
        
        # Determine ChromaDB path
        chroma_db_dir = self._determine_chroma_path(query, context)
        logger.info(f"Using ChromaDB path: {chroma_db_dir}")
        
        # Switch retriever to appropriate ChromaDB
        if hasattr(self.agent, 'set_chroma_db_dir'):
            self.agent.set_chroma_db_dir(chroma_db_dir)
        
        # Perform retrieval
        documents = self.agent.retrieve(
            query_text=query,
            k=k,
            doc_type_filter=doc_type_filter if doc_type_filter else None
        )
        
        # Format result
        return self._format_retrieval_result(documents, chroma_db_dir)
    
    def _determine_chroma_path(self, query: str, context: Dict[str, Any]) -> str:
        """Determine which ChromaDB to use."""
        paths = get_project_paths()
        
        # Auto-detect product from query text
        detected_product = self._detect_product_from_query(query)
        
        if detected_product:
            chroma_db_dir = str(paths['chroma_base_dir'] / detected_product)
            logger.info(f"Auto-detected product from query: {detected_product}")
        elif context.get('chroma_db_dir'):
            chroma_db_dir = context.get('chroma_db_dir')
            logger.info(f"Using context-provided ChromaDB")
        else:
            selected_product = context.get('selected_product', 'ActivAssure')
            chroma_db_dir = str(paths['chroma_base_dir'] / selected_product)
            logger.info(f"Using default product: {selected_product}")
        
        return chroma_db_dir
    
    def _format_retrieval_result(self, documents: list, chroma_db_dir: str) -> str:
        """Format retrieval result as observation string."""
        if documents:
            first_doc = documents[0]
            content = first_doc.get('content', '')[:300]
            metadata = first_doc.get('metadata', {})
            
            return f"Retrieved {len(documents)} relevant documents. " \
                   f"Top result: {content}... " \
                   f"(Source: {metadata.get('source', 'unknown')})"
        else:
            if self.agent.collection is None:
                product_name = chroma_db_dir.split('/')[-1] if '/' in chroma_db_dir else chroma_db_dir.split('\\')[-1]
                return f"Error: No documents available for '{product_name}'. The product database is empty or not initialized. Please run ingestion for this product first."
            else:
                return "No relevant documents found for the query"
    
    def _detect_product_from_query(self, query: str) -> Optional[str]:
        """Detect product name from query text."""
        paths = get_project_paths()
        base_dir = paths['chroma_base_dir']
        
        available_products = []
        
        if base_dir.exists():
            available_products = [d.name for d in base_dir.iterdir() if d.is_dir()]
            logger.info(f"Available products for detection: {available_products}")
        else:
            logger.warning(f"ChromaDB base directory not found: {base_dir}")
        
        # Search for product names in query (case-insensitive)
        query_lower = query.lower()
        for product in available_products:
            if re.search(r'\b' + re.escape(product.lower()) + r'\b', query_lower):
                logger.info(f"Detected product '{product}' in query")
                return product
        
        return None
