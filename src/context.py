def build_contextual_question(
    question: str,
    messages: list,
) -> str:
    """
    Build a self-contained question using
    recent conversation history.
    """

    if not messages:
        return question

    history = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in messages[-6:]
    )

    return (
        "Conversation history:\n"
        f"{history}\n\n"
        "Current question:\n"
        f"{question}"
    )