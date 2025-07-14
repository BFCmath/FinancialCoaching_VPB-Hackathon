# Transaction Classifier Agent 🏷️

A ReAct-based intelligent transaction classifier that categorizes user expenses into appropriate budget jars using proactive information gathering and confidence-based decision making.

## Overview

The Transaction Classifier Agent uses the ReAct (Reason-Act-Observe) framework to intelligently classify transactions by:
- **Reasoning** through user input to identify missing information
- **Acting** by calling tools to gather context or perform classifications  
- **Observing** the results and iterating until a final decision is reached

## Features

### 🧠 Intelligent Classification
- **Multi-language support**: Handles both English and Vietnamese naturally
- **Context-aware**: Uses transaction history to infer missing details
- **Confidence scoring**: Provides transparency in classification certainty
- **Multi-transaction support**: Can process multiple transactions in a single request

### 🔍 Proactive Information Gathering
- **Historical analysis**: Fetches past transactions to resolve ambiguity
- **Pattern recognition**: Identifies spending patterns (requires 10+ exact matches)
- **Smart inference**: Estimates amounts based on historical data
- **Jar matching**: Maps expenses to appropriate budget categories

### ⚙️ ReAct Framework Implementation
- **Iterative processing**: Maximum 5 reasoning loops for complex queries
- **Tool-based actions**: Uses specialized tools for different operations
- **Follow-up handling**: Manages conversation continuity for clarifications
- **Error handling**: Graceful fallbacks for edge cases

## Architecture

### Core Components

```
classifier/
├── main.py              # ReAct agent implementation
├── tools.py             # Tool definitions for LLM
├── prompt.py            # ReAct system prompts
├── interface.py         # Orchestrator interface
├── config.py            # Agent configuration
└── README.md           # This file
```

### Key Classes

#### `ReActClassifierAgent`
- Main agent implementation with ReAct framework
- Handles LLM interactions and tool execution
- Supports both sync and async operation modes
- Manages database context for full functionality

#### `ClassifierInterface`
- Standardized interface for orchestrator integration
- Provides both sync and async processing methods
- Handles database context injection
- Implements `BaseWorkerInterface` for consistency

## Tools Available

### 🔍 Information Gathering

#### `transaction_fetcher(user_query, description)`
Primary tool for gathering historical transaction data when input is ambiguous.

**Use cases:**
- Missing amount: `"coffee"` → fetch past coffee purchases
- Vague description: `"lunch"` → get recent lunch transactions  
- Amount verification: `"$50 grocery"` → confirm typical grocery amounts

**Returns:** Transaction history matching the query context

### 🎯 Final Actions

#### `add_money_to_jar_with_confidence(amount, jar_name, confidence)`
**Terminal tool** for successful transaction classification.

**Parameters:**
- `amount`: Exact monetary value (e.g., 15.50)
- `jar_name`: Target jar name (must match existing jars)
- `confidence`: Certainty level 0-100

**Confidence levels:**
- `90-100%`: ✅ High confidence with clear input
- `70-89%`: ⚠️ Moderate confidence with minor ambiguity
- `Below 70%`: ❓ Low confidence requiring verification

#### `report_no_suitable_jar(description, suggestion)`
**Terminal tool** for transactions that don't fit existing jars.

**Use cases:**
- New expense categories not covered by current jars
- One-time unusual expenses
- Categories requiring jar creation

#### `respond(pattern_found, confirm_question)`
**Terminal tool** for requesting user confirmation.

**Use cases:**
- Pattern detected but needs verification
- Multiple possible interpretations
- User confirmation required before proceeding

## Usage Examples

### Basic Classification
```python
# Direct classification with clear input
response = await classifier.process_task_async(
    task="coffee $5.50",
    conversation_history=[],
    db=db,
    user_id=user_id
)
# Result: Adds $5.50 to appropriate jar (e.g., "play" or "necessities")
```

### Ambiguous Input Handling
```python
# Missing amount - triggers information gathering
response = await classifier.process_task_async(
    task="coffee",
    conversation_history=[],
    db=db, 
    user_id=user_id
)
# Process: 
# 1. Fetches past coffee transactions
# 2. Analyzes patterns
# 3. Either infers amount or asks for confirmation
```

