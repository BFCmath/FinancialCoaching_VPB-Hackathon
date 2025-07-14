# README.md: VPBank AI Financial Coach Backend Services

This document provides an exhaustive description of all files in the `backend/services` folder. The services layer implements the core business logic for the VPBank AI Financial Coach application, handling budgeting, transactions, recurring fees, plans, conversations, and more. It integrates with the database (MongoDB via Motor) and ensures async operations for efficiency.

The architecture is modular:
- **Core Services**: Foundational utilities like calculations and user settings.
- **Domain Services**: Specific to features like jars, transactions, fees, plans.
- **Support Services**: Confidence handling, inter-agent communication, knowledge base.
- **Integration Services**: Orchestrator, adapters for legacy/lab compatibility.
- **Security**: Authentication utilities.

All services are designed to be user-scoped where applicable, using `user_id` and `db` parameters. Methods involving database access are asynchronous.

## core_services.py

**Purpose**: Contains foundational services for user settings and financial calculations. This file includes all utility functions from the lab's `utils.py` related to calculations, validation, database stats, export, initialization, and reset. It serves as a dependency for other services.

**Key Components**:
- **UserSettingsService** (class): Manages user-specific settings like total income.
  - `get_user_total_income(db, user_id) -> float`: Retrieves user's total income, defaults to 5000.0.
  - `update_user_total_income(db, user_id, new_income) -> UserSettingsInDB`: Updates total income.
- **CalculationService** (class): Handles all financial computations and validations.
  - `format_currency(amount) -> str`: Formats amount as "$X,XXX.XX".
  - `format_percentage(percent) -> str`: Formats as "XX.X%".
  - `validate_percentage_range(percent) -> bool`: Checks if 0.0 <= percent <= 1.0.
  - `validate_positive_amount(amount) -> bool`: Checks if amount > 0.
  - `calculate_percent_from_amount(db, user_id, amount) -> float`: Converts amount to percent of total income.
  - `calculate_amount_from_percent(db, user_id, percent) -> float`: Converts percent to amount based on total income.
  - `calculate_jar_total_allocation(db, user_id) -> float`: Sums percentages of all user jars.
  - `validate_jar_percentages(db, user_id) -> Tuple[bool, float]`: Checks if total allocation <= 100%.
  - `calculate_jar_spending_total(db, user_id, jar_name) -> float`: Sums transaction amounts for a jar.
  - `get_database_stats(db, user_id) -> Dict[str, Any]`: Comprehensive stats on jars, transactions, fees, plans, conversations.
  - `export_database_json(db, user_id) -> str`: Exports all user data as JSON string.
  - `initialize_default_data(db, user_id) -> None`: Sets up default 6-jar system and sample data.
  - `reset_database(db, user_id) -> None`: Resets to initial state by calling initialize.

**Dependencies**: Relies on `db_utils` for database operations and models like `jar`, `transaction`, etc.
**Usage**: Used by all domain services for calculations and data validation.

## jar_service.py

**Purpose**: Manages budget jars based on T. Harv Eker's 6-jar system. Covers all jar operations from lab's `utils.py` and `service.py`, including creation, update, deletion, listing, finding, validation, and rebalancing. Supports multi-jar operations with atomic validation.

**Key Components**:
- **JarManagementService** (class): Main service for jar operations.
  - `create_jar(db, user_id, name, description, percent=None, amount=None, confidence=85) -> str`: Creates jars with rebalancing and confidence formatting.
  - `update_jar(db, user_id, jar_name, new_name=None, new_description=None, new_percent=None, new_amount=None, confidence=85) -> str`: Updates jars with rebalancing.
  - `delete_jar(db, user_id, jar_name, reason) -> str`: Deletes jars with redistribution.
  - `list_jars(db, user_id) -> str`: Formatted list of all jars with summaries.
  - `find_jar_by_keywords(db, user_id, keywords) -> Optional[JarInDB]`: Searches jars by name/description.
  - `validate_jar_name(db, user_id, name, exclude_current=None) -> Tuple[bool, str]`: Checks name validity and uniqueness.
  - `request_clarification(question, suggestions=None) -> str`: Formats clarification requests.
  - `validate_jar_data(db, user_id, jar_data) -> Tuple[bool, List[str]]`: Validates jar creation data.
  - Private methods: `_rebalance_after_creation`, `_rebalance_after_update`, `_redistribute_deleted_percentage` for allocation adjustments.

**Dependencies**: Uses `CalculationService` for percent/amount conversions, `ConfidenceService` for response formatting, `db_utils` for CRUD.
**Usage**: Called by agents/orchestrator for jar management; rebalancing ensures total allocation ~100%.

## transaction_service.py

**Purpose**: Handles transaction creation, validation, and advanced querying. Combines lab's classifier and fetcher functionalities, covering all operations from `utils.py` and `service.py`.

