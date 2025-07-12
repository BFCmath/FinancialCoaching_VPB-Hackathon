# Fee Manager Agent

The Fee Manager Agent is a specialized agent responsible for handling recurring financial commitments like subscriptions and bills. It uses direct tool execution based on LLM decisions, with a focus on clear, straightforward interactions and smart follow-up handling.

## Core Features

- **Direct Tool Execution**: Single tool call per request, returning tool results directly without LLM wrapping.
- **Smart Follow-up**: Uses conversation history for context in follow-ups, similar to the classifier agent.
- **Natural Language Understanding**: Parses user requests to manage fees (e.g., "create a monthly $15.99 netflix fee").
- **Advanced Scheduling**: Supports daily, weekly, and monthly recurrence patterns with specific details.
- **Jar Integration**: Automatically determines appropriate jars for fees based on context.
- **Confidence Scoring**: Uses confidence scores for fee assignments and updates.
- **Full CRUD Operations**: Complete set of tools to **C**reate, **R**ead (List), **U**pdate (Adjust), and **D**elete fees.

## How it Works

The Fee Manager uses a streamlined, single-pass approach:

1. **Context Gathering**
   - Retrieves existing fees and available jars
   - For follow-ups, includes relevant fee-related conversation history

2. **Tool Selection**
   - LLM analyzes request and available tools
   - Chooses ONE appropriate tool to execute
   - Agent always returns the tool's result directly

3. **Follow-up Handling**
   - Only `request_clarification` tool can trigger follow-ups
   - Lock is set ONLY by `request_clarification`
   - Previous fee-related conversations feed into follow-up context
   - Agent focuses on essential clarifications (amount, schedule) without re-asking about jars

## Agent Components

- `main.py`: Core logic implementing direct tool execution and follow-up handling
- `prompt.py`: System prompt with conversation history integration for follow-ups
- `tools.py`: Tool definitions, with clear marking of which tools can trigger follow-up
- `interface.py`: Clean orchestrator interface returning direct tool results
- `config.py`: Configuration management
- `test.py`: Interactive testing with lock visualization
- `env.example`: Environment variable templates

## Configuration

The agent requires a `.env` file in the `/agents/fee` directory with the following variables:

```env
# Gemini API Key (required)
GOOGLE_API_KEY=your_gemini_api_key_here

# Model settings
MODEL_NAME=gemini-2.5-flash-lite-preview-06-17
LLM_TEMPERATURE=0.1

# Agent settings
DEBUG_MODE=false
HIGH_CONFIDENCE_THRESHOLD=80
LOW_CONFIDENCE_THRESHOLD=50
```

## Usage

### Programmatic Usage

The Fee Manager returns direct tool results without LLM wrapping:

```python
from agents.fee.interface import FeeManagerAgent

# Initialize the agent
fee_agent = FeeManagerAgent()

# Process request - returns tool result directly
result = fee_agent.process_task(
    task="Cancel my gym membership subscription",
    conversation_history=None  # Optional: needed for follow-ups
)

# Tool result and follow-up status
print(f"Response: {result['response']}")
print(f"Needs follow-up: {result['requires_follow_up']}")
```

### Interactive Testing

Test the agent with follow-up support:

1. Make sure you have a valid `.env` file in the `agents/fee/` directory
2. From the `full_multi_agent` directory, run:

```bash
python -m agents.fee.test
```

The test interface will show:
- Direct tool results
- Lock status (🔒/🔓)
- Follow-up context handling

---
This README documents the streamlined fee manager implementation.
 