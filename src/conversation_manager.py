"""
Conversation management for multi-conversation support.
Handles creation, switching, and persistence of conversations.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional


def create_conversation_id() -> str:
    """Generate a unique conversation ID."""
    return str(uuid.uuid4())[:8]


def generate_title_from_question(question: str, max_length: int = 50) -> str:
    """
    Generate a conversation title from the first question.
    Simple deterministic logic - no API calls.
    """
    # Remove extra whitespace and limit length
    title = question.strip()

    # Truncate to max_length, break on word boundary
    if len(title) > max_length:
        title = title[:max_length].rsplit(' ', 1)[0] + "..."

    return title if title else "Untitled Conversation"


def create_conversation(title: str = "") -> Dict:
    """Create a new conversation object."""
    conv_id = create_conversation_id()
    now = datetime.now().isoformat()

    return {
        "id": conv_id,
        "title": title,
        "messages": [],
        "created_at": now,
        "updated_at": now,
    }


def update_conversation_timestamp(conversation: Dict) -> None:
    """Update the 'updated_at' timestamp of a conversation."""
    conversation["updated_at"] = datetime.now().isoformat()


def get_conversation_summary(conversation: Dict) -> str:
    """
    Get a summary of a conversation (title + count).
    """
    msg_count = len(conversation.get("messages", []))
    title = conversation.get("title", "Untitled")

    if msg_count == 0:
        return f"{title}"
    else:
        return f"{title} ({msg_count} messages)"
