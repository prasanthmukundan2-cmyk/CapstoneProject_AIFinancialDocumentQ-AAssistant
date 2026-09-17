"""
Simple Document Q&A - No Rate Limit Issues
Uses single LLM call instead of 6 parallel agents
"""

import logging
import time
from src.agents_fixed import get_llm, _extract_text
from src.retry_utils import invoke_with_retry

logger = logging.getLogger(__name__)


def answer_document_question(document_text: str, document_name: str, question: str) -> dict:
    """
    Answer a question about a document using a single LLM call.

    This avoids rate limits by:
    - Using 1 API call instead of 6
    - No parallel execution
    - Simple, fast, reliable

    Args:
        document_text: Full text from uploaded document
        document_name: Name of the document
        question: User's question

    Returns:
        dict with answer, sources, agent name, and time
    """

    start_time = time.time()

    try:
        logger.info(f"Answering question about {document_name}")

        # Limit text to avoid token limits
        max_chars = 4000
        if len(document_text) > max_chars:
            text_preview = document_text[:max_chars] + "\n... [Document truncated for processing]"
        else:
            text_preview = document_text

        # Create prompt that asks the LLM to answer directly
        prompt = f"""You are a financial document analyst.

DOCUMENT: {document_name}

CONTENT:
{text_preview}

USER QUESTION:
{question}

INSTRUCTIONS:
1. Answer based ONLY on the document content
2. Be specific with numbers, dates, and facts
3. If information is not in the document, say "Not mentioned in document"
4. Quote relevant sections when possible
5. Keep answer concise but complete

ANSWER:
"""

        logger.info(f"Making API call to answer question about {document_name}")

        # Single API call
        response = invoke_with_retry(get_llm(), prompt, max_retries=1)
        answer = _extract_text(response.content)

        execution_time = time.time() - start_time

        logger.info(f"Question answered in {execution_time:.2f} seconds")

        return {
            "answer": answer,
            "sources": [document_name],
            "agent": "simple_document_qa",
            "time": execution_time,
            "cached": False,
        }

    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        raise


def compare_documents(documents: dict, question: str) -> dict:
    """
    Compare multiple documents with a single question.

    Args:
        documents: Dict of {doc_name: doc_text}
        question: Comparison question

    Returns:
        dict with answer and sources
    """

    start_time = time.time()

    try:
        logger.info(f"Comparing {len(documents)} documents")

        # Build document context
        doc_context = ""
        doc_names = []

        for doc_name, doc_text in documents.items():
            doc_names.append(doc_name)
            max_chars = 2000  # Less text when comparing multiple

            if len(doc_text) > max_chars:
                text_preview = doc_text[:max_chars] + "\n... [truncated]"
            else:
                text_preview = doc_text

            doc_context += f"\n\n--- DOCUMENT: {doc_name} ---\n{text_preview}"

        # Create comparison prompt
        prompt = f"""You are a financial document analyst.

Your task is to compare these documents and answer the question.

DOCUMENTS:{doc_context}

COMPARISON QUESTION:
{question}

INSTRUCTIONS:
1. Compare information across documents
2. Highlight similarities and differences
3. Use specific numbers and facts
4. Show which document had what information
5. Provide clear comparison summary

ANSWER:
"""

        logger.info(f"Making API call to compare {len(documents)} documents")

        # Single API call for comparison
        response = invoke_with_retry(get_llm(), prompt, max_retries=1)
        answer = _extract_text(response.content)

        execution_time = time.time() - start_time

        logger.info(f"Comparison completed in {execution_time:.2f} seconds")

        return {
            "answer": answer,
            "sources": doc_names,
            "agent": "document_comparison",
            "time": execution_time,
            "cached": False,
        }

    except Exception as e:
        logger.error(f"Error comparing documents: {str(e)}")
        raise
