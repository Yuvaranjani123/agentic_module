"""
Policy Comparison Agent - Compares multiple insurance products.
This agent retrieves information about different products and generates comparison tables.
"""
import os
from dotenv import load_dotenv
load_dotenv()

import chromadb
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
import logging
from logs.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class PolicyComparisonAgent:
    """
    Agent that handles policy comparison across multiple products.
    Retrieves relevant information from multiple product databases and generates comparisons.
    """
    
    def __init__(self, chroma_base_dir: str, premium_calculator=None):
        """
        Initialize the Policy Comparison Agent.
        
        Args:
            chroma_base_dir: Base directory containing all product databases
            premium_calculator: Optional PremiumCalculator instance for premium comparisons
        """
        self.chroma_base_dir = chroma_base_dir
        self.available_products = self._detect_products()
        self.premium_calculator = premium_calculator
        
        # Initialize embeddings
        self.embeddings = AzureOpenAIEmbeddings(
            deployment=os.getenv("AZURE_OPENAI_TEXT_DEPLOYMENT_EMBEDDINGS"),
            openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
            openai_api_version=os.getenv("AZURE_OPENAI_TEXT_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        # Initialize LLM
        self.llm = AzureChatOpenAI(
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
            openai_api_version=os.getenv("AZURE_OPENAI_TEXT_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            temperature=0.3  # Lower temperature for more factual comparisons
        )
        
        logger.info(f"PolicyComparisonAgent initialized with {len(self.available_products)} products")
    
    def _detect_products(self):
        """Detect all available product databases."""
        products = []
        if os.path.exists(self.chroma_base_dir):
            for item in os.listdir(self.chroma_base_dir):
                item_path = os.path.join(self.chroma_base_dir, item)
                if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "chroma.sqlite3")):
                    products.append(item)
        return products
    
    def _get_product_collection(self, product_name: str):
        """Get ChromaDB collection for a specific product."""
        product_db_path = os.path.join(self.chroma_base_dir, product_name)
        client = chromadb.PersistentClient(path=product_db_path)
        return client.get_collection("insurance_chunks")
    
    def _refine_comparison_query(self, query: str) -> str:
        """
        Refine the comparison query to be more focused on specific aspects.
        Extracts the main topic/benefit being compared.
        
        Args:
            query: Original user query
            
        Returns:
            Refined query for better retrieval
        """
        query_lower = query.lower()
        
        # Common comparison patterns - extract specific aspect
        aspect_keywords = {
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
        
        # Check if query mentions specific aspect
        for keyword, refined_aspect in aspect_keywords.items():
            if keyword in query_lower:
                logger.info(f"Detected specific aspect: {keyword} -> {refined_aspect}")
                return f"What are the {refined_aspect} details?"
        
        # If no specific aspect, return original query
        return query
    
    def _retrieve_from_product(self, product_name: str, query: str, k: int = 5):
        """
        Retrieve relevant chunks from a specific product database.
        
        Args:
            product_name: Name of the product database
            query: Comparison query
            k: Number of chunks to retrieve
            
        Returns:
            List of retrieved chunks with metadata
        """
        try:
            collection = self._get_product_collection(product_name)
            query_embedding = self.embeddings.embed_query(query)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            
            chunks = []
            if results and results['documents'] and len(results['documents']) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    chunk = {
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'product': product_name
                    }
                    chunks.append(chunk)
            
            logger.info(f"Retrieved {len(chunks)} chunks from product: {product_name}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error retrieving from product {product_name}: {e}")
            return []
    
    def compare_products(self, product_names: list, comparison_aspects: list, k: int = 5):
        """
        Compare specific products on given aspects.
        
        Args:
            product_names: List of product names to compare
            comparison_aspects: List of aspects to compare (e.g., ['coverage', 'premium', 'exclusions'])
            k: Number of chunks to retrieve per product
            
        Returns:
            Dictionary with comparison results
        """
        logger.info(f"Comparing products: {product_names} on aspects: {comparison_aspects}")
        
        # Validate products
        invalid_products = [p for p in product_names if p not in self.available_products]
        if invalid_products:
            return {
                'success': False,
                'error': f"Products not found: {invalid_products}",
                'available_products': self.available_products
            }
        
        # Retrieve information for each product and aspect
        product_data = {}
        for product in product_names:
            product_data[product] = {}
            for aspect in comparison_aspects:
                query = f"What is the {aspect} for this insurance product?"
                chunks = self._retrieve_from_product(product, query, k=k)
                product_data[product][aspect] = chunks
        
        # Generate comparison using LLM
        comparison_prompt = self._build_comparison_prompt(product_data, comparison_aspects)
        
        try:
            response = self.llm.invoke(comparison_prompt)
            comparison_result = response.content
            
            return {
                'success': True,
                'products': product_names,
                'aspects': comparison_aspects,
                'comparison': comparison_result,
                'raw_data': product_data
            }
        except Exception as e:
            logger.error(f"Error generating comparison: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_comparison_prompt(self, product_data: dict, aspects: list):
        """Build prompt for LLM to generate comparison."""
        prompt = """You are an insurance policy comparison expert. Compare the following insurance products based on the provided information.

Create a detailed, structured comparison covering each aspect. Use tables where appropriate.

"""
        
        for aspect in aspects:
            prompt += f"\n## {aspect.upper()}\n\n"
            for product, data in product_data.items():
                prompt += f"### {product}\n"
                chunks = data.get(aspect, [])
                if chunks:
                    for i, chunk in enumerate(chunks[:3], 1):  # Top 3 chunks per aspect
                        prompt += f"- {chunk['content'][:300]}...\n"
                else:
                    prompt += "- No information available\n"
                prompt += "\n"
        
        prompt += """
Based on the above information, create a comprehensive comparison:

1. **Summary Table**: Create a comparison table showing key differences
2. **Detailed Analysis**: For each aspect, explain the differences
3. **Strengths & Weaknesses**: Highlight what each product excels at
4. **Recommendations**: Suggest which product might be better for different customer profiles

Be factual and only use information from the provided context. If information is missing, clearly state it.
"""
        
        return prompt
    
    def compare_all_products(self, comparison_aspects: list, k: int = 5):
        """
        Compare all available products.
        
        Args:
            comparison_aspects: List of aspects to compare
            k: Number of chunks to retrieve per product
            
        Returns:
            Comparison results for all products
        """
        if len(self.available_products) < 2:
            return {
                'success': False,
                'error': 'Need at least 2 products for comparison',
                'available_products': self.available_products
            }
        
        return self.compare_products(self.available_products, comparison_aspects, k)
    
    def get_available_products(self):
        """Get list of available products for comparison."""
        return self.available_products
    
    def quick_compare(self, product_names: list, k: int = 5):
        """
        Quick comparison with default aspects.
        
        Args:
            product_names: List of products to compare
            k: Number of chunks to retrieve
            
        Returns:
            Comparison results with default aspects
        """
        default_aspects = [
            'coverage and benefits',
            'premium and pricing',
            'exclusions and limitations',
            'claim process',
            'eligibility criteria'
        ]
        
        return self.compare_products(product_names, default_aspects, k)
    
    def custom_compare(self, query: str, product_names: list = None, k: int = 5):
        """
        Free-form comparison based on natural language query.
        
        Args:
            query: Natural language comparison query
            product_names: List of products to compare (None = all products)
            k: Number of chunks to retrieve
            
        Returns:
            Comparison results based on query
        """
        if product_names is None:
            product_names = self.available_products
        
        if len(product_names) < 2:
            return {
                'success': False,
                'error': 'Need at least 2 products for comparison'
            }
        
        logger.info(f"Custom comparison query: {query} for products: {product_names}")
        
        # Extract specific aspect if mentioned in query for more focused retrieval
        focused_query = self._refine_comparison_query(query)
        logger.info(f"Refined query for retrieval: {focused_query}")
        
        # Retrieve relevant information from each product
        product_contexts = {}
        for product in product_names:
            chunks = self._retrieve_from_product(product, focused_query, k=k)
            product_contexts[product] = chunks
        
        # Build custom comparison prompt
        prompt = f"""You are an insurance policy comparison expert. 

User Question: {query}

Compare the following insurance products SPECIFICALLY based on this question. Focus ONLY on the aspect mentioned in the question.

"""
        
        for product, chunks in product_contexts.items():
            prompt += f"\n### {product}\n"
            if chunks:
                for chunk in chunks[:5]:  # Top 5 chunks
                    prompt += f"- {chunk['content']}\n"
            else:
                prompt += "- No relevant information found\n"
            prompt += "\n"
        
        prompt += f"""
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
        
        try:
            response = self.llm.invoke(prompt)
            
            return {
                'success': True,
                'query': query,
                'products': product_names,
                'comparison': response.content,
                'sources': product_contexts
            }
        except Exception as e:
            logger.error(f"Error in custom comparison: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def compare_with_premium_calculation(self, query: str, product_names: list, premium_params: dict, k: int = 5):
        """
        Compare products including actual premium calculations.
        
        Args:
            query: Comparison query
            product_names: List of products to compare
            premium_params: Parameters for premium calculation (members, sum_insured, policy_type)
            k: Number of chunks to retrieve
            
        Returns:
            Comparison with document info AND calculated premiums
        """
        if not self.premium_calculator:
            logger.warning("Premium calculator not available, falling back to document-only comparison")
            return self.custom_compare(query, product_names, k)
        
        if len(product_names) < 2:
            return {
                'success': False,
                'error': 'Need at least 2 products for comparison'
            }
        
        logger.info(f"Comparison with premium calculation for: {product_names}")
        
        # Check if we can calculate premiums for the specified products
        available_workbooks = {}
        if hasattr(self.premium_calculator, 'get_available_workbooks'):
            try:
                workbooks = self.premium_calculator.get_available_workbooks()
                available_workbooks = workbooks
                logger.info(f"Available premium workbooks: {list(workbooks.keys())}")
            except Exception as e:
                logger.warning(f"Could not get available workbooks: {e}")
        
        # Check which products have premium data
        products_with_premium_data = []
        products_without_premium_data = []
        
        for product in product_names:
            # Check if a workbook exists for this product (case-insensitive match)
            has_workbook = any(
                product.lower() in wb_name.lower() or wb_name.lower() in product.lower()
                for wb_name in available_workbooks.keys()
            ) if available_workbooks else True  # Assume available if we can't check
            
            if has_workbook:
                products_with_premium_data.append(product)
            else:
                products_without_premium_data.append(product)
        
        # If no products have premium data, inform user
        if not products_with_premium_data and products_without_premium_data:
            return {
                'success': False,
                'error': f"Premium calculation data not available for: {', '.join(products_without_premium_data)}",
                'message': f"To compare premiums across {', '.join(product_names)}, please upload premium rate Excel files for each product.",
                'available_workbooks': list(available_workbooks.keys()) if available_workbooks else []
            }
        
        # Get document-based comparison first
        product_contexts = {}
        for product in product_names:
            chunks = self._retrieve_from_product(product, query, k=k)
            product_contexts[product] = chunks
        
        # Calculate premiums for products that have data
        premium_results = {}
        for product in product_names:
            try:
                # Check if this product has premium data
                if product in products_without_premium_data:
                    premium_results[product] = {
                        'success': False,
                        'error': f'Premium data not available for {product}',
                        'message': f'Please upload premium rate Excel file for {product}'
                    }
                    continue
                
                # Try to find a workbook matching this product
                matching_workbook = None
                for wb_name in available_workbooks.keys():
                    # Case-insensitive partial match
                    if product.lower() in wb_name.lower() or wb_name.lower() in product.lower():
                        matching_workbook = wb_name
                        logger.info(f"Found matching workbook '{wb_name}' for product '{product}'")
                        break
                
                # Create product-specific calculator or use existing if no match found
                if matching_workbook:
                    from .premium_calculator import PremiumCalculator
                    product_calculator = PremiumCalculator(doc_name=matching_workbook)
                    logger.info(f"Created calculator for product '{product}' using workbook '{matching_workbook}'")
                else:
                    product_calculator = self.premium_calculator
                    logger.warning(f"No specific workbook found for '{product}', using default calculator")
                
                # Try to calculate premium for this product
                result = product_calculator.calculate_premium(
                    policy_type=premium_params.get('policy_type', 'family_floater'),
                    members=premium_params.get('members', []),
                    sum_insured=premium_params.get('sum_insured', 500000)
                )
                
                # Check if calculation succeeded (no 'error' key means success)
                if 'error' not in result and result.get('total_premium') is not None:
                    premium_results[product] = {
                        'success': True,
                        'total_premium': result.get('total_premium'),
                        'base_premium': result.get('gross_premium'),  # Note: it's 'gross_premium' not 'base_premium'
                        'gst_amount': result.get('gst_amount'),
                        'gst_rate': result.get('gst_rate', 0) * 100  # Convert to percentage
                    }
                    logger.info(f"Premium calculated for {product}: ₹{result.get('total_premium'):,.2f}")
                else:
                    premium_results[product] = {
                        'success': False,
                        'error': result.get('error', 'Calculation failed')
                    }
                    logger.warning(f"Premium calculation failed for {product}: {result.get('error')}")
            except Exception as e:
                logger.error(f"Premium calculation failed for {product}: {e}")
                premium_results[product] = {'error': str(e)}
        
        # Build enhanced comparison prompt with both document info and calculated premiums
        prompt = f"""You are an insurance policy comparison expert with access to both policy documents and calculated premium amounts.

User Question: {query}

## Document Information

"""
        
        for product, chunks in product_contexts.items():
            prompt += f"\n### {product}\n"
            if chunks:
                for chunk in chunks[:3]:
                    prompt += f"- {chunk['content'][:300]}...\n"
            else:
                prompt += "- No relevant information found\n"
            prompt += "\n"
        
        # Add premium calculation results
        prompt += "\n## Calculated Premiums\n\n"
        
        has_any_premium = False
        for product, premium_data in premium_results.items():
            prompt += f"### {product}\n"
            if not premium_data.get('success', False) or 'error' in premium_data:
                prompt += f"- Premium calculation not available: {premium_data.get('error', 'Unknown error')}\n"
            else:
                has_any_premium = True
                prompt += f"- **Total Premium (incl. GST)**: ₹{premium_data.get('total_premium', 0):,.2f}\n"
                prompt += f"- **Base Premium**: ₹{premium_data.get('base_premium', 0):,.2f}\n"
                prompt += f"- **GST Amount**: ₹{premium_data.get('gst_amount', 0):,.2f}\n"
                prompt += f"- **GST Rate**: {premium_data.get('gst_rate', 0):.0f}%\n"
            prompt += "\n"
        
        if premium_params.get('members'):
            ages = [m.get('age') for m in premium_params['members']]
            prompt += f"\n**Calculated for**: {len(ages)} members (ages: {ages}), Sum Insured: ₹{premium_params.get('sum_insured', 0):,}\n"
        
        prompt += f"""
Based on the above information (both documents and calculated premiums), answer: "{query}"

Create a comprehensive comparison that includes:
1. **Premium Comparison Table** (if premiums calculated)
2. **Coverage & Benefits** comparison
3. **Value Analysis**: Which offers better value for money?
4. **Recommendation**: Which product is better for the given scenario?

Be factual and use both the document context and calculated premiums.
"""
        
        try:
            response = self.llm.invoke(prompt)
            
            # Build helpful messages for missing premium data
            missing_premium_products = [
                p for p, data in premium_results.items() 
                if not data.get('success', False) or 'error' in data
            ]
            additional_notes = []
            
            if missing_premium_products:
                additional_notes.append(
                    f"\n\n---\n**Note:** Premium calculation data is not available for: {', '.join(missing_premium_products)}. "
                    f"To enable premium comparison for these products, please upload their premium rate Excel files during ingestion."
                )
            
            if available_workbooks:
                available_list = ', '.join(available_workbooks.keys())
                additional_notes.append(
                    f"\n**Available Premium Workbooks:** {available_list}"
                )
            
            final_comparison = response.content
            if additional_notes:
                final_comparison += '\n'.join(additional_notes)
            
            return {
                'success': True,
                'query': query,
                'products': product_names,
                'comparison': final_comparison,
                'sources': product_contexts,
                'premium_calculations': premium_results if has_any_premium else None,
                'includes_premiums': has_any_premium,
                'missing_premium_data': missing_premium_products,
                'available_workbooks': list(available_workbooks.keys()) if available_workbooks else []
            }
        except Exception as e:
            logger.error(f"Error in premium comparison: {e}")
            return {
                'success': False,
                'error': str(e)
            }
