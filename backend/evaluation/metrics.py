"""
Retrieval Evaluation Metrics for Insurance RAG System

This module provides evaluation metrics to assess the quality of retrieval
and generation in the RAG system, addressing feedback about evaluation capabilities.
"""

import numpy as np
from typing import List, Dict, Any, Tuple
import logging
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import re

logger = logging.getLogger(__name__)

class RetrievalEvaluator:
    """Evaluate retrieval quality and RAG system performance."""
    
    def __init__(self):
        self.evaluation_history = []
    
    def calculate_retrieval_precision_at_k(self, retrieved_docs: List[Dict], 
                                         relevant_doc_ids: List[str], k: int = 5) -> float:
        """
        Calculate Precision@K for retrieved documents.
        
        Args:
            retrieved_docs: List of retrieved documents with metadata
            relevant_doc_ids: List of known relevant document IDs
            k: Number of top documents to consider
            
        Returns:
            Precision@K score (0.0 to 1.0)
        """
        if not retrieved_docs or not relevant_doc_ids:
            return 0.0
        
        top_k_docs = retrieved_docs[:k]
        retrieved_ids = [doc.get('id', doc.get('metadata', {}).get('chunk_idx', '')) 
                        for doc in top_k_docs]
        
        relevant_in_top_k = sum(1 for doc_id in retrieved_ids if doc_id in relevant_doc_ids)
        precision_at_k = relevant_in_top_k / min(k, len(retrieved_docs))
        
        logger.info(f"Precision@{k}: {precision_at_k:.3f} ({relevant_in_top_k}/{min(k, len(retrieved_docs))})")
        return precision_at_k
    
    def calculate_retrieval_recall_at_k(self, retrieved_docs: List[Dict], 
                                      relevant_doc_ids: List[str], k: int = 5) -> float:
        """
        Calculate Recall@K for retrieved documents.
        
        Args:
            retrieved_docs: List of retrieved documents with metadata
            relevant_doc_ids: List of known relevant document IDs
            k: Number of top documents to consider
            
        Returns:
            Recall@K score (0.0 to 1.0)
        """
        if not retrieved_docs or not relevant_doc_ids:
            return 0.0
        
        top_k_docs = retrieved_docs[:k]
        retrieved_ids = [doc.get('id', doc.get('metadata', {}).get('chunk_idx', '')) 
                        for doc in top_k_docs]
        
        relevant_in_top_k = sum(1 for doc_id in retrieved_ids if doc_id in relevant_doc_ids)
        recall_at_k = relevant_in_top_k / len(relevant_doc_ids)
        
        logger.info(f"Recall@{k}: {recall_at_k:.3f} ({relevant_in_top_k}/{len(relevant_doc_ids)})")
        return recall_at_k
    
    def calculate_mrr(self, queries_and_relevance: List[Tuple[str, List[str], List[Dict]]]) -> float:
        """
        Calculate Mean Reciprocal Rank (MRR) across multiple queries.
        
        Args:
            queries_and_relevance: List of (query, relevant_doc_ids, retrieved_docs) tuples
            
        Returns:
            MRR score (0.0 to 1.0)
        """
        if not queries_and_relevance:
            return 0.0
        
        reciprocal_ranks = []
        
        for query, relevant_ids, retrieved_docs in queries_and_relevance:
            retrieved_ids = [doc.get('id', doc.get('metadata', {}).get('chunk_idx', '')) 
                           for doc in retrieved_docs]
            
            # Find rank of first relevant document
            first_relevant_rank = None
            for i, doc_id in enumerate(retrieved_ids, 1):
                if doc_id in relevant_ids:
                    first_relevant_rank = i
                    break
            
            if first_relevant_rank:
                reciprocal_ranks.append(1.0 / first_relevant_rank)
            else:
                reciprocal_ranks.append(0.0)
        
        mrr = np.mean(reciprocal_ranks)
        logger.info(f"Mean Reciprocal Rank (MRR): {mrr:.3f}")
        return mrr
    
    def evaluate_semantic_similarity(self, query: str, retrieved_texts: List[str], 
                                   embeddings_client=None) -> List[float]:
        """
        Evaluate semantic similarity between query and retrieved documents.
        
        Args:
            query: User query
            retrieved_texts: List of retrieved document texts
            embeddings_client: Client for generating embeddings
            
        Returns:
            List of similarity scores
        """
        if not embeddings_client or not retrieved_texts:
            return []
        
        try:
            # Get embeddings
            query_embedding = embeddings_client.embed_query(query)
            doc_embeddings = [embeddings_client.embed_query(text) for text in retrieved_texts]
            
            # Calculate cosine similarities
            similarities = []
            for doc_emb in doc_embeddings:
                sim = cosine_similarity([query_embedding], [doc_emb])[0][0]
                similarities.append(float(sim))
            
            avg_similarity = np.mean(similarities)
            logger.info(f"Average semantic similarity: {avg_similarity:.3f}")
            return similarities
        
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return []
    
    def evaluate_coverage(self, query: str, retrieved_texts: List[str]) -> Dict[str, float]:
        """
        Evaluate how well retrieved documents cover the query terms.
        
        Args:
            query: User query
            retrieved_texts: List of retrieved document texts
            
        Returns:
            Dictionary with coverage metrics
        """
        if not query or not retrieved_texts:
            return {"term_coverage": 0.0, "query_coverage": 0.0}
        
        # Extract key terms from query (simple approach)
        query_terms = set(re.findall(r'\b\w+\b', query.lower()))
        query_terms = {term for term in query_terms if len(term) > 2}  # Filter short words
        
        if not query_terms:
            return {"term_coverage": 0.0, "query_coverage": 0.0}
        
        # Check coverage across all retrieved documents
        all_retrieved_text = ' '.join(retrieved_texts).lower()
        covered_terms = {term for term in query_terms if term in all_retrieved_text}
        
        term_coverage = len(covered_terms) / len(query_terms)
        
        # Calculate per-document query coverage
        doc_coverages = []
        for text in retrieved_texts:
            text_lower = text.lower()
            doc_covered = {term for term in query_terms if term in text_lower}
            doc_coverage = len(doc_covered) / len(query_terms)
            doc_coverages.append(doc_coverage)
        
        avg_doc_coverage = np.mean(doc_coverages) if doc_coverages else 0.0
        
        coverage_metrics = {
            "term_coverage": term_coverage,
            "query_coverage": avg_doc_coverage,
            "covered_terms": list(covered_terms),
            "total_terms": len(query_terms)
        }
        
        logger.info(f"Term coverage: {term_coverage:.3f}, Avg doc coverage: {avg_doc_coverage:.3f}")
        return coverage_metrics
    
    def evaluate_diversity(self, retrieved_texts: List[str]) -> float:
        """
        Evaluate diversity of retrieved documents to avoid redundancy.
        
        Args:
            retrieved_texts: List of retrieved document texts
            
        Returns:
            Diversity score (0.0 to 1.0, higher is more diverse)
        """
        if len(retrieved_texts) < 2:
            return 1.0
        
        # Simple diversity metric based on unique n-grams
        all_bigrams = []
        for text in retrieved_texts:
            words = re.findall(r'\b\w+\b', text.lower())
            bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words)-1)]
            all_bigrams.extend(bigrams)
        
        if not all_bigrams:
            return 0.0
        
        unique_bigrams = len(set(all_bigrams))
        total_bigrams = len(all_bigrams)
        diversity = unique_bigrams / total_bigrams if total_bigrams > 0 else 0.0
        
        logger.info(f"Document diversity: {diversity:.3f}")
        return diversity
    
    def comprehensive_evaluation(self, query: str, retrieved_docs: List[Dict], 
                               relevant_doc_ids: List[str] = None,
                               embeddings_client=None, k: int = 5) -> Dict[str, Any]:
        """
        Perform comprehensive evaluation of retrieval quality.
        
        Args:
            query: User query
            retrieved_docs: List of retrieved documents
            relevant_doc_ids: Optional list of known relevant document IDs
            embeddings_client: Optional embeddings client for semantic similarity
            k: Number of top documents for precision/recall calculation
            
        Returns:
            Dictionary with all evaluation metrics
        """
        retrieved_texts = [doc.get('text', '') for doc in retrieved_docs]
        
        evaluation_results = {
            "query": query,
            "num_retrieved": len(retrieved_docs),
            "timestamp": np.datetime64('now').item().isoformat()
        }
        
        # Coverage evaluation
        coverage_metrics = self.evaluate_coverage(query, retrieved_texts)
        evaluation_results.update(coverage_metrics)
        
        # Diversity evaluation
        diversity_score = self.evaluate_diversity(retrieved_texts)
        evaluation_results["diversity"] = diversity_score
        
        # Semantic similarity (if embeddings client available)
        if embeddings_client:
            similarities = self.evaluate_semantic_similarity(query, retrieved_texts, embeddings_client)
            if similarities:
                evaluation_results["semantic_similarities"] = similarities
                evaluation_results["avg_semantic_similarity"] = np.mean(similarities)
                evaluation_results["min_semantic_similarity"] = np.min(similarities)
                evaluation_results["max_semantic_similarity"] = np.max(similarities)
        
        # Precision/Recall (if ground truth available)
        if relevant_doc_ids:
            precision_at_k = self.calculate_retrieval_precision_at_k(retrieved_docs, relevant_doc_ids, k)
            recall_at_k = self.calculate_retrieval_recall_at_k(retrieved_docs, relevant_doc_ids, k)
            
            evaluation_results[f"precision_at_{k}"] = precision_at_k
            evaluation_results[f"recall_at_{k}"] = recall_at_k
            
            # F1 score
            if precision_at_k + recall_at_k > 0:
                f1_score = 2 * (precision_at_k * recall_at_k) / (precision_at_k + recall_at_k)
                evaluation_results[f"f1_at_{k}"] = f1_score
        
        # Store evaluation history
        self.evaluation_history.append(evaluation_results)
        
        logger.info(f"Comprehensive evaluation completed for query: '{query[:50]}...'")
        return evaluation_results
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get summary statistics from evaluation history."""
        if not self.evaluation_history:
            return {"message": "No evaluations performed yet"}
        
        # Calculate average metrics
        metrics = ["term_coverage", "query_coverage", "diversity"]
        summary = {"total_evaluations": len(self.evaluation_history)}
        
        for metric in metrics:
            values = [eval_result.get(metric, 0) for eval_result in self.evaluation_history 
                     if metric in eval_result]
            if values:
                summary[f"avg_{metric}"] = np.mean(values)
                summary[f"std_{metric}"] = np.std(values)
        
        return summary