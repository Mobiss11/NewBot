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
    existing_block = "\n".join(f"- {f}" for f in existing_facts) if existing_facts else "Пока фактов нет."
    conv_block = "\n".join(f"{m['role']}: {m['content']}" for m in conversation)

    extraction_prompt = (
        "Ты — система извлечения фактов о пользователе из диалога. "
        "Будь МАКСИМАЛЬНО внимательным — извлекай ВСЁ, что пользователь (роль 'user') "
        "упоминает о себе, даже косвенно.\n\n"
        "Какие факты извлекать:\n"
        "- Имя, возраст, пол, город, страна\n"
        "- Работа, профессия, учёба\n"
        "- Хобби, увлечения, интересы\n"
        "- Предпочтения, вкусы (еда, музыка, фильмы, книги)\n"
        "- Отношения, семья, друзья, питомцы\n"
        "- Настроение, эмоции, проблемы, переживания\n"
        "- Планы, мечты, цели\n"
        "- Мнения, убеждения, взгляды\n"
        "- Любые другие персональные детали\n\n"
        "Правила:\n"
        "- Записывай как короткие утвердительные предложения на русском\n"
        "- Извлекай ТОЛЬКО новые факты, которых нет в существующем списке\n"
        "- Факты ТОЛЬКО о пользователе, НЕ о боте/ассистенте\n"
        "- Лучше извлечь лишний факт, чем пропустить важный\n\n"
        f"Существующие факты:\n{existing_block}\n\n"
        f"Диалог:\n{conv_block}\n\n"
        "Верни ТОЛЬКО JSON-массив строк. Пример: "
        '[\"Пользователя зовут Саша\", \"Любит кофе\", \"Работает в IT\"]\n'
        "Если фактов нет — верни []\n"
        "Без пояснений, без markdown — ТОЛЬКО JSON."
    )

    try:
        response = await client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[{"role": "user", "content": extraction_prompt}],
        )
        raw = response.choices[0].message.content or "[]"
        logger.debug(f"Fact extraction raw LLM response: {raw!r}")

        # Try to extract JSON array from the response
        raw = raw.strip()
        if raw.startswith("```"):
            # Strip markdown code fences
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            raw = raw.strip()

        # Try to find JSON array if LLM wrapped it in text
        if not raw.startswith("["):
            start = raw.find("[")
            end = raw.rfind("]")
            if start != -1 and end != -1:
                raw = raw[start : end + 1]

        facts = json.loads(raw)
        if isinstance(facts, list):
            result = [str(f) for f in facts if f and str(f).strip()]
            logger.debug(f"Parsed {len(result)} facts from response")
            return result
        logger.warning(f"LLM returned non-list type: {type(facts)}")
        return []
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        logger.warning(f"Failed to parse facts from LLM response: {exc}, raw={raw!r}")
        return []
    except Exception as exc:
        logger.error(f"Fact extraction LLM call failed: {exc}")
        return []
