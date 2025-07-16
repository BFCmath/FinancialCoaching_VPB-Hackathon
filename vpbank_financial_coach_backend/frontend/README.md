# VPBank Financial Coach - Testing Tools

This directory contains comprehensive testing tools for the VPBank Financial Coach Backend API.

## Files

- **`mock.py`** - Comprehensive API testing script with interactive chat simulator
- **`chat_simulator.py`** - Standalone interactive chat simulator

## Features

### Comprehensive API Testing (`mock.py`)
- Tests all API endpoints (auth, transactions, jars, fees, plans, chat)
- Validates the new ConversationTurnInDB response format
- Interactive checkpoints for manual verification
- Detailed test reporting with pass/fail statistics

### Interactive Chat Simulator
- Real-time conversation with the financial coach agent
- Supports all agent types (classifier, jar, fee, plan, fetcher, knowledge, orchestrator)
- Shows agent locks and plan stages
- Command support: `history`, `status`, `quit`

## Usage

### Option 1: Run mock.py with menu
```bash
python mock.py
```
Choose from:
1. Run comprehensive API tests
2. Start interactive chat simulator  
3. Run tests then start interactive chat

### Option 2: Direct chat mode
```bash
python mock.py chat
```

### Option 3: Standalone chat simulator
```bash
python chat_simulator.py
```

## Chat API Response Format

The improved tests validate the new ConversationTurnInDB response format:

```json
{
  "_id": "conversation_turn_id",
  "user_id": "user_id", 
  "user_input": "Add a $25 transaction to my play jar",
  "agent_output": "I've added a $25 transaction to your play jar for the movie.",
  "agent_list": ["orchestrator", "jar"],
  "tool_call_list": ["route_to_jar_manager"],
  "timestamp": "2025-07-17T10:30:00Z",
  "agent_lock": null,
  "plan_stage": null
}
```

## Interactive Chat Commands

- **Regular message**: Type any message to chat with the agent
- **`history`**: Show recent conversation history
- **`status`**: Show current agent lock and plan stage
- **`quit`** / **`exit`** / **`bye`**: End the chat session

## Agent Lock & Plan Stage

The chat simulator shows:
- 🔒 **Agent Lock**: When conversation is locked to a specific agent
- 📋 **Plan Stage**: Current stage in multi-step planning workflows
- 🤖 **Agent Output**: The agent's response to your message
- 🔧 **Tools Used**: Which backend tools were called

## Prerequisites

1. Backend server running on `http://127.0.0.1:8000`
2. Python packages: `requests`

```bash
pip install requests
```

## Example Chat Session

```
💬 You: Add a $25 transaction to my play jar for a movie
🤔 Processing your message...

🤖 Agent: I've successfully added a $25 transaction to your play jar for the movie.
   └── Agents involved: orchestrator, jar
   └── Tools used: route_to_jar_manager

💬 You: What's my play jar balance now?
🤔 Processing your message...

🤖 Agent: Your play jar currently has a balance of $75.50.
   └── Tools used: route_to_jar_manager

💬 You: status
📊 Current Chat Session Status:
🔓 No Agent Lock
📋 No Active Plan Stage
👤 User: interactive_user_1737150000
```

## Testing Scenarios

The comprehensive tests cover:
- User registration and authentication
- Default jar verification (6 jars auto-created)
- Transaction lifecycle (create, verify balance impact, delete, verify refund)
- Fee filtering and due date calculations
- Plan status filtering
- Chat message processing with ConversationTurnInDB validation
- Conversation history retrieval

## Troubleshooting

- **Connection errors**: Ensure backend server is running on port 8000
- **Authentication failures**: Tests create unique users with timestamps
- **Response format errors**: Tests validate the new ConversationTurnInDB format
- **Import errors**: Run scripts from the frontend directory
