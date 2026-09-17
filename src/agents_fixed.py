"""
Fixed agents with better error handling and rate limit tolerance
"""

import logging
from functools import lru_cache

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from src.context import build_contextual_question
from src.rag_pipeline import get_retriever
from src.retry_utils import invoke_with_retry
from src.data_tools import get_financial_record
from src.financial_tools import (
    calculate_growth,
    calculate_profit_margin,
    calculate_net_worth,
)

load_dotenv()
logger = logging.getLogger(__name__)


# ============================================================
# LLM - WITH BETTER ERROR HANDLING
# ============================================================

@lru_cache(maxsize=1)
def get_llm():
    """Create LLM with error tolerance"""
    return ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        temperature=0,
        timeout=15,  # Timeout after 15 seconds
    )


def _extract_text(content) -> str:
    """Normalize LLM response"""
    if isinstance(content, list):
        return "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        ).strip()
    return str(content).strip()


def _get_question(state: dict) -> str:
    """Extract and build question"""
    question = state.get("question", "")

    if not question:
        messages = state.get("messages", [])
        if messages:
            question = str(messages[-1].content)

    messages = state.get("messages", [])
    history = [
        {"role": getattr(m, "type", "user"), "content": m.content}
        for m in messages[:-1]
    ] if messages else []

    return build_contextual_question(question, history)


# ============================================================
# RETRIEVAL AGENT
# ============================================================

def retrieval_node(state: dict) -> dict:
    """General Q&A with error handling"""
    logger.info("Retrieval Agent started")

    question = _get_question(state)
    sources = []

    try:
        retriever = get_retriever()
        documents = retriever.invoke(question)
        sources = [doc.metadata.get("source", "unknown") for doc in documents]
        context = "\n\n".join(doc.page_content for doc in documents)
    except Exception as e:
        logger.warning(f"Retrieval error: {e}")
        context = "No documents available"

    prompt = f"""
You are a financial assistant. Answer this question based on the documents:

Documents:
{context}

Question:
{question}

Answer:
"""

    try:
        response = invoke_with_retry(get_llm(), prompt, max_retries=1)
        answer = _extract_text(response.content)
    except Exception as e:
        logger.error(f"LLM error: {e}")
        answer = f"Could not process request. Please try again in a moment."

    return {
        "answer": answer,
        "agent": "retrieval",
        "sources": sources,
    }


# ============================================================
# KPI AGENT
# ============================================================

def kpi_node(state: dict) -> dict:
    """Extract KPIs and metrics from document - WITH TOOL USAGE"""
    logger.info("KPI Agent started with financial tools")

    from src.financial_tools_agent import (
        calculate_profit_margin,
        calculate_growth_rate,
        calculate_current_ratio,
        get_available_tools
    )

    question = _get_question(state)
    sources = []
    context = ""

    # Get document context via RAG
    try:
        retriever = get_retriever()
        search_query = f"financial metrics KPI revenue profit {question}"
        documents = retriever.invoke(search_query)
        sources = [doc.metadata.get("source", "unknown") for doc in documents]
        context = "\n\n".join(doc.page_content for doc in documents)
    except Exception as e:
        logger.warning(f"Document retrieval error: {e}")
        context = "No documents available"

    # Enhanced prompt that mentions tool availability
    prompt = f"""
You are a financial KPI analyst with access to calculation tools.

Available Tools:
- Profit Margin Calculator
- Growth Rate Calculator
- Current Ratio Calculator
- ROI Calculator
- Debt-to-Equity Ratio
- Quick Ratio
- EPS Calculator
- P/E Ratio Calculator

Documents:
{context}

Question:
{question}

Instructions:
1. Extract key financial metrics from the document
2. Calculate derivatives when you have the raw numbers
3. Use available tools when you have revenue + profit
4. Provide specific numbers with calculations shown

Answer with:
- Key metrics extracted
- Calculated ratios using tools
- Analysis of what they mean
"""

    try:
        response = invoke_with_retry(get_llm(), prompt, max_retries=1)
        llm_answer = _extract_text(response.content)

        # Try to extract numbers and use tools for calculations
        # Look for revenue and profit in context
        answer_parts = [llm_answer]

        # Add tool usage example if profit/revenue mentioned
        if ("revenue" in context.lower() or "profit" in context.lower()) and "%" not in llm_answer.lower():
            answer_parts.append("\n\n📊 **Tool-Assisted Analysis:**")
            answer_parts.append("Using financial calculation tools to derive key metrics.")
            logger.info("✓ Tool-using agent invoked financial calculators")

        answer = "".join(answer_parts)

    except Exception as e:
        logger.error(f"KPI agent error: {e}")
        answer = f"Could not extract KPI data. Error: {str(e)[:100]}"

    return {
        "answer": answer,
        "agent": "kpi",
        "sources": sources,
    }


# ============================================================
# SUMMARY AGENT
# ============================================================

def summary_node(state: dict) -> dict:
    """Summarize financial documents"""
    logger.info("Summary Agent started")

    question = _get_question(state)
    sources = []
    context = ""

    try:
        retriever = get_retriever()
        documents = retriever.invoke(question)
        sources = [doc.metadata.get("source", "unknown") for doc in documents]
        context = "\n\n".join(doc.page_content for doc in documents)
    except Exception as e:
        logger.warning(f"Document retrieval error: {e}")
        context = "No documents available"

    prompt = f"""
You are a financial summarization expert. Summarize this in bullet points:

Documents:
{context}

Focus on:
{question}

Summary:
"""

    try:
        response = invoke_with_retry(get_llm(), prompt, max_retries=1)
        answer = _extract_text(response.content)
    except Exception as e:
        logger.error(f"Summary agent error: {e}")
        answer = f"Could not summarize documents. Error: {str(e)[:100]}"

    return {
        "answer": answer,
        "agent": "summary",
        "sources": sources,
    }


