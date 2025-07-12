# Transaction Classifier Agent

The Transaction Classifier is an intelligent agent designed to categorize user-provided financial transactions into predefined budget jars. It is built using a **ReAct (Reason-Act-Observe)** framework, which allows it to handle ambiguous inputs by proactively seeking missing information before making a final decision.

For example, if a user provides a vague input like "went out for lunch," the agent can use its tools to look up past lunch transactions, infer a likely cost, and then classify it, rather than immediately failing or asking for clarification.

## Core Features

-   **ReAct Framework**: Intelligently handles ambiguous queries (e.g., missing amounts or descriptions).
-   **Information Gathering**: Can query past transaction history to infer missing details.
-   **Confidence Scoring**: Reports its confidence level in the final classification.
-   **Extensible Tools**: The agent's capabilities are defined by a clear set of tools that can be expanded.
-   **Conversation Logging**: Logs all steps of its reasoning process and the final outcome to a central database.

## How it Works: The ReAct Flow

The agent operates on a "Reason-Act-Observe" cycle until it reaches a conclusion.

1.  **Reason**: The agent first analyzes the user's request. Is there enough information (e.g., a description and an amount) to classify the transaction?
2.  **Act**: If information is missing, the agent selects a tool to find it. Its primary tool is `transaction_fetcher`, which it uses to search the user's transaction history for clues.
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