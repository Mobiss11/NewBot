# Memory System

The memory system is the core differentiating feature of this bot.
It has two levels that work together to create a persistent, personalized experience.

## Short-Term Memory (Dialog Memory)

**Purpose**: Maintain context within the current conversation.

**How it works**:
1. Every user message and assistant response is saved to the `messages` table
2. When building LLM context, the last 10 messages are loaded (configurable via `SHORT_TERM_LIMIT`)
3. Messages are ordered oldest-first and included as conversation history

**Lifecycle**:
- Created: On every message exchange
- Cleared: By `/reset` command
- Persists: Between sessions (survives bot restart)

## Long-Term Memory (Fact Memory)

**Purpose**: Remember specific facts about the user across conversations and resets.

**How it works**:

### Extraction Trigger
After saving each assistant response, `schedule_fact_extraction()` fires.
It checks if the total message count for this (user, avatar) pair is a multiple
of `FACT_EXTRACTION_INTERVAL` (default: 5). If yes, extraction runs.

### Extraction Process
1. Load the last 10 messages as conversation context
2. Load existing facts to avoid duplicates
3. Send a special prompt to the LLM asking it to extract new facts
4. Parse the JSON array response
5. Save new facts to `memory_facts` table

### Extraction Prompt
```
You are a memory extraction system. Analyze the conversation below
and extract concrete, personal facts about the user.

Facts should be:
- Specific and factual (name, age, city, job, hobbies, preferences)
- Expressed as short declarative sentences
- Only NEW information not already in the existing facts

Return ONLY a valid JSON array of strings. Return [] if no new facts.
```

### Injection into Context
On every LLM call, facts are appended to the system prompt:
```
[LONG-TERM MEMORY — things you remember about this person]
- User's name is Alex
- User works as a frontend developer
- User has a cat named Pixel
Use these facts naturally in conversation.
```

### Safety Limits
- Maximum 20 facts per (user, avatar) pair
- Oldest facts are trimmed when limit is exceeded
- JSON parsing failures are silently logged and skipped
- LLM API failures don't affect the main conversation

## How They Work Together

```
System Prompt:
┌─────────────────────────────┐
│  Avatar personality prompt   │
│  +                          │
│  Long-term facts (if any)   │
├─────────────────────────────┤
│  Last 10 messages (history) │
├─────────────────────────────┤
│  Current user message        │
└─────────────────────────────┘
```

The LLM sees the full context: who it is (avatar), what it remembers (facts),
what was recently discussed (history), and what the user just said.
