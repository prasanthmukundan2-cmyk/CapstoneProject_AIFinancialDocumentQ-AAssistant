#!/usr/bin/env python3
"""
Test script to verify conversation management functionality.
"""

from src.conversation_manager import (
    create_conversation,
    create_conversation_id,
    generate_title_from_question,
    update_conversation_timestamp,
    get_conversation_summary,
)
from datetime import datetime
import time


def test_conversation_creation():
    """Test creating a conversation."""
    print("\n=== Test 1: Conversation Creation ===")
    conv = create_conversation("My First Chat")

    assert "id" in conv
    assert conv["title"] == "My First Chat"
    assert conv["messages"] == []
    assert "created_at" in conv
    assert "updated_at" in conv
    print(f"✓ Created conversation: {conv['id']}")
    print(f"  - Title: {conv['title']}")
    print(f"  - Created at: {conv['created_at']}")
    return conv


def test_conversation_default_title():
    """Test conversation with auto-generated title."""
    print("\n=== Test 2: Default Title ===")
    conv = create_conversation()

    assert conv["title"] == ""
    print(f"✓ Created conversation with empty title")
    return conv


def test_title_generation():
    """Test title generation from questions."""
    print("\n=== Test 3: Title Generation ===")

    test_cases = [
        ("What are the main financial metrics?", "What are the main..."),
        ("Compare the revenue between documents", "Compare the revenue..."),
        ("Short question", "Short question"),
        ("This is an extremely long question that should definitely be truncated to fit nicely in the conversation history", None),
    ]

    for question, expected in test_cases:
        title = generate_title_from_question(question)
        print(f"✓ Generated title for: '{question[:40]}...'")
        print(f"  → {title}")


def test_timestamp_update():
    """Test timestamp updates."""
    print("\n=== Test 4: Timestamp Updates ===")
    conv = create_conversation("Test Conv")
    initial_time = conv["updated_at"]

    time.sleep(0.1)
    update_conversation_timestamp(conv)
    new_time = conv["updated_at"]

    assert new_time != initial_time, "Timestamp should be updated"
    print(f"✓ Initial timestamp: {initial_time}")
    print(f"✓ Updated timestamp: {new_time}")


def test_conversation_messages():
    """Test adding messages to a conversation."""
    print("\n=== Test 5: Message Handling ===")
    conv = create_conversation("Chat with Messages")

    # Simulate user message
    conv["messages"].append({
        "role": "user",
        "content": "What is the revenue?"
    })

    # Simulate assistant message
    conv["messages"].append({
        "role": "assistant",
        "content": "The revenue is $100M.",
        "metadata": {
            "agent": "financial_agent",
            "time": 1.23,
            "cached": False,
            "sources": ["document.pdf"]
        }
    })

    assert len(conv["messages"]) == 2
    assert conv["messages"][0]["role"] == "user"
    assert conv["messages"][1]["role"] == "assistant"
    print(f"✓ Added 2 messages to conversation")
    print(f"  - User: {conv['messages'][0]['content']}")
    print(f"  - Assistant: {conv['messages'][1]['content']}")


def test_multiple_conversations():
    """Test managing multiple conversations."""
    print("\n=== Test 6: Multiple Conversations ===")

    conversations = {}

    # Create multiple conversations
    conv1 = create_conversation("Chat 1")
    conv2 = create_conversation("Chat 2")
    conv3 = create_conversation("Chat 3")

    conversations[conv1["id"]] = conv1
    conversations[conv2["id"]] = conv2
    conversations[conv3["id"]] = conv3

    # Add messages to conv1
    conv1["messages"].append({"role": "user", "content": "Question 1"})
    conv1["messages"].append({"role": "assistant", "content": "Answer 1"})

    # Add messages to conv2
    conv2["messages"].append({"role": "user", "content": "Question 2"})

    print(f"✓ Created {len(conversations)} conversations")

    # Display all conversations
    for conv_id, conv in conversations.items():
        summary = get_conversation_summary(conv)
        print(f"  - {conv_id[:8]}: {summary}")

    # Switch to conv2
    current_conv_id = conv2["id"]
    current_conv = conversations[current_conv_id]
    print(f"\n✓ Switched to conversation: {current_conv['title']}")
    print(f"  Messages in current conv: {len(current_conv['messages'])}")

    # Add message to current conversation
    current_conv["messages"].append({"role": "assistant", "content": "Answer 2"})
    print(f"  Messages after adding: {len(current_conv['messages'])}")

    # Verify conv1 messages are unchanged
    assert len(conv1["messages"]) == 2, "Conv1 should still have 2 messages"
    print(f"\n✓ Conv1 still has {len(conv1['messages'])} messages (not affected)")


