"""
Document Retriever

Handles ChromaDB operations and document retrieval with filtering.
"""
import chromadb
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class DocumentRetriever:
    """
    Manages document retrieval from ChromaDB with filtering support.
    
    Handles embedding queries, filtering by document type, and
    retrieving relevant chunks from the vector database.
    """
    
    def __init__(self, chroma_db_dir: str, embeddings):
        """
        Initialize document retriever.
        
        Args:
            chroma_db_dir: Path to ChromaDB persistence directory
            embeddings: Embeddings model for query vectorization
            
        Example:
            >>> retriever = DocumentRetriever(
            ...     chroma_db_dir="/path/to/chroma",
            ...     embeddings=embeddings_model
            ... )
        """
        self.chroma_db_dir = chroma_db_dir
        self.embeddings = embeddings
        self._client_cache = {}  # Cache clients for different products
        
        # Initialize default ChromaDB
        self._initialize_client(chroma_db_dir)
    
    def _initialize_client(self, chroma_db_dir: str):
        """Initialize ChromaDB client and collection for a specific directory."""
        if chroma_db_dir in self._client_cache:
            self.client = self._client_cache[chroma_db_dir]['client']
            self.collection = self._client_cache[chroma_db_dir]['collection']
            logger.info(f"Using cached ChromaDB client for: {chroma_db_dir}")
            return
        
        # Create new client
        self.client = chromadb.PersistentClient(path=chroma_db_dir)
        
        # Try to get existing collection (DO NOT create empty one)
        try:
            self.collection = self.client.get_collection("insurance_chunks")
            
            # Check if collection has documents
            count = self.collection.count()
            if count == 0:
                logger.warning(f"Collection 'insurance_chunks' is EMPTY at {chroma_db_dir}. Run ingestion first!")
                self.collection = None
            else:
                logger.info(f"DocumentRetriever using collection with {count} documents at: {chroma_db_dir}")
        except Exception as e:
            logger.error(f"Collection 'insurance_chunks' not found at {chroma_db_dir}: {e}")
            logger.error(f"Product database missing! Run ingestion for this product first.")
            self.collection = None
        
        # Cache the client and collection
        self._client_cache[chroma_db_dir] = {
            'client': self.client,
            'collection': self.collection
        }
        self.chroma_db_dir = chroma_db_dir
    
    def set_chroma_db_dir(self, chroma_db_dir: str):
        """
        Switch to a different ChromaDB directory (for different products).
        
        Args:
            chroma_db_dir: New ChromaDB directory path
            
        Example:
            >>> retriever.set_chroma_db_dir("media/output/chroma_db/ActivFit")
        """
        if chroma_db_dir != self.chroma_db_dir:
            logger.info(f"Switching ChromaDB from {self.chroma_db_dir} to {chroma_db_dir}")
            self._initialize_client(chroma_db_dir)
    
    def retrieve(
        self, 
        query_text: str, 
        k: int = 5,
        doc_type_filter: Optional[List[str]] = None,
        exclude_doc_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Retrieve relevant documents from ChromaDB.
        
        Args:
            query_text: Query string
            k: Number of documents to retrieve
            doc_type_filter: Include only these document types
            exclude_doc_types: Exclude these document types
            
        Returns:
            List of retrieved documents with metadata
            
        Example:
            >>> docs = retriever.retrieve(
            ...     query_text="What is maternity coverage?",
            ...     k=5,
            ...     doc_type_filter=["policy"]
            ... )
            >>> len(docs)
            5
        """
        try:
            # Check if collection is available
            if self.collection is None:
                product_name = self.chroma_db_dir.split('/')[-1] if '/' in self.chroma_db_dir else self.chroma_db_dir.split('\\')[-1]
                error_msg = f"No documents available for '{product_name}'. Please run ingestion for this product first."
                logger.error(error_msg)
                return []
            
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query_text)
            
            # Build filter if needed
            where_filter = self._build_filter(doc_type_filter, exclude_doc_types)
            
            # Query ChromaDB
            if where_filter:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=k,
                    where=where_filter
                )
            else:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=k
                )
            
            # Format results
            documents = []
            if results and results['documents'] and len(results['documents']) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    documents.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None
                    })
            
            logger.info(f"Retrieved {len(documents)} documents for query: {query_text[:50]}...")
            return documents
        
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def _build_filter(
        self, 
        doc_type_filter: Optional[List[str]], 
        exclude_doc_types: Optional[List[str]]
    ) -> Optional[Dict]:
        """
        Build ChromaDB where filter for document types.
        
        Args:
            doc_type_filter: Include only these types
            exclude_doc_types: Exclude these types
            
        Returns:
            Filter dict or None
            
        Example:
            >>> filter = retriever._build_filter(
            ...     doc_type_filter=["policy", "brochure"],
            ...     exclude_doc_types=None
            ... )
            >>> filter
            {'doc_type': {'$in': ['policy', 'brochure']}}
        """
        if doc_type_filter:
            return {"doc_type": {"$in": doc_type_filter}}
        elif exclude_doc_types:
            return {"doc_type": {"$nin": exclude_doc_types}}
        return None
    
    def get_collection_size(self) -> int:
        """
        Get total number of documents in collection.
        
        Returns:
            Document count
            
        Example:
            >>> retriever.get_collection_size()
            150
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error getting collection size: {e}")
            return 0
    
    def get_unique_doc_types(self) -> List[str]:
        """
        Get list of unique document types in collection.
        
        Returns:
            List of document type strings
            
        Example:
            >>> retriever.get_unique_doc_types()
            ['policy', 'brochure', 'prospectus']
        """
        try:
            # Get all metadatas (this might be slow for large collections)
            # Consider caching or alternative approach for production
            results = self.collection.get(
                limit=1000,  # Limit to avoid memory issues
                include=["metadatas"]
            )
            
            doc_types = set()
            if results and results['metadatas']:
                for metadata in results['metadatas']:
                    if 'doc_type' in metadata:
                        doc_types.add(metadata['doc_type'])
            
            return sorted(list(doc_types))
        except Exception as e:
            logger.error(f"Error getting unique doc types: {e}")
            return []
