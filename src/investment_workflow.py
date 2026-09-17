"""
Enhanced Workflow with Investment Recommendation & Human Approval

This workflow handles investment-related questions with proper
human approval before showing results to the user.
"""

import logging
from typing import TypedDict, Annotated

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from src.agents_fixed import (
    retrieval_node,
    kpi_node,
    summary_node,
    risk_analysis_node,
    combine_financial_analysis_node,
    get_llm,
)
from src.investment_recommendation_agent import investment_recommendation_node

load_dotenv()
logger = logging.getLogger(__name__)


# ============================================================
# WORKFLOW STATE
# ============================================================

class AgentState(TypedDict, total=False):
    """Shared state across all agents"""

    messages: Annotated[list[BaseMessage], add_messages]
    question: str
    agent: str
    answer: str
    sources: list
    requires_approval: bool
    approved: bool
    route: str
    metrics: dict
    error: str
    kpi_answer: str
    risk_answer: str

    # Investment recommendation specific
    kpi_analysis: str
    risk_analysis: str
    recommendation: str
    approval_id: str
    approval_status: str
    analyst_notes: str


# ============================================================
# ROUTER AGENT
# ============================================================

def router_node(state: AgentState):
    """
    Route question to appropriate agent.

    Now detects investment questions and routes to
    investment_recommendation instead of generic handlers.
    """

    logger.info("Router Agent started")

    question = state["messages"][-1].content
    question_lower = question.lower()

    # Investment keywords - these get special handling
    investment_keywords = [
        "invest",
        "buy",
        "sell",
        "investment",
        "should i",
        "can i invest",
        "recommendation",
    ]

    # Check if it's an investment question
    is_investment = any(kw in question_lower for kw in investment_keywords)

    if is_investment:
        logger.info("Investment question detected - routing to investment_recommendation")
        return {
            "question": question,
            "agent": "investment_recommendation",
            "route": "investment_recommendation",
            "requires_approval": True,
        }

    # Check for approval keywords (fallback for investment questions)
    approval_keywords = ["invest", "buy", "sell", "should i"]
    if any(keyword in question_lower for keyword in approval_keywords):
        return {
            "question": question,
            "agent": "human_approval",
            "route": "human_approval",
            "requires_approval": True,
        }

    # For KPI questions
    if any(kw in question_lower for kw in ["revenue", "profit", "growth", "margin"]):
        return {
            "question": question,
            "agent": "kpi",
            "route": "kpi_node",
        }

    # For summary questions
    if any(kw in question_lower for kw in ["summarize", "summary", "overview"]):
        return {
            "question": question,
            "agent": "summary",
            "route": "summary_node",
        }

    # Default to retrieval
    return {
        "question": question,
        "agent": "retrieval",
        "route": "retrieval_node",
    }


# ============================================================
# ROUTING FUNCTION
# ============================================================

def route_decision(state: AgentState):
    """Route to appropriate node based on agent decision"""

    route = state.get("route", "retrieval_node")

    if route == "investment_recommendation":
        return "investment_recommendation"
    elif route == "kpi_node":
        return "kpi_node"
    elif route == "summary_node":
        return "summary_node"
    elif route == "human_approval":
        return "human_approval"

    return "retrieval_node"


# ============================================================
# HUMAN APPROVAL NODE (Enhanced for Investment)
# ============================================================

def human_approval_node(state: AgentState):
    """
    Human approval node for investment recommendations.

    In production, this would:
    1. Send to manager for review
    2. Wait for approval decision
    3. Store approval record

    For now, it marks as requiring approval.
    """

    logger.info("Human approval required")

    agent = state.get("agent", "unknown")

    if agent == "investment_recommendation":
        # This is an investment recommendation - requires approval before release
        return {
            "approval_status": "pending",
            "requires_approval": True,
            "approval_id": __import__('uuid').uuid4().hex[:8],
        }

    # For other approval-requiring questions
    return {
        "answer": (
            "This question requires human approval "
            "before a financial recommendation can be made."
        ),
        "agent": "human_approval",
        "requires_approval": True,
    }


# ============================================================
# CREATE WORKFLOW
# ============================================================

def create_investment_workflow():
    """
    Create workflow with investment recommendation handling.

    Flow for investment questions:
    Question → Router → investment_recommendation →
    human_approval → Response
    """

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("retrieval_node", retrieval_node)
    workflow.add_node("kpi_node", kpi_node)
    workflow.add_node("summary_node", summary_node)
    workflow.add_node("investment_recommendation", investment_recommendation_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("risk_analysis", risk_analysis_node)
    workflow.add_node("combine_financial_analysis", combine_financial_analysis_node)

    # Start → Router
    workflow.add_edge(START, "router")

    # Router → Agent (conditional)
    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "kpi_node": "kpi_node",
            "summary_node": "summary_node",
            "retrieval_node": "retrieval_node",
            "investment_recommendation": "investment_recommendation",
            "human_approval": "human_approval",
        },
    )

    # Investment recommendation → Human approval
    workflow.add_edge("investment_recommendation", "human_approval")

    # Agents → End
    workflow.add_edge("kpi_node", END)
    workflow.add_edge("summary_node", END)
    workflow.add_edge("retrieval_node", END)
    workflow.add_edge("human_approval", END)

    # Compile with memory
    workflow = workflow.compile(
        checkpointer=MemorySaver()
    )

    return workflow


# ============================================================
# HELPER FUNCTION
# ============================================================

def is_investment_question(question: str) -> bool:
    """Check if question is investment-related"""

    keywords = [
        "invest",
        "buy",
        "sell",
        "investment",
        "should i",
        "can i invest",
    ]

    return any(kw in question.lower() for kw in keywords)