### Multi-transaction Processing
```python
# Multiple transactions in one request
response = await classifier.process_task_async(
    task="lunch $12, coffee $4, gas $45",
    conversation_history=[],
    db=db,
    user_id=user_id
)
# Result: Classifies each transaction to appropriate jars
```

## Integration Points

### Database Services
The classifier integrates with backend financial services:

```python
from backend.services.financial_services import configure_classifier_services

# Configure services with database context
configure_classifier_services(db, user_id)

# Services automatically handle:
# - Transaction creation and jar updates
# - Historical data retrieval
# - Cross-agent communication
```

### Orchestrator Integration
```python
from backend.agents.classifier.interface import get_agent_interface

# Create interface with database context
classifier = get_agent_interface(db, user_id)

# Process task through standard interface
result = await classifier.process_task_async(task, history)
```

## Configuration

### Environment Variables
```python
# config.py settings
MODEL_NAME = "gemini-2.0-flash-exp"
GOOGLE_API_KEY = "your-api-key"
TEMPERATURE = 0.1
MAX_REACT_ITERATIONS = 5
DEBUG_MODE = False
VERBOSE_LOGGING = True
```

### ReAct Behavior
- **Maximum iterations**: 5 reasoning loops to prevent infinite cycles
- **Tool timeout**: Each tool call has reasonable timeout limits
- **Fallback prompts**: Basic classification when database unavailable
- **Error recovery**: Graceful handling of service failures

## Error Handling

### Common Scenarios
1. **No suitable jar found**: Uses `report_no_suitable_jar` with suggestions
2. **Service unavailable**: Falls back to basic classification
3. **Invalid input**: Requests clarification through `respond` tool
4. **Database errors**: Provides fallback responses with reduced functionality

### Debugging
Enable debug mode for detailed logging:
```python
config.debug_mode = True
# Outputs:
# 🔍 Processing query: coffee
# 🧠 System prompt length: 1243 chars  
# 🔄 ReAct Iteration 1/5
# 📞 Calling Tool: transaction_fetcher with args: {...}
```

## Best Practices

### Prompt Engineering
- **Clear task description**: Always specify the classification goal
- **Context provision**: Include relevant transaction history
- **Jar information**: Ensure current jar definitions are available
- **Conversation continuity**: Pass filtered agent history for context

### Service Configuration
- **Early initialization**: Configure services before first tool call
- **Database context**: Always provide valid database connection
- **Error boundaries**: Wrap classifier calls in try-catch blocks
- **Async handling**: Use async methods for full functionality

### Performance Optimization
- **History limiting**: Pass only relevant conversation history
- **Caching**: Services cache frequently accessed data
- **Batch processing**: Handle multiple transactions efficiently
- **Tool selection**: Minimize unnecessary information gathering

## Testing

### Unit Tests
```bash
# Test individual components
python -m pytest backend/agents/classifier/tests/

# Test tools in isolation
python -c "from backend.agents.classifier.tools import get_all_classifier_tools; print('Tools loaded')"

# Test prompt generation
python -c "from backend.agents.classifier.prompt import build_react_classifier_prompt; print('Prompt builder ready')"
```

### Integration Tests
```python
# Test with mock database
async def test_classifier_integration():
    classifier = ReActClassifierAgent(mock_db, "test_user")
    result = await classifier.process_request("coffee $5")
    assert "✅" in result[0]  # Success indicator
```

## Troubleshooting

### Common Issues

**Import errors**: Ensure all backend services are properly installed
```bash
cd vpbank_financial_coach_backend
pip install -r requirements.txt
```

**Service not configured**: Call `configure_classifier_services()` before tool usage
```python
from backend.services.financial_services import configure_classifier_services
configure_classifier_services(db, user_id)
```

**Async/sync issues**: Use appropriate method based on context
```python
# In async context
result = await classifier.process_task_async(task, history, db, user_id)

# In sync context  
result = classifier.process_task(task, history)
```

**Database connectivity**: Verify database connection and user permissions
```python
# Test database access
jars = await get_all_jars_for_user(db, user_id)
print(f"Found {len(jars)} jars for user")
```

## Future Enhancements

- **Machine learning integration**: Pattern recognition with ML models
- **Natural language understanding**: Enhanced parsing of complex queries
- **Multi-currency support**: Handle different currency formats
- **Spending insights**: Provide analytics alongside classification
- **Batch import**: Process multiple transactions from files/APIs

