"""
ReAct Tool Wrappers
Wraps existing agents as tools for ReAct agent to use.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ReActTool:
    """Base class for ReAct tools."""
    
    def __init__(self, name: str, description: str, agent):
        """
        Initialize tool.
        
        Args:
            name: Tool identifier
            description: What the tool does
            agent: Underlying agent/component
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


class PremiumCalculatorTool(ReActTool):
    """Tool for premium calculations."""
    
    def __init__(self, calculator):
        super().__init__(
            name="premium_calculator",
            description="Calculate insurance premiums based on age, plan, family composition",
            agent=calculator
        )
    
    def execute(self, action_input: str, context: Dict[str, Any]) -> str:
        """
        Execute premium calculation.
        
        Args:
            action_input: JSON string with parameters:
                - policy_name: Policy/plan name
                - policy_type: 'individual' or 'family_floater'
                - members: List of member dicts with 'age' and optional 'relation'
                - sum_insured: Coverage amount (default: 500000)
            context: Execution context
            
        Returns:
            Observation string for ReAct agent
        """
        self.usage_count += 1
        logger.info(f"[ReAct Tool] Premium Calculator: {action_input[:100]}")
        
        try:
            import json
            params = json.loads(action_input)
            
            policy_name = params.get('policy_name')
            policy_type = params.get('policy_type', 'individual')
            members = params.get('members', [])
            sum_insured = params.get('sum_insured', 500000)
            
            if not policy_name:
                return "Error: policy_name is required"
            
            if not members:
                return "Error: members list is required with age information"
            
            # Call actual PremiumCalculator.calculate_premium()
            result = self.agent.calculate_premium(
                policy_type=policy_type,
                members=members,
                sum_insured=sum_insured,
                include_gst=True
            )
            
            # Check if calculation was successful (no error key means success)
            if 'error' not in result:
                total = result.get('total_premium', 0)
                gross = result.get('gross_premium', 0)
                gst = result.get('gst_amount', 0)
                return f"Premium calculated for {policy_name}: ₹{total:,.2f} annually. " \
                       f"Base premium: ₹{gross:,.2f}, GST: ₹{gst:,.2f}"
            else:
                error_msg = result.get('error', 'Calculation failed')
                return f"Error calculating premium: {error_msg}"
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in action_input: {e}")
            return f"Error: Invalid JSON format in action_input"
        except Exception as e:
            logger.error(f"Premium calculator error: {e}", exc_info=True)
            return f"Error calculating premium: {str(e)}"


