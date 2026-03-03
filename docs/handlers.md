# Handlers Documentation

## start.py — Avatar Selection

### `cmd_start(message, session, state)`
- **Trigger**: `/start` command
- **Action**: Creates user if needed, shows inline keyboard with 3 avatars
- **FSM**: Sets state to `selecting_avatar`

### `on_avatar_selected(callback, callback_data, session, state)`
- **Trigger**: `AvatarCallback` in state `selecting_avatar`
- **Action**: Assigns avatar to user, shows confirmation
- **FSM**: Sets state to `chatting`

## chat.py — AI Conversation

### `handle_chat_message(message, session, state)`
- **Trigger**: Any text message in state `chatting`
- **Action**:
  1. Saves user message to DB
  2. Loads short-term history (last 10 messages)
  3. Loads long-term facts from DB
  4. Builds system prompt (avatar personality + facts)
  5. Sends placeholder message ("...")
  6. Streams LLM response, editing message every ~1 second
  7. Saves assistant response to DB
  8. Triggers background fact extraction (every 5 messages)
- **Error handling**: On LLM failure, edits placeholder to error message

## commands.py — Utility Commands

### `cmd_history(message, session)`
- **Trigger**: `/history`
- **Action**: Shows last 10 messages from current dialog
- **Format**: "**You:** message" / "**AvatarName:** message"

### `cmd_facts(message, session)`
- **Trigger**: `/facts`
- **Action**: Shows all long-term facts for current user+avatar pair
- **Format**: Bullet list of facts

### `cmd_reset(message, session)`
- **Trigger**: `/reset`
- **Action**: Deletes all messages for current user+avatar. Keeps facts.
- **Response**: Confirmation with count of deleted messages

### `cmd_change_avatar(message, session, state)`
- **Trigger**: `/change_avatar`
- **Action**: Shows avatar selection keyboard again
- **FSM**: Sets state to `selecting_avatar`