## Dependencies

### Core Requirements
- `langchain-google-genai`: LLM integration
- `motor`: MongoDB async driver  
- `pydantic`: Data validation
- `asyncio`: Async operation support

### Backend Integration
- `backend.services.financial_services`: Service layer integration
- `backend.models`: Database model definitions
- `backend.utils.db_utils`: Database utilities
- `backend.agents.base_worker`: Agent interface standard

---

For questions or issues, refer to the main project documentation or contact the development team.
    -   *User Input: "lunch"*
    -   *Action: `transaction_fetcher(user_query="past lunch transactions")`*
3.  **Observe**: The agent analyzes the output from the tool. The `transaction_fetcher` might return that past lunches cost between $12 and $18.
4.  **Repeat or Finalize**: With this new information, the agent reasons again. It now has an inferred amount ($15) and can proceed. It calls a **Final Action Tool** like `add_money_to_jar_with_confidence` to complete the task.

### Handling Ambiguity: Asking for Clarification

When the agent cannot find or infer the necessary information to classify a transaction, it will directly ask the user for clarification. This is treated as a **Final Action**.

1.  **Reason**: The agent determines that information like the transaction amount or a specific jar is missing and cannot be found in the user's history.
2.  **Act (Final Action)**: It calls the `respond` tool. This tool formats a question for the user (e.g., "How much did you spend on coffee?") and might suggest a possible classification pattern it found.
3.  **Terminate**: The `respond` tool is a "Final Action," meaning the agent's turn ends here. It returns the clarifying question to the Orchestrator along with `requires_follow_up: True`.
4.  **Orchestrator's Role**: The Orchestrator presents the question to the user. When the user replies, the Orchestrator will call the `classifier` agent again, providing the user's original request, the agent's question, and the user's new answer as part of the conversation history.
5.  **Re-evaluate**: With the new, richer context in the conversation history, the agent can now successfully classify the transaction in the next turn.

## Agent Components

-   `main.py`: Contains the core agent logic, including the `ReActClassifierAgent` class and the main `process_task` function which handles the ReAct loop and conversation history.
-   `prompt.py`: Defines the master system prompt. Critically, it's designed to dynamically include the **current conversation history**, which gives the agent the context it needs to understand follow-up answers.
-   `tools.py`: Defines the functions (tools) the agent can call. This includes tools for information gathering (`transaction_fetcher`) and final actions (`add_money_to_jar_with_confidence`, `respond`). The `respond` tool is a final action used to ask the user for more information.
-   `interface.py`: Provides a clean, high-level `ClassifierInterface` for the Orchestrator to use.
-   `config.py`: Manages agent configuration, loading settings from an `.env` file.
-   `test.py`: An interactive command-line script for testing the agent in isolation.
-   `env.example`: An example environment file showing the required configuration variables.

## Configuration

The agent requires a `.env` file in the same directory (`/agents/classifier`) with the following variables:

```
# Gemini API Key (required)
GOOGLE_API_KEY=your_gemini_api_key_here

# Model settings
MODEL_NAME=gemini-2.5-flash-lite-preview-06-17
LLM_TEMPERATURE=0.1

# Agent settings
DEBUG_MODE=false
MAX_REACT_ITERATIONS=5
```

## Usage

### Programmatic Usage

To use the classifier from another part of the system (e.g., the Orchestrator), import and use the `get_agent_interface` factory function.

```python
from agents.classifier.interface import get_agent_interface
from utils import get_conversation_history

# Initialize the agent interface
classifier_interface = get_agent_interface()

# Get the current conversation history
history = get_conversation_history()

# Process a transaction
# The agent now returns a dictionary with the response and a follow-up flag
result_dict = classifier_interface.process_task(task="went out for coffee", conversation_history=history)

print(result_dict["response"])

if result_dict["requires_follow_up"]:
    print("Agent is waiting for more input.")
```

### Interactive Testing

An interactive test script is provided to chat directly with the agent.

1.  Make sure you have a valid `.env` file in the `agents/classifier/` directory.
2.  From the `full_multi_agent` directory, run the following command:

```bash
python -m agents.classifier.test
```

This will start a session where you can input transactions and see the agent's live responses.

---
This README provides a comprehensive guide to the `classifier` agent. 