**Key Components**:
- **TransactionService** (class): Management operations.
  - `save_transaction(db, user_id, transaction_data) -> TransactionInDB`: Saves validated transaction.
  - `get_all_transactions(db, user_id) -> List[TransactionInDB]`: Retrieves all user transactions.
  - `get_transactions_by_jar(db, user_id, jar_name) -> List[TransactionInDB]`: By jar.
  - `get_transactions_by_date_range(db, user_id, start_date, end_date=None) -> List[TransactionInDB]`: By date.
  - `get_transactions_by_amount_range(db, user_id, min_amount=None, max_amount=None) -> List[TransactionInDB]`: By amount.
  - `get_transactions_by_source(db, user_id, source) -> List[TransactionInDB]`: By source.
  - `calculate_jar_spending_total(db, user_id, jar_name) -> float`: Sum for jar.
  - `add_money_to_jar_with_confidence(db, user_id, amount, jar_name, confidence) -> str`: Adds transaction with jar update and confidence.
  - `report_no_suitable_jar(description, suggestion) -> str`: No-match report.
  - `request_more_info(question) -> str`: Clarification request.
  - `validate_transaction_data(db, user_id, transaction_data) -> Tuple[bool, List[str]]`: Data validation.
- **TransactionQueryService** (class): Query tools.
  - `get_jar_transactions(db, user_id, jar_name=None, limit=50, description="") -> Dict`: Filtered by jar.
  - `get_time_period_transactions(...) -> Dict`: By date.
  - `get_amount_range_transactions(...) -> Dict`: By amount.
  - `get_hour_range_transactions(...) -> Dict`: By time of day.
  - `get_source_transactions(...) -> Dict`: By source.
  - `get_complex_transaction(...) -> Dict`: Multi-filter query.
  - Private: `_parse_flexible_date`, `_time_in_range`.

**Dependencies**: `CalculationService` for formatting/validation, `ConfidenceService` for responses, `db_utils` for CRUD.
**Usage**: Used for expense tracking, categorization, and analysis.

## fee_service.py

**Purpose**: Manages recurring fees/subscriptions. Covers all lab operations for fees.

**Key Components**:
- **FeeManagementService** (class):
  - `save_recurring_fee(db, user_id, fee_data) -> FeeInDB`: Saves fee.
  - `get_recurring_fee(db, user_id, fee_name) -> Optional[FeeInDB]`: By name.
  - `get_all_recurring_fees(db, user_id) -> List[FeeInDB]`: All fees.
  - `get_active_recurring_fees(db, user_id) -> List[FeeInDB]`: Active only.
  - `delete_recurring_fee(db, user_id, fee_name) -> bool`: Deletes fee.
  - `calculate_next_fee_occurrence(pattern_type, pattern_details, from_date=None) -> datetime`: Next due date.
  - `get_fees_due_today(db, user_id) -> List[FeeInDB]`: Due today.
  - `create_recurring_fee(db, user_id, name, amount, description, pattern_type, pattern_details, target_jar, confidence=85) -> str`: Creates with confidence.
  - `adjust_recurring_fee(db, user_id, fee_name, ...) -> str`: Updates with confidence.
  - `delete_recurring_fee(db, user_id, fee_name, reason) -> str`: Deletes with response.
  - `list_recurring_fees(db, user_id, active_only=True, target_jar=None) -> str`: Formatted list.
  - Private: `_validate_fee_name`, `_format_pattern_description`.

**Dependencies**: `CalculationService` for formatting/validation, `ConfidenceService` for responses, `db_utils` for CRUD.
**Usage**: For subscription tracking and recurring expense management.

## plan_service.py

**Purpose**: Manages budget plans and goals. Covers all lab operations for plans.

**Key Components**:
- **PlanManagementService** (class):
  - `save_budget_plan(db, user_id, plan_data) -> BudgetPlanInDB`: Saves plan.
  - `get_budget_plan(db, user_id, plan_name) -> Optional[BudgetPlanInDB]`: By name.
  - `get_all_budget_plans(db, user_id) -> List[BudgetPlanInDB]`: All plans.
  - `get_budget_plans_by_status(db, user_id, status) -> List[BudgetPlanInDB]`: By status.
  - `delete_budget_plan(db, user_id, plan_name) -> bool`: Deletes plan.
  - `create_plan(db, user_id, name, description, status="active", jar_propose_adjust_details=None, confidence=85) -> str`: Creates with confidence.
  - `adjust_plan(db, user_id, name, description=None, status=None, jar_propose_adjust_details=None, confidence=85) -> str`: Updates with confidence.
  - `get_plan(db, user_id, status="active", description="") -> Dict`: Retrieves by status.
  - `delete_plan(db, user_id, plan_name, reason="") -> str`: Deletes with response.

**Dependencies**: `ConfidenceService` for responses, `db_utils` for CRUD.
**Usage**: For goal setting and progress tracking.

## conversation_service.py

**Purpose**: Manages user conversations and agent locks. Covers all lab conversation operations.

