# Jar Manager Agent

## Overview

The **Jar Manager Agent** is a specialized agent responsible for all Create, Read, Update, and Delete (CRUD) operations related to budget jars. It is built on the principles of T. Harv Eker's 6-Jar Money Management System but is flexible enough to allow users to create any custom jars they need.

Its core feature is the **automatic rebalancing system**. Whenever a jar's percentage allocation is created, updated, or deleted, the agent automatically and proportionally adjusts all other jars to ensure the total allocation always remains exactly 100%.

This agent is designed to handle both single-jar and complex multi-jar operations in a single, atomic transaction.

## Execution Flow

The agent operates in a straightforward, single-pass flow:

1.  **Receive Task**: The orchestrator calls the agent with a natural language task (e.g., "create a vacation jar with 10% and an emergency jar for $500").
2.  **Build Contextual Prompt**: The `main.py` script fetches all existing jars from the central database to build a rich, contextual prompt. This prompt includes the user's request, the current state of all jars (names, descriptions, allocations), and detailed instructions for the LLM.
3.  **LLM Invocation**: The prompt is sent to the Gemini LLM, which has been bound to the agent's specific toolset.
4.  **Tool Call Analysis**: The LLM analyzes the request and determines the correct tool to call (e.g., `create_jar`) and the precise arguments needed (e.g., `name=["vacation", "emergency"]`, `percent=[0.10]`, `amount=[None, 500.0]`).
5.  **Service Layer Execution**: The agent executes the tool call, which passes the arguments to the `JarManagementService` in the unified `service.py`. The service handles all business logic, including validation, data manipulation, and the crucial rebalancing calculations.
6.  **Return Result**: The `JarManagementService` returns a formatted string detailing the outcome of the operation, including a summary of any rebalancing changes. This result is passed back to the orchestrator.

## Agent Tools (`tools.py`)

The agent exposes a set of powerful, service-integrated tools to the LLM. All tools support multi-jar operations by accepting lists as arguments.

-   `create_jar(name: List[str], description: List[str], percent: List[Optional[float]], amount: List[Optional[float]], confidence: int) -> str`
    -   Creates one or more new jars. Automatically rebalances existing jars to make room for the new allocation.

-   `update_jar(jar_name: List[str], new_name: List[Optional[str]], new_description: List[Optional[str]], new_percent: List[Optional[float]], new_amount: List[Optional[float]], confidence: int) -> str`
    -   Modifies one or more existing jars. Can update name, description, and allocation. Automatically rebalances all other jars if the percentage changes.

-   `delete_jar(jar_name: List[str], reason: str) -> str`
    -   Permanently removes one or more jars. Automatically redistributes the freed-up percentage allocation among the remaining jars.

-   `list_jars() -> str`
    -   Returns a formatted string listing all current jars, their budget allocations, current balances, and descriptions.

-   `request_clarification(question: str, suggestions: Optional[str]) -> str`
    -   Allows the agent to ask the user for more information if a request is ambiguous or incomplete.

## Agent Interface (`interface.py`)

The orchestrator interacts with the Jar Manager through a clean interface class.

**Class:** `JarManagerAgent`

**Primary Method:** `process(task: str) -> str`
This is the main entry point for the orchestrator. It takes the user's natural language request as a string and returns the formatted result.

**Example Usage:**
```python
from agents.jar_test.interface import JarManagerAgent

jar_agent = JarManagerAgent()
result = jar_agent.process(task="create a new 'car fund' jar with 5%")
print(result)
```

## Interactive Testing (`test.py`)

The agent includes an interactive test script that allows you to chat directly with it from the command line. This is useful for debugging and seeing the agent's raw output.

**To run the test script:**

1.  Navigate to the `full_multi_agent` directory in your terminal:
    ```bash
    cd agent-testing-lab/full_multi_agent
    ```

2.  Run the test script as a module:
    ```bash
    python -m agents.jar_test.test
    ```

3.  You will be prompted to enter your requests. Type `exit` or `quit` to end the session. 