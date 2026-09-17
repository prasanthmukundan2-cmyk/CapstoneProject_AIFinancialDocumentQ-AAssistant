"""
Investment Recommendation Agent
Generates investment recommendations based on financial analysis
"""

import logging
from src.retry_utils import invoke_with_retry
from src.agents_fixed import get_llm, _extract_text, _get_question
from src.rag_pipeline import get_retriever

logger = logging.getLogger(__name__)


def investment_recommendation_node(state: dict) -> dict:
    """
    Generate a comprehensive investment recommendation.

    This agent combines:
    - Financial analysis
    - Risk assessment
    - KPI evaluation
    - Recommendation synthesis

    Output goes to human_approval for review before showing to user.
    """

    logger.info("Investment Recommendation Agent started")

    question = _get_question(state)

    # Get existing analysis from state (if available)
    kpi_answer = state.get("kpi_answer", "")
    risk_answer = state.get("risk_answer", "")

    # If we don't have analysis yet, do financial analysis
    if not kpi_answer or not risk_answer:
        kpi_answer, risk_answer = _perform_financial_analysis(question)

    # Generate investment recommendation
    recommendation = _generate_recommendation(
        question=question,
        kpi_analysis=kpi_answer,
        risk_analysis=risk_answer
    )

    return {
        "answer": recommendation,
        "agent": "investment_recommendation",
        "requires_approval": True,  # Always requires approval
        "kpi_analysis": kpi_answer,
        "risk_analysis": risk_answer,
        "sources": state.get("sources", []),
    }


def _perform_financial_analysis(question: str) -> tuple:
    """
    Perform financial and risk analysis
    """

    try:
        retriever = get_retriever()
        documents = retriever.invoke(question)
        context = "\n\n".join(doc.page_content for doc in documents)
    except Exception as e:
        logger.warning(f"Retrieval error: {e}")
        context = "No financial documents available"

    # KPI Analysis
    kpi_prompt = f"""
You are a financial analyst. Extract and analyze key KPIs from the documents:

Documents:
{context}

Question:
{question}

Analyze:
1. Revenue and growth
2. Profitability metrics
3. Debt and leverage ratios
4. Liquidity position

KPI Analysis:
"""

    try:
        kpi_response = invoke_with_retry(get_llm(), kpi_prompt, max_retries=1)
        kpi_answer = _extract_text(kpi_response.content)
    except Exception as e:
        logger.error(f"KPI analysis error: {e}")
        kpi_answer = "Could not analyze KPIs"

    # Risk Analysis
    risk_prompt = f"""
You are a risk analyst. Identify and assess key risks from the documents:

Documents:
{context}

Question:
{question}

Assess:
1. Financial risks (debt, liquidity)
2. Operational risks (concentration, dependencies)
3. Market risks (competition, sector)
4. Overall risk level (Low/Medium/High)

Risk Analysis:
"""

    try:
        risk_response = invoke_with_retry(get_llm(), risk_prompt, max_retries=1)
        risk_answer = _extract_text(risk_response.content)
    except Exception as e:
        logger.error(f"Risk analysis error: {e}")
        risk_answer = "Could not analyze risks"

    return kpi_answer, risk_answer


def _generate_recommendation(question: str, kpi_analysis: str, risk_analysis: str) -> str:
    """
    Synthesize KPI and risk analysis into investment recommendation
    """

    prompt = f"""
You are an investment advisor. Based on the following analysis,
generate a balanced investment recommendation.

FINANCIAL PERFORMANCE ANALYSIS:
{kpi_analysis}

RISK ANALYSIS:
{risk_analysis}

QUESTION:
{question}

Generate a structured recommendation that:
1. Summarizes key positive indicators
2. Highlights key risks
3. Provides balanced perspective
4. Includes appropriate disclaimers
5. Does NOT make a definitive "buy" or "sell" recommendation
   (That's the human analyst's job - you provide the analysis)

INVESTMENT RESEARCH RECOMMENDATION:
"""

    try:
        response = invoke_with_retry(get_llm(), prompt, max_retries=1)
        recommendation = _extract_text(response.content)
    except Exception as e:
        logger.error(f"Recommendation generation error: {e}")
        recommendation = f"Could not generate recommendation: {str(e)[:100]}"

    return recommendation


def format_recommendation_for_approval(state: dict) -> str:
    """
    Format the recommendation for human approval review
    """

    recommendation = state.get("answer", "")
    kpi_analysis = state.get("kpi_analysis", "")
    risk_analysis = state.get("risk_analysis", "")

    formatted = f"""
═══════════════════════════════════════════════════════════
INVESTMENT RECOMMENDATION - PENDING HUMAN APPROVAL
═══════════════════════════════════════════════════════════

FINANCIAL PERFORMANCE ANALYSIS:
{kpi_analysis}

───────────────────────────────────────────────────────────

RISK ASSESSMENT:
{risk_analysis}

───────────────────────────────────────────────────────────

AI-GENERATED RECOMMENDATION:
{recommendation}

───────────────────────────────────────────────────────────

STATUS: AWAITING HUMAN ANALYST REVIEW

This recommendation has been generated by AI and requires
human analyst review before being shared with the user.

═══════════════════════════════════════════════════════════
"""

    return formatted


def create_user_response(
    recommendation: str,
    approval_status: str,
    analyst_notes: str = ""
) -> str:
    """
    Create final response to show user after approval
    """

    if approval_status == "approved":
        status_badge = "✅ Human Reviewed"
        color = "green"
    elif approval_status == "changes_requested":
        status_badge = "🔄 Changes Requested - Regenerating"
        color = "yellow"
    else:  # rejected
        status_badge = "❌ Not Approved"
        color = "red"

    response = f"""
═══════════════════════════════════════════════════════════
INVESTMENT RESEARCH ANALYSIS
═══════════════════════════════════════════════════════════

{recommendation}

───────────────────────────────────────────────────────────

APPROVAL STATUS: {status_badge}

Review Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}

{f'Analyst Notes: {analyst_notes}' if analyst_notes else ''}

───────────────────────────────────────────────────────────

IMPORTANT DISCLAIMER:

This analysis is based on the financial documents provided.
It has been reviewed by a human analyst.

This recommendation:
✓ Is for informational purposes only
✓ Should not be considered financial advice
✓ Does not guarantee investment performance
✓ Should be reviewed with your financial advisor
✓ Should be considered alongside your risk tolerance

Please conduct additional due diligence before making
any investment decisions.

═══════════════════════════════════════════════════════════
"""

    return response