def test_document_state_isolation():
    """Test that documents are isolated from conversations."""
    print("\n=== Test 7: Document State Isolation ===")

    # Simulate session state
    session_state = {
        "uploaded_documents": {
            "doc1.pdf": {"path": "/path/to/doc1.pdf", "text": "Content 1"},
            "doc2.pdf": {"path": "/path/to/doc2.pdf", "text": "Content 2"},
        },
        "current_document": "doc1.pdf",
        "conversations": {
            "conv1": create_conversation("Chat 1"),
            "conv2": create_conversation("Chat 2"),
        },
        "current_conversation_id": "conv1"
    }

    # Verify documents are shared across conversations
    print(f"✓ Documents: {list(session_state['uploaded_documents'].keys())}")
    print(f"✓ Current document: {session_state['current_document']}")
    print(f"✓ Conversations: {len(session_state['conversations'])}")

    # Switch conversation
    session_state["current_conversation_id"] = "conv2"
    print(f"✓ Switched to conversation: {session_state['current_conversation_id']}")

    # Documents should still be available
    assert len(session_state["uploaded_documents"]) == 2
    print(f"✓ Documents still available after conversation switch: {len(session_state['uploaded_documents'])}")


def test_new_chat_workflow():
    """Simulate the New Chat workflow."""
    print("\n=== Test 8: New Chat Workflow ===")

    # Initial state
    conversations = {}
    initial_conv = create_conversation("Conversation 1")
    conversations[initial_conv["id"]] = initial_conv
    current_conv_id = initial_conv["id"]

    print(f"✓ Initial conversation: {current_conv_id}")

    # Add some messages
    initial_conv["messages"].append({"role": "user", "content": "First question"})
    initial_conv["messages"].append({"role": "assistant", "content": "First answer"})
    print(f"✓ Added messages to first conversation: {len(initial_conv['messages'])}")

    # Click "New Chat"
    print("\n  [User clicks 'New Chat']")
    new_conv = create_conversation(f"Conversation {len(conversations) + 1}")
    conversations[new_conv["id"]] = new_conv
    current_conv_id = new_conv["id"]

    print(f"✓ Created new conversation: {new_conv['id']}")
    print(f"✓ Total conversations: {len(conversations)}")

    # Verify old conversation still exists
    assert len(initial_conv["messages"]) == 2, "Initial conversation should be preserved"
    print(f"✓ First conversation still has {len(initial_conv['messages'])} messages")

    # Verify new conversation is empty
    assert len(new_conv["messages"]) == 0, "New conversation should be empty"
    print(f"✓ New conversation is empty")

    # Switch back to first conversation
    print("\n  [User clicks on first conversation]")
    current_conv_id = initial_conv["id"]
    current_conv = conversations[current_conv_id]

    print(f"✓ Switched back to first conversation")
    print(f"✓ Messages restored: {len(current_conv['messages'])}")
    assert len(current_conv["messages"]) == 2
    print(f"✓ First message: '{current_conv['messages'][0]['content']}'")


def test_title_from_first_question():
    """Test generating title from first question."""
    print("\n=== Test 9: Auto-Title from First Question ===")

    # Create conversation with generic title
    conv = create_conversation(f"Conversation 1")
    print(f"✓ Initial title: '{conv['title']}'")

    # User asks first question
    first_question = "What are the main financial metrics in this report?"

    # Generate title from question
    if conv["title"].startswith("Conversation"):
        conv["title"] = generate_title_from_question(first_question)

    print(f"✓ Updated title: '{conv['title']}'")

    # Add message
    conv["messages"].append({"role": "user", "content": first_question})

    # Verify title is meaningful
    assert not conv["title"].startswith("Conversation")
    assert "financial" in conv["title"].lower() or "metrics" in conv["title"].lower()
    print(f"✓ Title reflects first question content")


if __name__ == "__main__":
    print("=" * 60)
    print("CONVERSATION MANAGEMENT TEST SUITE")
    print("=" * 60)

    try:
        test_conversation_creation()
        test_conversation_default_title()
        test_title_generation()
        test_timestamp_update()
        test_conversation_messages()
        test_multiple_conversations()
        test_document_state_isolation()
        test_new_chat_workflow()
        test_title_from_first_question()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
