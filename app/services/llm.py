import json
from collections.abc import AsyncIterator

from loguru import logger
from openai import AsyncOpenAI

from app.config import settings

client = AsyncOpenAI(
    api_key=settings.openrouter_api_key,
    base_url=settings.openrouter_base_url,
)


async def stream_chat_response(
    messages: list[dict[str, str]],
) -> AsyncIterator[str]:
    """Yield text chunks from OpenRouter streaming response."""
    stream = await client.chat.completions.create(
        model=settings.openrouter_model,
        messages=messages,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def extract_facts_from_conversation(
    conversation: list[dict[str, str]],
    existing_facts: list[str],
) -> list[str]:
    """Ask LLM to extract new facts about the user from recent conversation."""
    existing_block = "\n".join(f"- {f}" for f in existing_facts) if existing_facts else "None yet."
    conv_block = "\n".join(f"{m['role']}: {m['content']}" for m in conversation)

    extraction_prompt = (
        "You are a memory extraction system. Analyze the conversation below and extract "
        "concrete, personal facts about the user. Facts should be:\n"
        "- Specific and factual (name, age, city, job, hobbies, preferences, relationships)\n"
        "- Expressed as short declarative sentences\n"
        "- Only NEW information not already in the existing facts list\n\n"
        f"Existing facts:\n{existing_block}\n\n"
        f"Recent conversation:\n{conv_block}\n\n"
        "Return ONLY a valid JSON array of strings. Return [] if no new facts.\n"
        'Example: ["User\'s name is Alex", "User works as a developer"]'
    )

    try:
        response = await client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[{"role": "user", "content": extraction_prompt}],
        )
        raw = response.choices[0].message.content or "[]"

        # Try to extract JSON array from the response
        raw = raw.strip()
        if raw.startswith("```"):
            # Strip markdown code fences
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            raw = raw.strip()

        facts = json.loads(raw)
        if isinstance(facts, list):
            return [str(f) for f in facts if isinstance(f, str) and f.strip()]
        return []
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        logger.warning(f"Failed to parse facts from LLM response: {exc}")
        return []
    except Exception as exc:
        logger.error(f"Fact extraction LLM call failed: {exc}")
        return []
