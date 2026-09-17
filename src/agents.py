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


# --------------------------------------------------
# LLM
# --------------------------------------------------

@lru_cache(maxsize=1)
def get_llm():
    """
    Create the chat model once and reuse it.
    """

    return ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        temperature=0,
    )


def _extract_text(content) -> str:
    """
    Normalize LLM response content (str or list of blocks) to plain text.
    """

    if isinstance(content, list):
        return "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        ).strip()

    return str(content).strip()


def _get_question(state: dict) -> str:
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


# --------------------------------------------------
# RETRIEVAL AGENT
# --------------------------------------------------

def retrieval_node(state: dict) -> dict:
    """
    General RAG lookup over the financial documents.
    """

    logger.info("Retrieval Agent started")

    question = _get_question(state)

    retriever = get_retriever()
    documents = retriever.invoke(question)

    context = "\n\n".join(doc.page_content for doc in documents)

    prompt = f"""
You are a financial document assistant.

Answer the question using only the provided financial documents.
If the answer is not available, say:
"I could not find that information in the provided documents."

Financial documents:
{context}

Question:
{question}

Answer:
"""

    response = invoke_with_retry(get_llm(), prompt)

    return {
        "answer": _extract_text(response.content),
        "agent": "retrieval",
        "sources": [
            doc.metadata.get("source", "unknown") for doc in documents
        ],
    }


# --------------------------------------------------
# KPI AGENT
# --------------------------------------------------

def kpi_node(state: dict) -> dict:
    """
    Extract or calculate a financial KPI, preferring the structured
    CSV data and falling back to a plain calculation explanation.
    """

    logger.info("KPI Agent started")

    question = _get_question(state)

    metrics = {}
    lines = []

    try:
        latest = get_financial_record(2024)
        previous = get_financial_record(2023)

        revenue_growth = calculate_growth(
            previous["Revenue_Millions"], latest["Revenue_Millions"]
        )
        profit_margin = calculate_profit_margin(
            latest["Revenue_Millions"], latest["Net_Income_Millions"]
        )
        net_worth = calculate_net_worth(
            latest["Total_Assets_Millions"], latest["Total_Liabilities_Millions"]
        )

        metrics = {
            "revenue_growth_pct": round(revenue_growth, 2),
            "profit_margin_pct": round(profit_margin, 2),
            "net_worth_millions": round(net_worth, 2),
        }

        lines.append(
            f"Revenue growth (2023 to 2024): {metrics['revenue_growth_pct']}%"
        )
        lines.append(f"Profit margin (2024): {metrics['profit_margin_pct']}%")
        lines.append(f"Net worth (2024): ${metrics['net_worth_millions']}M")

    except (FileNotFoundError, ValueError) as error:
        logger.warning("KPI data unavailable: %s", error)

    prompt = f"""
You are a financial KPI assistant.

Use the calculated metrics below (if any) together with the question
to give a concise, numbers-first answer. If metrics are missing, say
you could not calculate them from the available data.

Calculated metrics:
{chr(10).join(lines) if lines else "None available."}

Question:
{question}

Answer:
"""

    response = invoke_with_retry(get_llm(), prompt)

    return {
        "answer": _extract_text(response.content),
        "agent": "kpi",
        "metrics": metrics,
        "kpi_answer": _extract_text(response.content),
        "sources": ["data/balance_sheet.csv"],
    }


# --------------------------------------------------
# SUMMARY AGENT
# --------------------------------------------------

def summary_node(state: dict) -> dict:
    """
    Summarize the retrieved financial document content.
    """

    logger.info("Summary Agent started")

    question = _get_question(state)

    retriever = get_retriever()
    documents = retriever.invoke(question)

    context = "\n\n".join(doc.page_content for doc in documents)

    prompt = f"""
You are a financial summarization assistant.

Summarize the following financial document content in clear,
plain-English bullet points. Focus on what is relevant to the
question below.

Financial documents:
{context}

Question:
{question}

Summary:
"""

    response = invoke_with_retry(get_llm(), prompt)

    return {
        "answer": _extract_text(response.content),
        "agent": "summary",
        "sources": [
            doc.metadata.get("source", "unknown") for doc in documents
        ],
    }


# --------------------------------------------------
# RISK ANALYSIS AGENT (parallel branch)
# --------------------------------------------------

def risk_analysis_node(state: dict) -> dict:
    """
    Analyze financial/market risks from the annual report content.
    """

    logger.info("Risk Analysis Agent started")

    question = state.get("question", "")

    retriever = get_retriever()
    documents = retriever.invoke(f"financial risks {question}")

    context = "\n\n".join(doc.page_content for doc in documents)

    prompt = f"""
You are a financial risk analyst.

Identify and explain the key financial and market risks described
in the documents below, relevant to the question.

Financial documents:
{context}

Question:
{question}

Risk analysis:
"""

    response = invoke_with_retry(get_llm(), prompt)

    return {
        "risk_answer": _extract_text(response.content),
        "risk_sources": [
            doc.metadata.get("source", "unknown") for doc in documents
        ],
    }


# --------------------------------------------------
# COMBINE FINANCIAL ANALYSIS (join node)
# --------------------------------------------------

def combine_financial_analysis_node(state: dict) -> dict:
    """
    Merge the parallel KPI and risk-analysis branches into one answer.
    """

    logger.info("Combining financial analysis")

    kpi_answer = state.get("kpi_answer", "")
    risk_answer = state.get("risk_answer", "")

    parts = []

    if kpi_answer:
        parts.append(f"**Financial Performance**\n{kpi_answer}")

    if risk_answer:
        parts.append(f"**Risk Analysis**\n{risk_answer}")

    combined = "\n\n".join(parts) if parts else (
        "No financial analysis could be generated from the available data."
    )

    sources = list(
        {
            *state.get("sources", []),
            *state.get("risk_sources", []),
        }
    )

    return {
        "answer": combined,
        "agent": "financial_analysis",
        "sources": sources,
    }