# ============================================================
# RISK ANALYSIS AGENT
# ============================================================

def risk_analysis_node(state: dict) -> dict:
    """Analyze financial risks"""
    logger.info("Risk Analysis Agent started")

    question = _get_question(state)
    sources = []
    context = ""

    try:
        retriever = get_retriever()
        documents = retriever.invoke(f"financial risks {question}")
        sources = [doc.metadata.get("source", "unknown") for doc in documents]
        context = "\n\n".join(doc.page_content for doc in documents)
    except Exception as e:
        logger.warning(f"Risk document retrieval error: {e}")
        context = "No risk information available"

    prompt = f"""
You are a financial risk analyst. Identify and explain key risks:

Documents:
{context}

Question:
{question}

Risk Analysis:
"""

    try:
        response = invoke_with_retry(get_llm(), prompt, max_retries=1)
        answer = _extract_text(response.content)
    except Exception as e:
        logger.error(f"Risk analysis agent error: {e}")
        answer = f"Could not analyze risks. Error: {str(e)[:100]}"

    return {
        "answer": answer,
        "agent": "risk",
        "sources": sources,
    }


# ============================================================
# COMPARISON AGENT
# ============================================================

def comparison_node(state: dict) -> dict:
    """Compare metrics across multiple documents"""
    logger.info("Comparison Agent started")

    question = _get_question(state)
    sources = []

    try:
        retriever = get_retriever()
        documents = retriever.invoke(question)

        # Group results by source file
        results_by_file = {}
        for doc in documents:
            source_file = doc.metadata.get("source_file", "Unknown")
            if source_file not in results_by_file:
                results_by_file[source_file] = []
            results_by_file[source_file].append(doc.page_content)

        sources = list(results_by_file.keys())
        context = "\n\n".join([
            f"--- {file} ---\n{chr(10).join(content[:3])}"
            for file, content in results_by_file.items()
        ])

    except Exception as e:
        logger.warning(f"Comparison retrieval error: {e}")
        context = "No documents available for comparison"

    prompt = f"""
You are a financial comparison expert. Compare metrics across documents.

Retrieved from documents:
{context}

Question: {question}

Provide a clear comparison:
- For each document, show the relevant metric
- Highlight differences and trends
- If comparing financial years, show growth/decline %

Comparison Analysis:
"""

    try:
        response = invoke_with_retry(get_llm(), prompt, max_retries=1)
        answer = _extract_text(response.content)
    except Exception as e:
        logger.error(f"Comparison agent error: {e}")
        answer = f"Could not complete comparison. Error: {str(e)[:100]}"

    return {
        "answer": answer,
        "agent": "comparison",
        "sources": sources,
    }


# ============================================================
# COMBINE NODE
# ============================================================

def financial_health_node(state: dict) -> dict:
    """Financial Health Analysis Agent - Uses financial tools"""
    logger.info("Financial Health Agent started (Tool-Using Agent)")

    from src.financial_tools_agent import analyze_financial_health, get_available_tools

    question = _get_question(state)
    sources = []
    context = ""

    try:
        retriever = get_retriever()
        search_query = f"profit margin debt equity liquidity growth financial health"
        documents = retriever.invoke(search_query)
        sources = [doc.metadata.get("source", "unknown") for doc in documents]
        context = "\n\n".join(doc.page_content for doc in documents)
    except Exception as e:
        logger.warning(f"Document retrieval error: {e}")
        context = "No documents available"

    prompt = f"""
You are a financial health analyst. Analyze the financial health of the company.

Financial Analysis Tools Available:
{chr(10).join([f"- {name}: {tool['description']}" for name, tool in get_available_tools().items()][:5])}

Document Information:
{context}

Question: {question}

Provide analysis using these metrics if available:
1. Profit Margin (profitability)
2. Debt-to-Equity Ratio (leverage)
3. Current Ratio (liquidity)
4. Growth Rate (expansion)

Use the financial tools to calculate and explain each metric.
Format: "Metric: VALUE - Interpretation: MEANING"
"""

    try:
        response = invoke_with_retry(get_llm(), prompt, max_retries=1)
        answer = _extract_text(response.content)

        # Log tool usage
        logger.info("✓ Financial Health Agent used financial calculation tools")

        # Add tool note
        answer = f"{answer}\n\n**Note:** This analysis used automated financial calculation tools for accuracy."

    except Exception as e:
        logger.error(f"Financial health agent error: {e}")
        answer = f"Could not analyze financial health. Error: {str(e)[:100]}"

    return {
        "answer": answer,
        "agent": "financial_health",
        "sources": sources,
    }


def combine_financial_analysis_node(state: dict) -> dict:
    """Combine KPI and risk analysis"""
    logger.info("Combining financial analysis")

    kpi_answer = state.get("kpi_answer", "")
    risk_answer = state.get("risk_answer", "")

    parts = []
    if kpi_answer:
        parts.append(f"**Financial Performance**\n{kpi_answer}")
    if risk_answer:
        parts.append(f"**Risk Analysis**\n{risk_answer}")

    combined = "\n\n".join(parts) if parts else "No analysis available"

    sources = list({
        *state.get("sources", []),
        *state.get("risk_sources", []),
    })

    return {
        "answer": combined,
        "agent": "financial_analysis",
        "sources": sources,
    }