**Key Components**:
- **ConversationService** (class, user-scoped):
  - `add_conversation_turn(user_input, agent_output, agent_list=None, tool_call_list=None) -> None`: Adds turn with limit.
  - `get_conversation_history(limit=None) -> List[ConversationTurnInDB]`: Recent history.
  - `get_agent_specific_history(agent_name, max_turns=10) -> List[ConversationTurnInDB]`: Agent-specific.
  - `clear_conversation_history() -> None`: Clears all.
  - `get_conversation_context_string(limit=5) -> str`: Formatted string.
  - `parse_confidence_response(response, agent_name) -> Tuple[str, bool]`: Checks for follow-up.
  - `check_conversation_lock() -> Optional[str]`: Current lock.
  - `lock_conversation_to_agent(agent_name) -> None`: Sets lock.
  - `release_conversation_lock() -> None`: Clears lock.

**Dependencies**: `db_utils` for CRUD, config for MAX_MEMORY_TURNS.
**Usage**: For maintaining chat history and multi-turn interactions.

## confidence_service.py

**Purpose**: Handles confidence levels and user validations. Covers all lab confidence functions.

**Key Components**:
- **ConfidenceService** (class):
  - `format_confidence_response(result, confidence) -> str`: Formats with emoji.
  - `request_clarification(question, suggestions=None) -> str`: Clarification message.
  - `determine_confidence_level(confidence) -> str`: Level category.
  - `should_ask_for_confirmation(confidence, threshold=70) -> bool`: Confirmation check.
  - `generate_confidence_explanation(confidence, factors=None) -> str`: Explanation text.
  - `validate_user_intent(user_input, expected_actions) -> Tuple[bool, str, int]`: Intent validation.
  - `suggest_alternatives(failed_input, available_options) -> str`: Suggestion message.

**Dependencies**: None (stateless).
**Usage**: Used across services for response formatting and validation.

## communication_service.py

**Purpose**: Facilitates inter-agent communication. Covers all lab communication functions.

**Key Components**:
- **AgentCommunicationService** (class):
  - `call_transaction_fetcher(db, user_id, user_query, description="") -> Dict`: Calls transaction query.
  - `call_jar_agent(db, user_id, jar_name=None, description="") -> Dict`: Calls jar service.
  - `format_cross_agent_request(target_agent, request) -> Dict`: Formats request.
  - `handle_cross_agent_response(response) -> Dict`: Processes response.
  - `coordinate_multi_agent_task(db, user_id, task_description, required_agents) -> Dict`: Coordinates multiple agents.

**Dependencies**: `TransactionQueryService`, `JarManagementService`.
**Usage**: For agent collaboration in orchestrator.

## financial_services.py

**Purpose**: Unified entry point providing factories for all services.

**Key Components**:
- **FinancialServices** (class):
  - Factory methods like `get_jar_service()`, `get_transaction_service()`, etc.
  - `get_all_services(db, user_id) -> Dict`: Dictionary of instantiated services.

**Dependencies**: Imports all other services.
**Usage**: Central import point for accessing services.

## adapters.py

**Purpose**: Compatibility layer for lab sync interfaces with backend async services.

**Key Components**:
- **BaseAdapter** (class): Sync/async bridge using futures.
- **ClassifierAdapter**, **FeeAdapter**, **JarAdapter** (classes): Specific adapters with lab methods.
- Factory functions: `get_classifier_adapter(db, user_id)`, etc.

**Dependencies**: Domain services like TransactionService, etc.
**Usage**: For legacy/lab tool compatibility without async changes.

## knowledge_service.py

**Purpose**: Provides app knowledge and help. Covers lab knowledge functions.

**Key Components**:
- **KnowledgeService** (class):
  - `get_application_information(db, user_id, description="") -> Dict`: App info with user context.
  - `respond(answer, description="") -> Dict`: Final response format.
  - `search_help(db, user_id, query) -> str`: Query-based help.
  - `get_help_information(query="") -> Dict`: Categorized help.

**Dependencies**: `db_utils` for context.
**Usage**: For informational queries and help commands.

## orchestrator_service.py

**Purpose**: Manages message processing and context for orchestrator.

**Key Components**:
- **OrchestratorService** (class, user-scoped):
  - `process_chat_message(message, context=None) -> Dict`: Processes user message.
  - Private: `_load_context`, `_format_response`, `_handle_error`.
  - `get_user_stats() -> Dict`: User statistics.
  - `export_user_data() -> str`: JSON export.

**Dependencies**: `ConversationService`, `FinancialServices`, orchestrator agent.
**Usage**: Main interface for chat processing.

## security.py

**Purpose**: Handles password hashing and JWT tokens.

**Key Components**:
- `verify_password(plain_password, hashed_password) -> bool`: Verifies password.
- `get_password_hash(password) -> str`: Hashes password.
- `create_access_token(data, expires_delta=None) -> str`: Creates JWT.
- `decode_access_token(token) -> Optional[Dict]`: Decodes JWT.

**Dependencies**: `passlib`, `jose`, config settings.
**Usage**: For authentication and authorization.