"""
Simple Investment Recommendation - Basic Version
Just detects investment questions and shows human approval is needed
"""

import logging

logger = logging.getLogger(__name__)


def detect_investment_question(question: str) -> bool:
    """
    Check if question is investment-related
    Returns True if it needs human approval
    """

    keywords = [
        "invest",
        "buy",
        "sell",
        "investment",
        "should i",
        "can i invest",
        "recommendation",
    ]

    question_lower = question.lower()
    return any(keyword in question_lower for keyword in keywords)


def get_investment_response(question: str) -> dict:
    """
    Simple response for investment questions
    Just indicates human approval is needed
    """

    logger.info(f"Investment question detected: {question}")

    return {
        "answer": """
🔐 **HUMAN APPROVAL REQUIRED**

This is an investment-related question that requires human review.

📋 **What This Means:**
Your question involves financial recommendations that need to be
reviewed and approved by a qualified financial analyst before
a response can be provided.

⏳ **What Happens Next:**
1. A financial analyst will examine this

📧 **You will be notified when the review is complete.**

⚠️ **Important:**
This system cannot provide investment advice without human approval.
Please consult with a qualified financial advisor for investment decisions.
        """,
        "agent": "human_approval",
        "requires_approval": True,
        "investment_question": True,
    }
