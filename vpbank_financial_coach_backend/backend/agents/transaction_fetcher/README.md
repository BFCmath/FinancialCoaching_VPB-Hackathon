# Transaction Fetcher Agent

## Overview

The Transaction Fetcher Agent is a specialized, stateless data retrieval service for transaction history. It intelligently selects and executes filtering tools based on query complexity, returning raw transaction data without analysis or interpretation. This agent serves as a backend for other agents (e.g., Transaction Classifier, Plan Agent) and supports natural language queries, including Vietnamese.

It uses a direct flow: Analyze query → Select one tool → Execute via service layer → Return data.

## Core Features

- **Intelligent Tool Selection**: Analyzes query complexity (simple 1-2 filters vs. complex 3+ filters) to choose the right tool.
- **Multi-Filter Support**: Handles jar, date, amount, time-of-day, and source filters.
- **Stateless Design**: No conversation lock or follow-up—pure retrieval per query.
- **Vietnamese Support**: Translates complex queries (e.g., "cho tôi xem thông tin ăn trưa dưới 20 đô" → lunch under $20).
- **Data Integrity**: Returns structured dicts with transactions + description; limits results (default 50) for efficiency.

## Execution Flow

1. **Receive Task**: Orchestrator/other agents call with a natural language query (e.g., "show me groceries last month under $50").
2. **Build Prompt**: Includes query + available jars (fetched fresh).
3. **LLM Invocation**: Bound to 6 tools; LLM selects one based on prompt rules.
4. **Tool Execution**: Calls service layer (e.g., `get_complex_transaction` for multi-filters).
5. **Return Result**: Dict with data (list of transactions) + description; logs to history.

No ReAct loop—single pass. Stateless, so no history usage.

## Agent Tools (`tools.py`)

6 tools for retrieval, all returning `Dict[data: List[Dict], description: str]`:

- `get_jar_transactions`: By jar/category.
- `get_time_period_transactions`: By date range (supports relatives like "last_month").
- `get_amount_range_transactions`: By min/max amount.
- `get_hour_range_transactions`: By time-of-day (hours).
- `get_source_transactions`: By source (e.g., "vpbank_api").
- `get_complex_transaction`: For 3+ filters (e.g., jar + date + amount).

## Agent Interface (`interface.py`)

Orchestrator integration:

**Class:** `TransactionFetcherInterface`

**Primary Method:** `process_task(task: str, conversation_history: List) → Dict`

**Example Usage:**
```python
from agents.transaction_fetcher.interface import TransactionFetcherInterface

fetcher = TransactionFetcherInterface()
result = fetcher.process_task(task="show me necessities last month under $100")
print(result['response']['data'])  # List of transactions