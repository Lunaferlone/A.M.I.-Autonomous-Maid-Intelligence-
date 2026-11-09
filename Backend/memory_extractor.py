import json
import re

from Backend.memory import save_memory
from Backend.ollama_client import chat_with_yona


def extract_user_memories(user_message):
    """Extract explicit and potentially useful facts from user messages."""

    system_prompt = """
You are a memory extraction engine.

Your task is to extract useful long-term information
explicitly stated by the user.

Rules:
1. Extract information only from the user's message.
2. Never extract assumptions or guesses.
3. Never treat AI-generated statements as user facts.
4. Prioritize preferences, habits, goals, projects,
   skills, and stable personal information.
5. Ignore greetings, temporary questions, and small talk.
6. Do not invent missing information.
7. Return valid JSON only.

Required JSON format:
{
    "memories": [
        {
            "category": "preference",
            "content": "The user likes coffee with milk."
        }
    ]
}

If there is no useful information, return:
{
    "memories": []
}
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    response = chat_with_yona(messages)

    try:
        cleaned_response = re.sub(
            r"<think>.*?</think>",
            "",
            response,
            flags=re.DOTALL
        ).strip()

        if cleaned_response.startswith("```"):
            cleaned_response = re.sub(
                r"^```(?:json)?\s*|\s*```$",
                "",
                cleaned_response
            ).strip()

        data = json.loads(cleaned_response)

        memories = data.get("memories", [])

        if not isinstance(memories, list):
            return []

        return [
            memory
            for memory in memories
            if isinstance(memory, dict)
            and isinstance(memory.get("category"), str)
            and isinstance(memory.get("content"), str)
            and memory["category"].strip()
            and memory["content"].strip()
        ]

    except (json.JSONDecodeError, AttributeError):
        return []


def extract_and_save_user_memories(user_message):
    """Extract and save useful information from a user message."""

    memories = extract_user_memories(user_message)

    saved_count = 0
    duplicate_count = 0

    for memory in memories:
        saved = save_memory(
            memory["category"],
            memory["content"]
        )

        if saved:
            saved_count += 1
        else:
            duplicate_count += 1

    return {
        "extracted": len(memories),
        "saved": saved_count,
        "duplicates": duplicate_count
    }