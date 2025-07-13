# Multi-Agent System Architecture Overview

This document provides a detailed breakdown of the agents within the financial coaching system, their capabilities, and how they interact.

---

### Orchestrator
- **Name**: Orchestrator
- **Description**: The central routing system (the "brain"). It analyzes user requests and routes them to the appropriate worker agent. It implements a stateful "Active Agent Context" (or "Conversation Lock") pattern. If an agent needs to ask a follow-up question, it can "lock" the conversation, ensuring the user's next response is routed directly back to it.
- **Database they work with**: Manages conversation history and the "Active Agent Context" state. It does not interact with service-level databases (jars, transactions) directly.
- **Routing Logic**: Uses an LLM to classify user intent into one of its "routing" tools, which correspond to the worker agents in its `AGENT_REGISTRY`.
- **Agent Registry Keys**: `transaction_classifier`, `jar_manager`, `fee_manager`, `budget_advisor`, `knowledge_base`.
- **Interactions**: Calls the primary worker agents.

---

### Worker Agents (Called by Orchestrator)

#### 1. Transaction Classifier
- **Name**: Transaction Classifier
- **Registry Key**: `transaction_classifier`
- **Description**: Classifies user spending into the correct budget jar. Uses a ReAct loop to gather information if the request is ambiguous.
- **Database they work with**: Reads Jar data and Transaction history (via the Transaction Fetcher).
- **Internal Tools**:
    - `transaction_fetcher()`: (Information Gathering) Calls the Transaction Fetcher service agent to get historical data for inferring missing details.
    - `add_money_to_jar_with_confidence()`: (Final Action) Classifies the transaction.
    - `report_no_suitable_jar()`: (Final Action) Reports when no matching jar is found.
    - `respond()`: (Final Action) Asks the user a clarifying question when information cannot be inferred. **This is a final action and does NOT lock the conversation.** The user's answer is handled as a new turn by the Orchestrator.
- **Interactions**: Is called by the Orchestrator. Calls the Transaction Fetcher.

#### 2. Jar Manager
- **Name**: Jar Manager
- **Registry Key**: `jar_manager`
- **Description**: Manages the 6-jar budget system (create, update, delete, list).
- **Database they work with**: Reads and writes to the Jars database via the `JarService`.
- **Internal Tools**:
    - `create_jar()`, `update_jar()`, `delete_jar()`, `list_jars()`
    - `request_clarification()`: Asks the user a clarifying question. **This tool engages the Conversation Lock**, pausing its own execution and waiting for the user's next input.
- **Interactions**: Is called by the Orchestrator.

#### 3. Fee Manager
- **Name**: Fee Manager
- **Registry Key**: `fee_manager`
- **Description**: Creates and manages recurring fee schedules (e.g., subscriptions, bills).
- **Database they work with**: Reads and writes to the Recurring Fees database via the `FeeService`.
- **Internal Tools**:
    - `create_recurring_fee()`, `adjust_recurring_fee()`, `delete_recurring_fee()`, `list_recurring_fees()`
    - `request_clarification()`: Asks the user a clarifying question. **This tool engages the Conversation Lock.**
- **Interactions**: Is called by the Orchestrator.

#### 4. Plan Agent (Budget Advisor)
- **Name**: Plan Agent
- **Registry Key**: `budget_advisor` (*Note: "budget_advisor" in registry, "plan" in codebase*)
- **Description**: High-level financial planning consultant. Creates and adjusts budget plans.
- **Database they work with**: Reads and writes to Budget Plans database; reads Jars and Transaction History.
- **Internal Tools**:
    - `transaction_fetcher()`: Calls the Transaction Fetcher for spending data.
    - `get_jar()`: Reads jar data directly.
    - `get_plan()`, `create_plan()`, `adjust_plan()`: Manages financial plans.
    - `respond()`: Provides the final response or asks a clarifying question. **If a question is asked, this tool engages the Conversation Lock.**
- **Interactions**: Is called by the Orchestrator. Calls the Transaction Fetcher.

#### 5. Knowledge Base
- **Name**: Knowledge Base
- **Registry Key**: `knowledge_base`
- **Description**: Answers financial and app-related questions.
- **Database they work with**: Reads a hardcoded documentation file; uses a live web search tool.
- **Internal Tools**:
    - `search_online()`: Searches the web with DuckDuckGo.
    - `get_application_information()`: Retrieves internal app docs.
    - `respond()`: Provides the final answer. **Does not use a conversation lock.**
- **Interactions**: Is called by the Orchestrator.

---

### Service Agents (Called by other Agents)

#### 1. Transaction Fetcher
- **Name**: Transaction Fetcher
- **Description**: A specialized data retrieval service that handles complex queries for transaction history. It is NOT called by the orchestrator directly.
- **Database they work with**: Reads the Transaction history database.
- **Internal Tools**:
    - `get_jar_transactions()`, `get_time_period_transactions()`, `get_amount_range_transactions()`, `get_hour_range_transactions()`, `get_source_transactions()`, `get_complex_transaction()`
- **Interactions**: Is called by the Transaction Classifier and the Plan Agent.