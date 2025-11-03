import os
from dotenv import load_dotenv
load_dotenv()  # load AZURE_OPENAI_* variables
import chromadb
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from langchain_openai import AzureOpenAIEmbeddings
from langchain_openai import AzureChatOpenAI
import logging
from logs.utils import setup_logging
from evaluation.metrics import RetrievalEvaluator
from typing import List, Dict, Any

setup_logging()
logger = logging.getLogger(__name__)

# Import our simple prompt configuration
from config.prompt_config import prompt_config

# Initialize evaluation system
evaluator = RetrievalEvaluator()

# ---------------------------
# Direct ChromaDB + LLM Query
# ---------------------------
def query_document_internal(
    collection: Any, 
    embedding_model: AzureOpenAIEmbeddings, 
    query: str, 
    k: int = 5, 
    doc_type_filter: str = None, 
    evaluate_retrieval: bool = False
) -> Dict[str, Any]:
    """
    Enhanced query function with document domain filtering and evaluation.
    
    Performs semantic search on ChromaDB collection using Azure OpenAI embeddings,
    optionally filters by document type, and evaluates retrieval quality.
    
    Args:
        collection: ChromaDB collection instance to query.
        embedding_model: Azure OpenAI embeddings model for query vectorization.
        query: User's natural language question or search query.
        k: Number of top results to retrieve (default: 5).
        doc_type_filter: Optional document type filter ('policy', 'brochure', 'prospectus', 'terms').
        evaluate_retrieval: If True, evaluates retrieval quality using RetrievalEvaluator.
        
    Returns:
        dict: Dictionary containing:
            - answer (str): Generated answer from LLM or error message
            - sources (List[Dict]): Retrieved document chunks with metadata
            - evaluation (Dict): Retrieval evaluation metrics if evaluate_retrieval=True
    """
    logger.info(f"Querying ChromaDB for: '{query}' with top {k} results, doc_type_filter: {doc_type_filter}")
    
    # Get query embedding
    try:
        query_embedding = embedding_model.embed_query(query)
    except Exception as e:
        logger.error(f"Error getting embedding for query: {e}")
        return {"answer": "Error getting embedding.", "sources": [], "evaluation": None}
    
    # Prepare filters for document domain integration
    where_filter = {}
    if doc_type_filter:
        # Filter by document type (policy, brochure, etc.)
        if doc_type_filter in ['policy', 'brochure', 'prospectus', 'terms']:
            where_filter["doc_type"] = doc_type_filter
            logger.info(f"Applying document type filter: doc_type = '{doc_type_filter}'")
    
    # Search ChromaDB with domain filtering
    try:
        search_params = {
            "query_embeddings": [query_embedding],
            "n_results": k
        }
        if where_filter:
            search_params["where"] = where_filter
            
        results = collection.query(**search_params)
    except Exception as e:
        logger.error(f"Error querying ChromaDB: {e}")
        return {"answer": "Error querying database.", "sources": [], "evaluation": None}
    # Build context from results
    if not results['documents'] or not results['documents'][0]:
        logger.info("No relevant documents found for query.")
        evaluation_results = None
        if evaluate_retrieval:
            evaluation_results = {"error": "No documents found for evaluation"}
        return {"answer": "No relevant documents found.", "sources": [], "evaluation": evaluation_results}
        
    context_parts = []
    sources = []
    retrieved_docs = []
    
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        context_parts.append(f"[Source {i+1}] {doc}")
        
        source_info = {
            "id": metadata.get("chunk_idx", f"doc_{i}"),
            "content": doc,
            "text": doc,  # For evaluation
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
    
    # Perform evaluation if requested
    evaluation_results = None
    if evaluate_retrieval:
        try:
            evaluation_results = evaluator.comprehensive_evaluation(
                query=query,
                retrieved_docs=retrieved_docs,
                embeddings_client=embedding_model,
                k=min(k, len(retrieved_docs))
            )
            logger.info(f"Retrieval evaluation completed: avg_similarity={evaluation_results.get('avg_semantic_similarity', 'N/A'):.3f}")
        except Exception as e:
            logger.error(f"Error during evaluation: {e}")
            evaluation_results = {"error": f"Evaluation failed: {str(e)}"}
    # Initialize LLM
    try:
        llm = AzureChatOpenAI(
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
            openai_api_version=os.getenv("AZURE_OPENAI_CHAT_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            temperature=0.0
        )
    except Exception as e:
        logger.error(f"Error initializing AzureChatOpenAI: {e}")
        return {"answer": "Error initializing LLM.", "sources": sources}
    # Use our configured prompt template
    try:
        formatted_prompt = prompt_config.format(
            context=context,
            question=query
        )
    except Exception as e:
        logger.error(f"Error formatting prompt: {e}")
        return {"answer": "Error formatting prompt.", "sources": sources}
    # Get LLM response
    try:
        response = llm.invoke(formatted_prompt)
        answer = response.content if hasattr(response, 'content') else str(response)
        logger.info("LLM response generated successfully.")
    except Exception as e:
        logger.error(f"Error invoking LLM: {e}")
        answer = "Error generating answer from LLM."
    response = {"answer": answer, "sources": sources}
    if evaluation_results:
        response["evaluation"] = evaluation_results
    return response

@api_view(['POST'])
def query_document(request):
    """Enhanced API endpoint to query the document database with domain filtering and evaluation."""
    try:
        query_text = request.data.get("query")
        chroma_db_dir = request.data.get("chroma_db_dir")
        k = request.data.get("k", 5)
        doc_type_filter = request.data.get("doc_type")  # New: document type filtering
        evaluate_retrieval = request.data.get("evaluate", False)  # New: evaluation flag
        
        logger.info(f"Received query_document API call: query='{query_text}', chroma_db_dir='{chroma_db_dir}', k={k}, doc_type={doc_type_filter}, evaluate={evaluate_retrieval}")
        if not query_text:
            logger.warning("query_document: 'query' is required.")
            return Response({"error": "query is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not chroma_db_dir:
            logger.warning("query_document: 'chroma_db_dir' is required.")
            return Response({"error": "chroma_db_dir is required"}, status=status.HTTP_400_BAD_REQUEST)
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path=chroma_db_dir)
        collection = client.get_collection("insurance_chunks")
        # Initialize embeddings
        embeddings = AzureOpenAIEmbeddings(
            deployment=os.getenv("AZURE_OPENAI_TEXT_DEPLOYMENT_EMBEDDINGS"),
            openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
            openai_api_version=os.getenv("AZURE_OPENAI_TEXT_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        # Perform query with enhanced parameters
        result = query_document_internal(
            collection=collection, 
            embedding_model=embeddings, 
            query=query_text, 
            k=k,
            doc_type_filter=doc_type_filter,
            evaluate_retrieval=evaluate_retrieval
        )
        logger.info("Enhanced query processed and response returned.")
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in query_document API: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def evaluation_summary(request):
    """API endpoint to get evaluation summary and statistics."""
    try:
        summary = evaluator.get_evaluation_summary()
        logger.info("Evaluation summary retrieved successfully")
        return Response(summary, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error getting evaluation summary: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @api_view(['GET'])
# def evaluation_summary(request):
#     """API endpoint to get evaluation summary statistics."""
#     try:
#         summary = evaluator.get_evaluation_summary()
#         logger.info("Evaluation summary retrieved successfully.")
#         return Response(summary, status=status.HTTP_200_OK)
#     except Exception as e:
#         logger.error(f"Error getting evaluation summary: {e}")
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------
# Main for CLI testing
# ---------------------------
# def main():
#     persist_dir = r"C:\repo\certification\lessons\chunk_manual_rag\data\output\chroma_db\ActivAssure"  
#     client = chromadb.PersistentClient(path=persist_dir)

#     # Use the same collection name as chunker_embedder.py
#     collection = client.get_collection("insurance_chunks")

#     embeddings = AzureOpenAIEmbeddings(
#         deployment=os.getenv("AZURE_OPENAI_TEXT_DEPLOYMENT_EMBEDDINGS"),
#         openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
#         openai_api_version=os.getenv("AZURE_OPENAI_TEXT_VERSION"),
#         azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
#     )

#     query = input("Enter your query: ")
#     result = query_document_internal(collection, embeddings, query)

#     print("\nAnswer:", result["answer"])
#     print("\nSources:")
#     for s in result["sources"]:
#         page_info = f"Page {s['page']}" if s['page'] else "No page"
#         table_info = f"Table: {s['table']}" if s['table'] else "Text chunk"
#         row_info = f"Row: {s['row_index']}" if s['row_index'] is not None else ""
#         method_info = f"[{s['chunking_method'].upper()}]" if s.get('chunking_method') else ""
        
#         print(f"- {page_info} | {table_info} {row_info} | Type: {s['type']} {method_info}")
#         print(f"  Chunk ID: {s['chunk_idx']}")
#         print(f"  Snippet: {s['content'][:200]}...\n")

# if __name__ == "__main__":
#     main()
