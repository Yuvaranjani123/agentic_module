"""
Document-based Comparison Module

Handles retrieval and comparison of insurance products based on document content.
"""
import logging
import chromadb
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class DocumentComparator:
    """
    Handles document-based comparison of insurance products.
    
    Retrieves relevant chunks from ChromaDB collections for each product
    and provides structured data for LLM-based comparison.
    """
    
    def __init__(self, chroma_base_dir: str, embeddings, llm):
        """
        Initialize document comparator.
        
        Args:
            chroma_base_dir: Base directory containing product databases
            embeddings: Embeddings model for query vectorization
            llm: Language model for generating comparisons
            
        Example:
            >>> comparator = DocumentComparator(
            ...     chroma_base_dir="media/output/chroma_db",
            ...     embeddings=embeddings_model,
            ...     llm=chat_model
            ... )
        """
        self.chroma_base_dir = chroma_base_dir
        self.embeddings = embeddings
        self.llm = llm
        self.available_products = self._detect_products()
        logger.info(f"DocumentComparator initialized with {len(self.available_products)} products")
    
    def _detect_products(self) -> List[str]:
        """
        Detect all available product databases.
        
        Returns:
            List of product names that have valid ChromaDB databases
            
        Example:
            >>> comparator._detect_products()
            ['ActivAssure', 'ActivFit', 'HealthPlus']
        """
        import os
        products = []
        
        if os.path.exists(self.chroma_base_dir):
            for item in os.listdir(self.chroma_base_dir):
                item_path = os.path.join(self.chroma_base_dir, item)
                if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "chroma.sqlite3")):
                    products.append(item)
        
        return products
    
    def get_available_products(self) -> List[str]:
        """
        Get list of available products.
        
        Returns:
            List of product names
            
        Example:
            >>> comparator.get_available_products()
            ['ActivAssure', 'ActivFit']
        """
        return self.available_products
    
    def _get_product_collection(self, product_name: str):
        """
        Get ChromaDB collection for a specific product.
        
        Args:
            product_name: Name of the product
            
        Returns:
            ChromaDB collection object
            
        Example:
            >>> collection = comparator._get_product_collection('ActivAssure')
        """
        import os
        product_db_path = os.path.join(self.chroma_base_dir, product_name)
        client = chromadb.PersistentClient(path=product_db_path)
        return client.get_collection("insurance_chunks")
    
    def retrieve_from_product(self, product_name: str, query: str, k: int = 5) -> List[Dict]:
        """
        Retrieve relevant chunks from a specific product database.
        
        Args:
            product_name: Name of the product database
            query: Comparison query
            k: Number of chunks to retrieve
            
        Returns:
            List of retrieved chunks with metadata
            
        Example:
            >>> chunks = comparator.retrieve_from_product(
            ...     product_name='ActivAssure',
            ...     query='What is the coverage for maternity?',
            ...     k=5
            ... )
            >>> len(chunks)
            5
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
    
    def retrieve_from_multiple_products(
        self, 
        product_names: List[str], 
        query: str, 
        k: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        Retrieve relevant chunks from multiple products.
        
        Args:
            product_names: List of product names
            query: Comparison query
            k: Number of chunks per product
            
        Returns:
            Dictionary mapping product names to their chunks
            
        Example:
            >>> contexts = comparator.retrieve_from_multiple_products(
            ...     product_names=['ActivAssure', 'ActivFit'],
            ...     query='Compare maternity benefits',
            ...     k=5
            ... )
            >>> 'ActivAssure' in contexts
            True
        """
        product_contexts = {}
        
        for product in product_names:
            chunks = self.retrieve_from_product(product, query, k=k)
            product_contexts[product] = chunks
        
        return product_contexts
    
    def retrieve_by_aspects(
        self, 
        product_names: List[str], 
        aspects: List[str], 
        k: int = 5
    ) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Retrieve information for multiple products across multiple aspects.
        
        Args:
            product_names: List of product names
            aspects: List of aspects to compare
            k: Number of chunks per aspect
            
        Returns:
            Nested dictionary: product -> aspect -> chunks
            
        Example:
            >>> data = comparator.retrieve_by_aspects(
            ...     product_names=['ActivAssure', 'ActivFit'],
            ...     aspects=['coverage', 'premium'],
            ...     k=5
            ... )
            >>> data['ActivAssure']['coverage']
            [{'content': '...', 'metadata': {...}}]
        """
        product_data = {}
        
        for product in product_names:
            product_data[product] = {}
            for aspect in aspects:
                query = f"What is the {aspect} for this insurance product?"
                chunks = self.retrieve_from_product(product, query, k=k)
                product_data[product][aspect] = chunks
        
        logger.info(f"Retrieved data for {len(product_names)} products across {len(aspects)} aspects")
        return product_data
    
    def validate_products(self, product_names: List[str]) -> tuple[List[str], List[str]]:
        """
        Validate that products exist in the database.
        
        Args:
            product_names: List of product names to validate
            
        Returns:
            Tuple of (valid_products, invalid_products)
            
        Example:
            >>> valid, invalid = comparator.validate_products(['ActivAssure', 'Unknown'])
            >>> print(valid, invalid)
            ['ActivAssure'] ['Unknown']
        """
        valid = [p for p in product_names if p in self.available_products]
        invalid = [p for p in product_names if p not in self.available_products]
        
        return valid, invalid