class PolicyComparatorTool(ReActTool):
    """Tool for policy comparisons."""
    
    def __init__(self, comparator):
        super().__init__(
            name="policy_comparator",
            description="Compare insurance policies, plans, premiums, coverage details",
            agent=comparator
        )
    
    def execute(self, action_input: str, context: Dict[str, Any]) -> str:
        """
        Execute policy comparison.
        
        Args:
            action_input: JSON string with parameters:
                - policy1: First policy name
                - policy2: Second policy name  
                - members: List of member dicts with 'age'
                - sum_insured: Coverage amount
            context: Execution context
            
        Returns:
            Observation string for ReAct agent
        """
        self.usage_count += 1
        logger.info(f"[ReAct Tool] Policy Comparator: {action_input[:100]}")
        
        try:
            import json
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
            
            # Calculate premium for policy1
            result1 = self.agent.premium_calculator.calculate_premium(
                policy_type='individual' if len(members) == 1 else 'family_floater',
                members=members,
                sum_insured=sum_insured,
                include_gst=True
            )
            
            # Calculate premium for policy2
            result2 = self.agent.premium_calculator.calculate_premium(
                policy_type='individual' if len(members) == 1 else 'family_floater',
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
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in action_input: {e}")
            return f"Error: Invalid JSON format in action_input"
        except Exception as e:
            logger.error(f"Policy comparator error: {e}", exc_info=True)
            return f"Error comparing policies: {str(e)}"


class DocumentRetrieverTool(ReActTool):
    """Tool for document retrieval."""
    
    def __init__(self, retriever):
        super().__init__(
            name="document_retriever",
            description="Retrieve policy information, coverage details, terms and conditions",
            agent=retriever
        )
    
    def execute(self, action_input: str, context: Dict[str, Any]) -> str:
        """
        Execute document retrieval.
        
        Args:
            action_input: JSON string with parameters:
                - query: Search query
                - policy_name: Optional policy name for filtering
                - k: Number of documents to retrieve (default: 5)
            context: Execution context (includes selected_product, chroma_db_dir)
            
        Returns:
            Observation string for ReAct agent
        """
        self.usage_count += 1
        logger.info(f"[ReAct Tool] Document Retriever: {action_input[:100]}")
        
        try:
            import json
            import os
            import re
            
            params = json.loads(action_input)
            
            query = params.get('query')
            k = params.get('k', 5)
            doc_type_filter = params.get('doc_type_filter')
            
            if not query:
                return "Error: query parameter is required"
            
            # Auto-detect product from query text
            detected_product = self._detect_product_from_query(query)
            
            # Determine which ChromaDB to use (need absolute paths for ChromaDB)
            from pathlib import Path
            backend_dir = Path(__file__).parent.parent.parent  # Go to backend/
            project_root = backend_dir.parent  # Go to project root
            
            if detected_product:
                # Use detected product with absolute path
                chroma_db_dir = str(project_root / "media" / "output" / "chroma_db" / detected_product)
                logger.info(f"Auto-detected product from query: {detected_product}")
                logger.info(f"Using ChromaDB path: {chroma_db_dir}")
            elif context.get('chroma_db_dir'):
                # Use context-provided path (already absolute from frontend)
                chroma_db_dir = context.get('chroma_db_dir')
                logger.info(f"Using context-provided ChromaDB: {chroma_db_dir}")
            else:
                # Fallback to default from context with absolute path
                selected_product = context.get('selected_product', 'ActivAssure')
                chroma_db_dir = str(project_root / "media" / "output" / "chroma_db" / selected_product)
                logger.info(f"Using default product: {selected_product}")
                logger.info(f"Using ChromaDB path: {chroma_db_dir}")
            
            # Switch retriever to the appropriate ChromaDB
            if hasattr(self.agent, 'set_chroma_db_dir'):
                self.agent.set_chroma_db_dir(chroma_db_dir)
            
            # Call actual DocumentRetriever.retrieve()
            documents = self.agent.retrieve(
                query_text=query,
                k=k,
                doc_type_filter=doc_type_filter if doc_type_filter else None
            )
            
            if documents:
                # Format the first document's content
                first_doc = documents[0]
                content = first_doc.get('content', '')[:300]  # First 300 chars
                metadata = first_doc.get('metadata', {})
                
                return f"Retrieved {len(documents)} relevant documents. " \
                       f"Top result: {content}... " \
                       f"(Source: {metadata.get('source', 'unknown')})"
            else:
                # Check if it's because collection is empty
                if self.agent.collection is None:
                    product_name = chroma_db_dir.split('/')[-1] if '/' in chroma_db_dir else chroma_db_dir.split('\\')[-1]
                    return f"Error: No documents available for '{product_name}'. The product database is empty or not initialized. Please run ingestion for this product first."
                else:
                    return "No relevant documents found for the query"
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in action_input: {e}")
            return f"Error: Invalid JSON format in action_input"
        except Exception as e:
            logger.error(f"Document retriever error: {e}", exc_info=True)
            return f"Error retrieving documents: {str(e)}"
    
    def _detect_product_from_query(self, query: str) -> str:
        """
        Detect product name from query text.
        
        Args:
            query: User query text
            
        Returns:
            Product name if detected, None otherwise
            
        Example:
            "What is maternity coverage in ActivFit?" -> "ActivFit"
            "Compare ActivAssure with ActivFit" -> "ActivAssure" (first found)
        """
        import os
        import re
        from pathlib import Path
        
        # Get available products from filesystem (use absolute path from Django project root)
        # Django runs from backend/, so go up one level to project root
        backend_dir = Path(__file__).parent.parent.parent  # Go up to backend/
        project_root = backend_dir.parent  # Go up to project root
        base_dir = project_root / "media" / "output" / "chroma_db"
        
        available_products = []
        
        if base_dir.exists():
            available_products = [
                d.name for d in base_dir.iterdir()
                if d.is_dir()
            ]
            logger.info(f"Available products for detection: {available_products}")
        else:
            logger.warning(f"ChromaDB base directory not found: {base_dir}")
        
        # Search for product names in query (case-insensitive)
        query_lower = query.lower()
        for product in available_products:
            # Check for exact match or word boundary match
            if re.search(r'\b' + re.escape(product.lower()) + r'\b', query_lower):
                logger.info(f"Detected product '{product}' in query")
                return product
        
        return None
