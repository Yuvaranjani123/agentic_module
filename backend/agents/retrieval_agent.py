"""
Retrieval Agent - Wraps existing retrieval logic into an agent pattern.
This agent handles document querying, evaluation, and answer generation.
"""
import os
from dotenv import load_dotenv
load_dotenv()

import chromadb
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
import logging
from logs.utils import setup_logging
from evaluation.metrics import RetrievalEvaluator
from config.prompt_config import prompt_config

setup_logging()
logger = logging.getLogger(__name__)


class RetrievalAgent:
    """
    Agent that handles document retrieval and answer generation.
    Uses existing retrieval logic, prompt templates, and evaluation metrics.
    Supports conversation memory for follow-up questions.
    """
    
    def __init__(self, chroma_db_dir: str):
        """
        Initialize the Retrieval Agent.
        
        Args:
            chroma_db_dir: Path to ChromaDB persistence directory
        """
        self.chroma_db_dir = chroma_db_dir
        self.evaluator = RetrievalEvaluator()
        self.conversation_history = []  # Store conversation history
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=chroma_db_dir)
        self.collection = self.client.get_collection("insurance_chunks")
        
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
            openai_api_version=os.getenv("AZURE_OPENAI_CHAT_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            temperature=0.0
        )
        
        logger.info(f"RetrievalAgent initialized with ChromaDB at: {chroma_db_dir}")
    
    def query(self, query_text: str, k: int = 5, doc_type_filter = None, 
              exclude_doc_types = None, evaluate_retrieval: bool = False, conversation_id: str = None):
        """
        Query documents and generate an answer with conversation memory support.
        
        Args:
            query_text: User's question
            k: Number of chunks to retrieve
            doc_type_filter: Filter by document type - string or list (policy, brochure, prospectus, terms)
            exclude_doc_types: List of document types to exclude (e.g., ['premium-calculation'])
            evaluate_retrieval: Whether to evaluate retrieval quality
            conversation_id: Optional conversation ID for memory management
            
        Returns:
            Dictionary with answer, sources, optional evaluation results, and conversation_id
        """
        logger.info(f"Agent querying: '{query_text}' with k={k}, doc_type={doc_type_filter}, exclude={exclude_doc_types}, conv_id={conversation_id}")
        
        # Build conversation context if history exists
        conversation_context = self._build_conversation_context()
        
        # Enhance query with conversation context for better retrieval
        enhanced_query = query_text
        if conversation_context:
            # For retrieval, combine recent context with current query
            enhanced_query = f"{conversation_context}\n\nCurrent question: {query_text}"
            logger.info(f"Enhanced query with conversation context")
        
        # Step 1: Get query embedding (use enhanced query for better context)
        try:
            query_embedding = self.embeddings.embed_query(enhanced_query)
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return {"answer": "Error getting embedding.", "sources": [], "evaluation": None}
        
        # Step 2: Search ChromaDB with filters
        where_filter = {}
        
        # Detect if query is asking for table data
        table_keywords = ['table', 'list', 'show', 'display', 'what are the', 'which tests', 'tests covered']
        is_table_query = any(keyword in query_text.lower() for keyword in table_keywords)
        
        if is_table_query:
            logger.info("Detected table-related query - will retrieve more results and prioritize table data")
            # Increase k for table queries to get full table content
            k = max(k, 15)  # Ensure we get enough results for table reconstruction
        
        # Handle inclusion filter (can be string or list)
        if doc_type_filter:
            if isinstance(doc_type_filter, list):
                # Multiple types to include - use $in operator
                where_filter["doc_type"] = {"$in": doc_type_filter}
                logger.info(f"Applying inclusion filter: doc_type in {doc_type_filter}")
            else:
                # Single type to include
                where_filter["doc_type"] = doc_type_filter
                logger.info(f"Applying inclusion filter: doc_type = '{doc_type_filter}'")
        
        # Handle exclusion filter
        if exclude_doc_types and isinstance(exclude_doc_types, list):
            # Exclude specific types - use $nin operator
            where_filter["doc_type"] = {"$nin": exclude_doc_types}
            logger.info(f"Applying exclusion filter: doc_type not in {exclude_doc_types}")
        
        try:
            search_params = {
                "query_embeddings": [query_embedding],
                "n_results": k
            }
            if where_filter:
                search_params["where"] = where_filter
                
            results = self.collection.query(**search_params)
            
            # If table query and we got results, try to get additional table rows
            if is_table_query and results['documents'] and results['documents'][0]:
                # Check if any results are table-related
                has_table_ref = any(
                    meta.get('type') in ['table_row', 'table_header'] or meta.get('table_file')
                    for meta in results['metadatas'][0]
                )
                
                if has_table_ref:
                    # Find the table file name from results
                    table_files = set()
                    for meta in results['metadatas'][0]:
                        if meta.get('table_file'):
                            table_files.add(meta['table_file'])
                    
                    # Retrieve all rows from identified tables
                    if table_files:
                        logger.info(f"Retrieving complete table data for: {table_files}")
                        for table_file in table_files:
                            table_results = self.collection.query(
                                query_embeddings=[query_embedding],
                                where={"table_file": table_file},
                                n_results=50  # Get all table rows
                            )
                            # Merge with existing results
                            if table_results['documents'] and table_results['documents'][0]:
                                results['documents'][0].extend(table_results['documents'][0])
                                results['metadatas'][0].extend(table_results['metadatas'][0])
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            return {"answer": "Error querying database.", "sources": [], "evaluation": None}
        
        # Step 3: Check if we have results
        if not results['documents'] or not results['documents'][0]:
            logger.info("No relevant documents found.")
            evaluation_results = {"error": "No documents found"} if evaluate_retrieval else None
            return {"answer": "No relevant documents found.", "sources": [], "evaluation": evaluation_results}
        
        # Step 4: Build context and sources
        context_parts = []
        sources = []
        retrieved_docs = []
        
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            context_parts.append(f"[Source {i+1}] {doc}")
            
            source_info = {
                "id": metadata.get("chunk_idx", f"doc_{i}"),
                "content": doc,
                "text": doc,
                "page": metadata.get("page_num"),
                "table": metadata.get("table_file"),
                "row_index": metadata.get("row_idx"),
                "type": metadata.get("type"),
                "chunking_method": metadata.get("chunking_method", "unknown"),
                "chunk_idx": metadata.get("chunk_idx"),
                "metadata": metadata
            }
            sources.append(source_info)
            retrieved_docs.append(source_info)
        
        context = "\n\n".join(context_parts)
        
        # Step 5: Evaluate retrieval if requested
        evaluation_results = None
        if evaluate_retrieval:
            try:
                evaluation_results = self.evaluator.comprehensive_evaluation(
                    query=query_text,
                    retrieved_docs=retrieved_docs,
                    embeddings_client=self.embeddings,
                    k=min(k, len(retrieved_docs))
                )
                logger.info(f"Evaluation: avg_similarity={evaluation_results.get('avg_semantic_similarity', 'N/A'):.3f}")
            except Exception as e:
                logger.error(f"Error during evaluation: {e}")
                evaluation_results = {"error": f"Evaluation failed: {str(e)}"}
        
        # Step 6: Generate answer using existing prompt template with conversation context
        try:
            # Add conversation history to the prompt if it exists
            full_question = query_text
            if conversation_context:
                full_question = f"Previous conversation:\n{conversation_context}\n\nCurrent question: {query_text}"
            
            formatted_prompt = prompt_config.format(
                context=context,
                question=full_question
            )
        except Exception as e:
            logger.error(f"Error formatting prompt: {e}")
            return {"answer": "Error formatting prompt.", "sources": sources, "evaluation": evaluation_results}
        
        # Step 7: Get LLM response
        try:
            response = self.llm.invoke(formatted_prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            logger.info("Answer generated successfully.")
        except Exception as e:
            logger.error(f"Error invoking LLM: {e}")
            answer = "Error generating answer from LLM."
        
        # Step 8: Return complete response and store in conversation history
        result = {"answer": answer, "sources": sources}
        if evaluation_results:
            result["evaluation"] = evaluation_results
        
        # Store this interaction in conversation history
        self._add_to_history(query_text, answer)
        
        # Add conversation ID to response
        if conversation_id:
            result["conversation_id"] = conversation_id
            
        return result
    
    def _build_conversation_context(self, max_history: int = 3):
        """
        Build conversation context from recent history.
        
        Args:
            max_history: Maximum number of recent exchanges to include
            
        Returns:
            Formatted conversation context string
        """
        if not self.conversation_history:
            return ""
        
        # Get recent history (last N exchanges)
        recent_history = self.conversation_history[-max_history:]
        
        context_parts = []
        for i, exchange in enumerate(recent_history, 1):
            context_parts.append(f"Q{i}: {exchange['question']}")
            context_parts.append(f"A{i}: {exchange['answer'][:200]}...")  # Truncate long answers
        
        return "\n".join(context_parts)
    
    def _add_to_history(self, question: str, answer: str):
        """
        Add question-answer pair to conversation history.
        
        Args:
            question: User's question
            answer: Agent's answer
        """
        self.conversation_history.append({
            "question": question,
            "answer": answer,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
        
        # Keep only last 10 exchanges to prevent memory issues
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        logger.info(f"Conversation history size: {len(self.conversation_history)}")
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_history(self):
        """Get current conversation history."""
        return self.conversation_history
