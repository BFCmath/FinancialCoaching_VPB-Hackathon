# Budget Advisor Agent

The Budget Advisor is a sophisticated agent that acts as a financial consultant. It uses a **ReAct (Reason-Act-Observe)** framework to analyze a user's financial situation, understand their goals, and create actionable savings and budget plans. It is the primary agent for strategic financial planning.

## Core Features

-   **ReAct Framework**: Intelligently gathers information before acting. It can query transaction history and check budget jar allocations to form a complete picture of the user's finances.
-   **Conversation History**: Utilizes conversation history to maintain context across multiple interactions, allowing for follow-up questions and more personalized advice.
-   **Multi-Agent Communication**: Can call the `transaction_fetcher` to get detailed spending data, demonstrating cross-agent coordination.
-   **Data-Driven Advice**: Bases its recommendations on actual user data, not just generic advice.
-   **Plan Management**: Can create, adjust, and retrieve financial plans.
-   **Conversation Lock**: Can ask clarifying questions and "lock" the conversation to itself, ensuring it gets the information it needs before proceeding.

## How it Works: The ReAct Flow

The agent's intelligence comes from its multi-step reasoning process.

1.  **Reason**: The agent analyzes the user's request (e.g., "help me save for a car") and the conversation history. It determines what information it's missing.
2.  **Act**: It calls the necessary tools to gather data. This usually involves:
    -   `transaction_fetcher`: To analyze spending habits.
    -   `get_jar`: To understand the current budget structure.
    -   `get_plan`: To see if a relevant plan already exists.
3.  **Observe**: It reviews the data returned from the tools.
4.  **Repeat or Finalize**: The agent synthesizes the information. It might reason that it has enough data to create a plan, or it might need to ask the user a clarifying question.
5.  **Respond**: The loop terminates when the agent calls the `respond` tool. This can either provide a complete plan and advice or ask a follow-up question to the user.

## Agent Components

-   `main.py`: Contains the `BudgetAdvisorAgent` class, which implements the ReAct loop and conversation logging.
-   `prompt.py`: Defines the master system prompt that instructs the LLM on its role, the ReAct framework, and how to use its tools.
-   `tools.py`: Defines the agent's capabilities, including `transaction_fetcher`, `get_jar`, `create_plan`, and the final `respond` action.
-   `interface.py`: Provides a standardized `BudgetAdvisorAgentInterface` for the Orchestrator.
-   `config.py`: Manages all agent configuration, loaded from the `.env` file.
-   `test.py`: An interactive script for testing the agent directly.
-   `env.example`: Details the required environment variables.

## Configuration

The agent requires a `.env` file in the `/agents/plan` directory. See `env.example` for a full list of variables. The most important is:

```
# Required: Google AI API Key for Gemini LLM
GOOGLE_API_KEY=your_google_api_key_here

# ReAct Framework Configuration
MAX_REACT_ITERATIONS=6
MAX_MEMORY_TURNS=20
```

## Usage

### Programmatic Usage

The agent is designed to be called by an orchestrator via its interface.

```python
from agents.plan.interface import get_agent_interface
from utils import get_conversation_history

# Get an instance of the agent
agent_interface = get_agent_interface()

# Get conversation history for context
history = get_conversation_history()

# Process a task
result = agent_interface.process_task("I want to start saving for retirement.", history)
print(result)
```

### Interactive Testing

You can chat directly with the agent for testing purposes.

1.  Ensure you have a valid `.env` file in the `agents/plan/` directory.
2.  From the `full_multi_agent` directory, run the test script:

```bash
python -m agents.plan.test
```

---
This README provides a comprehensive guide to the `plan` (Budget Advisor) agent. 