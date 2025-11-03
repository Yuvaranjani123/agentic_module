"""
Retrieval Agent - Orchestrates document retrieval and answer generation.

Coordinates modular components for conversation memory, document retrieval,
and query enhancement to provide intelligent Q&A capabilities.
"""
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
import logging
from logs.utils import setup_logging
from evaluation.metrics import RetrievalEvaluator
from config.prompt_config import prompt_config
from agents.retrievers import ConversationMemory, DocumentRetriever, QueryEnhancer

setup_logging()
logger = logging.getLogger(__name__)


class RetrievalAgent:
    """
    Orchestrator for document retrieval and answer generation.
    
    Coordinates conversation memory, document retrieval, and query
    enhancement to provide intelligent responses with conversation context.
    """
    
    def __init__(self, chroma_db_dir: str):
        """
        Initialize the Retrieval Agent with modular components.
        
        Args:
            chroma_db_dir: Path to ChromaDB persistence directory
        """
        self.chroma_db_dir = chroma_db_dir
        self.evaluator = RetrievalEvaluator()
        
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
        
        # Initialize modular components
        self.conversation = ConversationMemory(max_history=10)
        self.retriever = DocumentRetriever(chroma_db_dir, self.embeddings)
        self.query_enhancer = QueryEnhancer()
        
        logger.info(f"RetrievalAgent initialized with modular components")
    
    def query(self, query_text: str, k: int = 5, doc_type_filter=None, 
              exclude_doc_types=None, evaluate_retrieval: bool = False, 
              conversation_id: str = None):
        """
        Query documents and generate an answer with conversation context.
        
        Args:
            query_text: User's question
            k: Number of chunks to retrieve
            doc_type_filter: Filter by document type
            exclude_doc_types: Exclude document types
            evaluate_retrieval: Whether to evaluate retrieval quality
            conversation_id: Optional conversation ID
            
        Returns:
            Dictionary with answer, sources, evaluation, and conversation_id
        """
        logger.info(f"Query: '{query_text[:50]}...' k={k}, conv_id={conversation_id}")
        
        # Check for premium calculation intent
        intent = self.query_enhancer.detect_premium_intent(query_text)
        if intent['is_premium_query']:
            logger.info("Premium calculation intent detected - routing")
            return self._route_to_premium_calculator(conversation_id)
        
        # Build conversation context if relevant
        conversation_context = self.conversation.build_context_if_relevant(query_text)
        
        # Enhance query with context
        enhanced_query = self.query_enhancer.enhance_query(
            query_text, 
            conversation_context
        )
        
        # Detect table queries and adjust k
        k = self._adjust_k_for_table_queries(query_text, k)
        
        # Retrieve documents
        documents = self.retriever.retrieve(
            query_text=enhanced_query,
            k=k,
            doc_type_filter=doc_type_filter,
            exclude_doc_types=exclude_doc_types
        )
        
        if not documents:
            logger.info("No relevant documents found")
            return self._no_results_response(evaluate_retrieval, conversation_id)
        
        # Build context and sources
        context, sources = self._build_context_and_sources(documents)
        
        # Evaluate retrieval if requested
        evaluation_results = None
        if evaluate_retrieval:
            evaluation_results = self._evaluate_retrieval(
                query_text, sources, k
            )
        
        # Generate answer
        answer = self._generate_answer(query_text, context, conversation_context)
        
        # Store in conversation history
        self.conversation.add_turn(query_text, answer)
        
        # Build response
        result = {
            "answer": answer,
            "sources": sources,
            "evaluation": evaluation_results,
            "conversation_id": conversation_id
        }
        
        return result
    
    def _route_to_premium_calculator(self, conversation_id: str = None):
        """Route premium calculation requests to calculator agent."""
        return {
            "answer": "I've detected this is a premium calculation request. "
                     "Please use the premium calculator endpoints:\n\n"
                     "• `/agents/premium/individual/` for individual policies\n"
                     "• `/agents/premium/family-floater/` for family floater policies\n"
                     "• `/agents/premium/calculate/` for smart routing\n\n"
                     "Provide:\n"
                     "- Policy type (individual or family_floater)\n"
                     "- Member ages\n"
                     "- Sum insured (e.g., '5L' or 500000)\n\n"
                     "Example: For 2 adults aged 35 and 40 with ₹5L cover, "
                     "POST to `/agents/premium/individual/` with:\n"
                     '```json\n{"members": [{"age": 35}, {"age": 40}], '
                     '"sum_insured": "5L"}\n```',
            "sources": [],
            "conversation_id": conversation_id,
            "agent_type": "premium_calculator_router",
            "evaluation": None
        }
    
    def _adjust_k_for_table_queries(self, query_text: str, k: int) -> int:
        """Increase k for table-related queries."""
        table_keywords = [
            'table', 'list', 'show', 'display', 
            'what are the', 'which tests', 'tests covered'
        ]
        is_table_query = any(kw in query_text.lower() for kw in table_keywords)
        
        if is_table_query:
            logger.info("Table query detected - increasing k")
            return max(k, 15)
        
        return k
    
    def _no_results_response(self, evaluate_retrieval: bool, conversation_id: str):
        """Build response for when no documents are found."""
        evaluation_results = (
            {"error": "No documents found"} if evaluate_retrieval else None
        )
        return {
            "answer": "No relevant documents found.",
            "sources": [],
            "evaluation": evaluation_results,
            "conversation_id": conversation_id
        }
    
    def _build_context_and_sources(self, documents: list):
        """Build context string and sources list from retrieved documents."""
        context_parts = []
        sources = []
        
        for i, doc in enumerate(documents):
            context_parts.append(f"[Source {i+1}] {doc['content']}")
            
            metadata = doc.get('metadata', {})
            source_info = {
                "id": metadata.get("chunk_idx", f"doc_{i}"),
                "content": doc['content'],
                "text": doc['content'],
                "page": metadata.get("page_num"),
                "table": metadata.get("table_file"),
                "row_index": metadata.get("row_idx"),
                "type": metadata.get("type"),
                "chunking_method": metadata.get("chunking_method", "unknown"),
                "chunk_idx": metadata.get("chunk_idx"),
                "metadata": metadata
            }
            sources.append(source_info)
        
        context = "\n\n".join(context_parts)
        return context, sources
    
    def _evaluate_retrieval(self, query: str, sources: list, k: int):
        """Evaluate retrieval quality."""
        try:
            evaluation_results = self.evaluator.comprehensive_evaluation(
                query=query,
                retrieved_docs=sources,
                embeddings_client=self.embeddings,
                k=min(k, len(sources))
            )
            avg_sim = evaluation_results.get('avg_semantic_similarity', 'N/A')
            logger.info(f"Evaluation: avg_similarity={avg_sim:.3f}")
            return evaluation_results
        except Exception as e:
            logger.error(f"Error during evaluation: {e}")
            return {"error": f"Evaluation failed: {str(e)}"}
    
    def _generate_answer(self, query: str, context: str, 
                        conversation_context: str = None) -> str:
        """Generate answer using LLM."""
        try:
            # Build full question with conversation context if available
            full_question = query
            if conversation_context:
                full_question = (
                    f"Previous conversation:\n{conversation_context}\n\n"
                    f"Current question: {query}"
                )
            
            # Format prompt
            formatted_prompt = prompt_config.format(
                context=context,
                question=full_question
            )
            
            # Get LLM response
            response = self.llm.invoke(formatted_prompt)
            answer = (
                response.content if hasattr(response, 'content') 
                else str(response)
            )
            
            logger.info("Answer generated successfully")
            return answer
        
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "Error generating answer from LLM."
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation.clear()
        logger.info("Conversation history cleared")
    
    def get_history(self):
        """Get current conversation history."""
        return self.conversation.get_history()

