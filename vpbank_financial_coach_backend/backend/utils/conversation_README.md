# Conversation Utils Documentation

## Overview

The `conversation_utils.py` module provides essential functions for managing conversation turns, agent locks, and plan stages in the VPBank Financial Coach system. This module has been refactored to use dictionary-based operations for consistency with other utils modules.

## Key Features

- **Dictionary-Based Operations**: All functions use `Dict[str, Any]` for consistency
- **Agent Lock Management**: Track which agent currently has conversation control
- **Plan Stage Tracking**: Monitor conversation progression through plan stages
- **Simplified Architecture**: Removed complex update/query functions for better maintainability

## Functions Overview

### 1. `add_conversation_turn_for_user()`

**Purpose**: Creates a new conversation turn in the database

**Signature**:
```python
async def add_conversation_turn_for_user(
    db: AsyncIOMotorDatabase, 
    user_id: str, 
    turn_dict: Dict[str, Any]
) -> conversation.ConversationTurnInDB
```

**Parameters**:
- `db`: MongoDB database connection
- `user_id`: The user's unique identifier
- `turn_dict`: Dictionary containing conversation turn data

**Required Fields in turn_dict**:
```python
{
    "user_input": str,           # User's message
    "agent_output": str,         # Agent's response
    "agent_list": List[str],     # Agents involved (optional, defaults to [])
    "tool_call_list": List[str], # Tools called (optional, defaults to [])
    "agent_lock": str,           # Current agent lock (optional)
    "plan_stage": str            # Current plan stage (optional)
}
```

**Example Usage**:
```python
turn_data = {
    "user_input": "I want to create a budget plan",
    "agent_output": "I'll help you create a budget plan. Let me gather some information...",
    "agent_list": ["orchestrator", "plan"],
    "tool_call_list": ["plan.create_plan()"],
    "agent_lock": "plan",
    "plan_stage": "1"
}

result = await add_conversation_turn_for_user(db, "user123", turn_data)
```

### 2. `get_conversation_history_for_user()`

**Purpose**: Retrieves conversation history as raw dictionaries

**Signature**:
```python
async def get_conversation_history_for_user(
    db: AsyncIOMotorDatabase, 
    user_id: str, 
    limit: int = 10
) -> List[Dict[str, Any]]
```

**Parameters**:
- `db`: MongoDB database connection
- `user_id`: The user's unique identifier
- `limit`: Maximum number of turns to retrieve (default: 10)

**Returns**: List of conversation turn dictionaries (oldest first)

**Example Usage**:
```python
history = await get_conversation_history_for_user(db, "user123", limit=20)
for turn in history:
    print(f"User: {turn['user_input']}")
    print(f"Agent: {turn['agent_output']}")
    print(f"Stage: {turn.get('plan_stage', 'N/A')}")
```

### 3. `get_latest_conversation_turn_for_user()`

**Purpose**: Gets the most recent conversation turn (used internally by other functions)

**Signature**:
```python
async def get_latest_conversation_turn_for_user(
    db: AsyncIOMotorDatabase, 
    user_id: str
) -> Optional[conversation.ConversationTurnInDB]
```

**Returns**: Latest conversation turn as Pydantic model or None

### 4. `get_agent_lock_for_user()`

**Purpose**: Gets the current agent lock from the latest conversation turn

**Signature**:
```python
async def get_agent_lock_for_user(
    db: AsyncIOMotorDatabase, 
    user_id: str
) -> Optional[str]
```

**Returns**: Agent name that currently has the lock, or None

**Example Usage**:
```python
current_agent = await get_agent_lock_for_user(db, "user123")
if current_agent:
    print(f"Conversation is locked by: {current_agent}")
else:
    print("No agent lock active")
```

### 5. `get_plan_stage_for_user()`

**Purpose**: Gets the current plan stage from the latest conversation turn

**Signature**:
```python
async def get_plan_stage_for_user(
    db: AsyncIOMotorDatabase, 
    user_id: str
) -> Optional[str]
```

**Returns**: Current plan stage string, or None

**Example Usage**:
```python
stage = await get_plan_stage_for_user(db, "user123")
if stage:
    print(f"Current plan stage: {stage}")
else:
    print("No active plan stage")
```

## Usage Patterns

### Agent Lock Management

Agent locks are now managed entirely through conversation turns:

```python
# Set an agent lock by creating a conversation turn
turn_data = {
    "user_input": "Help me with budgeting",
    "agent_output": "I'll help you with that...",
    "agent_list": ["plan"],
    "agent_lock": "plan"  # This sets the lock
}
await add_conversation_turn_for_user(db, user_id, turn_data)

# Check current lock
current_agent = await get_agent_lock_for_user(db, user_id)

# Release lock by creating turn without agent_lock field
release_turn = {
    "user_input": "Thanks for the help",
    "agent_output": "You're welcome!",
    "agent_list": ["orchestrator"]
    # No agent_lock field = lock released
}
await add_conversation_turn_for_user(db, user_id, release_turn)
```

### Plan Stage Progression

Track conversation progress through plan stages:

```python
# Stage 1: Initial planning
stage1_turn = {
    "user_input": "I want to save money",
    "agent_output": "Let's create a savings plan...",
    "agent_list": ["plan"],
    "plan_stage": "1"
}
await add_conversation_turn_for_user(db, user_id, stage1_turn)

# Stage 2: Gathering information
stage2_turn = {
    "user_input": "My income is $5000",
    "agent_output": "Great! Now let's set up your jars...",
    "agent_list": ["plan", "jar"],
    "plan_stage": "2"
}
await add_conversation_turn_for_user(db, user_id, stage2_turn)

# Check current stage
current_stage = await get_plan_stage_for_user(db, user_id)
```

## Data Model

### Conversation Turn Structure

```python
{
    "_id": "ObjectId(auto-generated)",
    "user_id": "string",
    "timestamp": "datetime (auto-generated)",
    "user_input": "string (required)",
    "agent_output": "string (required)",
    "agent_list": ["string", ...] (optional, default: []),
    "tool_call_list": ["string", ...] (optional, default: []),
    "agent_lock": "string (optional)",
    "plan_stage": "string (optional)"
}
```

### Valid Agent Names (AGENT_LIST)

- `"classifier"` - Input classification agent
- `"jar"` - Budget jar management agent  
- `"fee"` - Recurring fee management agent
- `"plan"` - Budget planning agent
- `"fetcher"` - Transaction fetching agent
- `"knowledge"` - Knowledge base agent
- `"orchestrator"` - Coordination agent

## Migration Notes

### Changes from Previous Version

1. **Removed Functions**:
   - `set_agent_lock_for_user()` - Replaced by conversation turns
   - `update_conversation_turn_agent_lock()` - No longer needed
   - `update_conversation_turn_plan_stage()` - No longer needed
   - `get_conversation_turns_by_agent_lock()` - Simplified architecture
   - `get_conversation_turns_by_plan_stage()` - Simplified architecture

2. **Modified Functions**:
   - `add_conversation_turn_for_user()` now uses Dict input instead of Pydantic model
   - `get_conversation_history_for_user()` returns Dict list instead of Pydantic models
   - `get_agent_lock_for_user()` only checks conversation turns (no separate collection)

3. **New Functions**:
   - `get_plan_stage_for_user()` - Easy access to current plan stage

## Best Practices

### 1. Always Include Required Fields
```python
# ✅ Good
turn_data = {
    "user_input": "Hello",
    "agent_output": "Hi there!",
    "agent_list": ["orchestrator"]
}

# ❌ Bad - missing required fields
turn_data = {
    "user_input": "Hello"
}
```

### 2. Use Agent Locks Appropriately
```python
# ✅ Good - Set lock when agent needs exclusive control
turn_data = {
    "user_input": "Create a budget plan",
    "agent_output": "I'll guide you through this process...",
    "agent_list": ["plan"],
    "agent_lock": "plan",  # Lock while in planning process
    "plan_stage": "1"
}

# ✅ Good - Release lock when done
completion_turn = {
    "user_input": "Thanks!",
    "agent_output": "Plan created successfully!",
    "agent_list": ["plan"]
    # No agent_lock = released
}
```

### 3. Use Plan Stages for Complex Workflows
```python
# Multi-stage conversation
stages = ["1", "2", "3", "complete"]
for stage in stages:
    turn_data = {
        "user_input": f"Stage {stage} input",
        "agent_output": f"Stage {stage} response",
        "agent_list": ["plan"],
        "plan_stage": stage
    }
    await add_conversation_turn_for_user(db, user_id, turn_data)
```

## Error Handling

All functions handle ObjectId conversion automatically. If a function returns `None`, it indicates:
- No conversation turns exist for the user
- No agent lock is currently active
- No plan stage is currently set

```python
# Safe usage pattern
agent_lock = await get_agent_lock_for_user(db, user_id)
if agent_lock:
    # Agent is locked, handle accordingly
    pass
else:
    # No lock, conversation is free
    pass
```
