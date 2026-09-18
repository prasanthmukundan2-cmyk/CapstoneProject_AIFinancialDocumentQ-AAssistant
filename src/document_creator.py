"""
Document Creation & Approval Workflow
Detects when user wants to create documents and handles approval process
"""

import logging
from typing import Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Keywords that indicate document creation requests
DOCUMENT_CREATION_KEYWORDS = [
    "create", "generate", "make", "write", "prepare",
    "document", "report", "summary", "analysis",
    "kpi", "metrics", "financial report", "statement"
]

APPROVAL_KEYWORDS = [
    "approve", "confirm", "accept", "yes", "ok", "okay",
    "looks good", "perfect", "great", "proceed", "go ahead"
]

REJECTION_KEYWORDS = [
    "reject", "decline", "no", "cancel", "discard",
    "don't", "don't want", "redo", "revise", "change"
]


def detect_document_creation_request(question: str) -> bool:
    """
    Detect if user is asking to create/generate a document

    Examples:
    - "Create a financial report based on this KPI data"
    - "Generate a document summarizing the company's metrics"
    - "Write a KPI analysis document"

    Returns:
        bool: True if document creation is requested
    """
    question_lower = question.lower()

    # Check for document creation keywords
    has_creation_keyword = any(
        keyword in question_lower
        for keyword in DOCUMENT_CREATION_KEYWORDS
    )

    if not has_creation_keyword:
        return False

    # Check if it's asking to CREATE something (not just analyze)
    creation_verbs = ["create", "generate", "make", "write", "prepare", "produce"]
    has_creation_verb = any(
        verb in question_lower
        for verb in creation_verbs
    )

    return has_creation_verb


def detect_approval_response(question: str) -> str:
    """
    Detect if user is approving or rejecting a document

    Returns:
        str: "approve", "reject", or "none"
    """
    question_lower = question.lower().strip()

    # Check for approval
    if any(keyword in question_lower for keyword in APPROVAL_KEYWORDS):
        return "approve"

    # Check for rejection
    if any(keyword in question_lower for keyword in REJECTION_KEYWORDS):
        return "reject"

    return "none"


def get_document_creation_prompt(question: str, context: str) -> str:
    """
    Build a prompt for document creation

    Args:
        question: User's request to create document
        context: Document context/analysis

    Returns:
        str: Enhanced prompt for LLM
    """
    prompt = f"""
You are a professional financial document writer.

User Request: {question}

Document Context & Data:
{context}

Please create a professional financial document that:
1. Uses clear, concise language
2. Includes relevant metrics and KPIs
3. Provides actionable insights
4. Is formatted nicely with sections
5. Includes a summary and recommendations

Generate the complete document content below:
---
"""
    return prompt


def create_document_approval_message(document_content: str) -> Dict:
    """
    Create an approval message for the generated document

    Args:
        document_content: The generated document text

    Returns:
        dict: Message with document details
    """
    return {
        "status": "pending_approval",
        "document": document_content,
        "created_at": datetime.now().isoformat(),
        "message": "🔐 DOCUMENT REQUIRES APPROVAL",
        "instruction": """
This document has been generated based on your KPI data.

**Please review and approve:**
- Does the content accurately reflect the data?
- Are the insights helpful?
- Is the formatting professional?

**To approve:** Reply with "Approve" or "Yes"
**To revise:** Reply with "Reject" or describe changes needed
        """
    }


def format_document_for_display(document_content: str) -> str:
    """
    Format document for display in Streamlit

    Args:
        document_content: Raw document text

    Returns:
        str: Formatted document
    """
    return f"""
---
{document_content}
---
"""


def save_approved_document(filename: str, content: str) -> Tuple[bool, str]:
    """
    Save approved document to disk

    Args:
        filename: Document filename
        content: Document content

    Returns:
        tuple: (success, file_path or error_message)
    """
    try:
        from pathlib import Path

        # Create documents folder if not exists
        doc_folder = Path("data/generated_documents")
        doc_folder.mkdir(parents=True, exist_ok=True)

        # Add timestamp if not in filename
        if not filename.endswith(('.pdf', '.txt', '.docx')):
            filename = f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        file_path = doc_folder / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Document saved: {file_path}")
        return True, str(file_path)

    except Exception as e:
        logger.error(f"Error saving document: {e}")
        return False, str(e)


def get_document_creation_response(question: str) -> Dict:
    """
    Get the approval message for document creation

    Args:
        question: User's document creation request

    Returns:
        dict: Approval message structure
    """
    return {
        "type": "document_creation",
        "status": "pending_approval",
        "message": "🔐 DOCUMENT CREATED - AWAITING APPROVAL",
        "instruction": """
A financial document has been generated based on your KPI data.

**Next Steps:**
1. Review the document above
2. If satisfied, reply: "Approve" or "Yes"
3. If changes needed, reply: "Reject" or describe what to change

The document will only be saved after your approval.
        """
    }


if __name__ == "__main__":
    # Test document detection
    test_questions = [
        "Create a financial report based on this KPI data",
        "Generate a document summarizing metrics",
        "What are the main risks?",  # Should return False
        "Write an analysis of the company's performance"
    ]

    for q in test_questions:
        print(f"{q} -> {detect_document_creation_request(q)}")
