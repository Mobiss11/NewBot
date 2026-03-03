# Streaming Implementation

## Overview

The bot streams LLM responses to Telegram by repeatedly editing a single message
as new chunks arrive. This creates a "typing" effect similar to ChatGPT.

## How It Works

1. Bot sends a placeholder message ("...")
2. LLM response arrives as an async stream of text chunks
3. Chunks are accumulated into `full_text`
4. Every ~1 second, the message is edited with the current `full_text + " ▌"` (cursor)
5. When streaming completes, final edit removes the cursor

## Key Design Decisions

### No parse_mode During Streaming
Telegram's Markdown/HTML parser requires complete, valid markup.
Mid-stream text often has unclosed formatting (e.g., `**bold` without closing `**`).
Sending partial Markdown would cause `TelegramBadRequest` errors.
Therefore, all intermediate edits use plain text (no `parse_mode`).

### Rate Limiting (1 second interval)
Telegram's Bot API has rate limits:
- ~30 messages per second per chat
- `editMessageText` with identical text returns "message is not modified"

Editing every 1 second is a safe balance between responsiveness and rate limits.
Configured via `STREAM_EDIT_INTERVAL` in settings.

### Error Handling
- `TelegramBadRequest` on edit: caught silently (message unchanged or format error)
- LLM API failure: placeholder is edited to a user-friendly error message
- Empty response: shows "I couldn't generate a response"

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `STREAM_EDIT_INTERVAL` | 1.0 | Seconds between message edits |
| `OPENROUTER_MODEL` | google/gemini-2.5-flash-lite | Model used for streaming |
