# AI Financial Coach - Agent Documentation

This document provides a detailed explanation of each specialist agent within the `full_multi_agent` system. Each agent is designed as a modular component with a specific role, a set of tools, and a standardized interface for the orchestrator.

---

## 1. Transaction Classifier (`classifier/`)

-   **Purpose:** To analyze a user's free-text description of a transaction (e.g., "got coffee for 5 dollars") and accurately assign it to the correct budget jar (e.g., "Dining & Meals").
-   **Flow:** This agent uses a **single-pass execution model**. It builds a detailed prompt containing the user's input, the list of available jars, and recent transaction history for context. It then makes a single call to the LLM, which can return *multiple* tool calls in one response. The agent executes all of these tool calls sequentially, making it efficient for batch classifications (e.g., "coffee 5, gas 50").
-   **Tools:**
    -   `add_money_to_jar_with_confidence(amount, jar_name, confidence)`: Assigns the transaction amount to a specific jar, including a confidence score.
    -   `report_no_suitable_jar(description, suggestion)`: Used when no existing jar is a good fit.
    -   `request_more_info(question)`: Asks for clarification if the input is ambiguous.
-   **Interface:** `ClassifierAgent.process(task: str) -> str`
    -   **Input:** A string describing one or more transactions.
    -   **Output:** A string summarizing the results of the classification(s).

---

## 2. Jar Manager (`jar_test/`)

-   **Purpose:** To handle all Create, Read, Update, and Delete (CRUD) operations for the user's budget jars. It is responsible for maintaining the integrity of the budget structure, including automatically rebalancing percentages when jars are created, updated, or deleted.
-   **Flow:** This agent uses a **single-pass, multi-operation execution model**. It receives a user request, invokes the LLM with a list of powerful batch-capable tools, and executes the returned tool calls. Its strength lies in handling commands that affect multiple jars at once (e.g., "create a jar for vacation and another for emergencies").
-   **Tools:**
    -   `create_jar(name: List[str], ...)`: Creates one or more new jars.
    -   `update_jar(jar_name: List[str], ...)`: Updates one or more existing jars.
    -   `delete_jar(jar_name: List[str], ...)`: Deletes one or more jars and redistributes their allocation.
    -   `list_jars()`: Lists all current jars and their statuses.
    -   `request_clarification(question, suggestions)`: Asks for more information.
-   **Interface:** `JarManagerAgent.process(task: str) -> str`
    -   **Input:** A string describing the desired jar operation(s).
    -   **Output:** A string confirming the actions taken, including details on rebalancing.

---

## 3. Fee Manager (`fee_test/`)

-   **Purpose:** To manage recurring financial commitments like subscriptions and bills. It handles scheduling, amount, and allocation for these fees.
-   **Flow:** Similar to the Jar Manager, this agent uses a **single-pass execution model**. It builds a prompt with context about existing fees and available jars and executes the tool calls returned by the LLM.
-   **Tools:**
    -   `create_recurring_fee(...)`: Sets up a new recurring payment with a specific schedule (`daily`, `weekly`, `monthly`).
    -   `adjust_recurring_fee(...)`: Modifies an existing fee's amount, schedule, or status.
    -   `delete_recurring_fee(...)`: Deactivates a recurring fee.
    -   `list_recurring_fees()`: Shows all current recurring fees.
    -   `request_clarification(...)`: Asks for more details if the request is unclear.
-   **Interface:** `FeeManagerAgent.process(task: str) -> str`
    -   **Input:** A string describing the desired fee operation.
    -   **Output:** A string confirming the action and detailing the fee's schedule.

---

## 4. Knowledge Agent (`knowledge/`)

-   **Purpose:** To act as a financial expert and application guide. It can answer general financial questions (e.g., "What is compound interest?") or questions about the app's functionality by searching online and consulting internal documentation.
-   **Flow:** This agent uses a **ReAct (Reason-Act) framework**. It operates in a multi-step loop, "thinking" about what information it needs, using a tool to "act" and find that information, and then "observing" the result. This loop continues until it has gathered enough data to provide a complete answer, at which point it calls the special `respond` tool to exit the loop.
-   **Tools:**
    -   `search_online(query)`: Searches the web using DuckDuckGo for financial concepts.
    -   `get_application_information()`: Retrieves the entire hardcoded documentation for the app.
    -   `respond(answer)`: A terminal tool that concludes the ReAct loop and provides the final, synthesized answer to the user.
-   **Interface:** `KnowledgeAgent.process(task: str) -> str`
    -   **Input:** A question about finance or the application.
    -   **Output:** A comprehensive answer synthesized from its research.

---

## 5. Transaction Fetcher (`transaction_fetcher/`)

-   **Purpose:** A highly specialized **service agent** designed for one thing: retrieving transaction data with powerful filtering. It is not typically called directly by the orchestrator but by other agents (like the Budget Advisor) that need historical financial data.
-   **Flow:** This agent uses a **single-pass, intelligent tool-selection model**. It is given a suite of highly specific data retrieval tools and its primary job is to parse a natural language query (e.g., "show me manual play entries from last week over $30") and select the *single best tool* (`get_complex_transaction` in this case) with the correct parameters to fulfill the request.
-   **Tools:**
    -   `get_jar_transactions()`: Filters by jar.
    -   `get_time_period_transactions()`: Filters by date.
    -   `get_amount_range_transactions()`: Filters by amount.
    -   `get_hour_range_transactions()`: Filters by time of day.
    -   `get_source_transactions()`: Filters by entry method (API, manual, etc.).
    -   `get_complex_transaction()`: A powerful tool that combines all of the above filters for complex, multi-dimensional queries.
-   **Interface:** `TransactionFetcherAgent.process(task: str) -> List[Dict]`
    -   **Input:** A natural language query for transaction data.
    -   **Output:** A list of dictionaries, where each dictionary contains the raw transaction data and a description of the filters applied.

---

## 6. Budget Advisor (`plan_test/`)

-   **Purpose:** To serve as a high-level financial planner. It helps users create, adjust, and manage long-term financial plans. It acts as a sub-orchestrator, coordinating with other agents (like the Transaction Fetcher) to gather data needed for its analysis.
-   **Flow:** This agent uses a **ReAct framework with a conversation lock**. Like the Knowledge Agent, it operates in a multi-step reasoning loop. Critically, its `respond` tool can optionally ask the user a clarifying question, which sets a "lock" that routes the user's next response *directly* back to this agent, allowing for multi-turn, stateful financial consultations. It is also the only agent that logs its interactions to the central conversation history database.
-   **Tools:**
    -   `transaction_fetcher(...)`: Calls the Transaction Fetcher agent to get spending history.
    -   `get_jar(...)`: Gets jar information directly from the database.
    -   `get_plan(...)`, `create_plan(...)`, `adjust_plan(...)`: Manages financial plans via the Plan Service.
    -   `respond(summary, advice, question_ask_user)`: The terminal tool that provides the final advice and can optionally ask a follow-up question to lock the conversation.
-   **Interface:** `BudgetAdvisorAgentInterface.process_task(task: str, conversation_history: List[Dict]) -> str`
    -   **Input:** The user's planning request and the recent conversation history.
    -   **Output:** A string containing financial advice, a summary of actions, or a clarifying question.
