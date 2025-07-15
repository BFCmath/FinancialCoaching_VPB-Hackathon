# Fee Manager Agent (Backend Migration)

**Status**: ✅ ASYNC MIGRATION COMPLETED

## Async Migration Status
- ✅ All 4 async tools use direct service calls (FeeService methods)
- ✅ 1 sync tool appropriately remains sync (request_clarification - returns string only)
- ✅ inspect.iscoroutinefunction() check added to main.py
- ✅ Direct FeeService integration for all operations
- ✅ Proper async/await patterns throughout

The Fee Manager Agent is a specialized agent responsible for handling recurring financial commitments like subscriptions and bills. **Successfully migrated from lab to backend** with full database integration while preserving the intentional **direct flow pattern** for efficient fee operations.

## Core Features

- **Direct Tool Execution**: Single tool call per request, returning tool results directly without LLM wrapping (intentional design vs. Classifier's ReAct pattern).
- **Backend Database Integration**: Full MongoDB async integration while maintaining exact lab interface compatibility.
- **Smart Follow-up**: Uses conversation history for context in follow-ups, integrated with backend conversation models.
- **Natural Language Understanding**: Parses user requests to manage fees (e.g., "create a monthly $15.99 netflix fee").
- **Advanced Scheduling**: Supports daily, weekly, and monthly recurrence patterns with specific details.
- **Jar Integration**: Automatically determines appropriate jars for fees based on user's jar configuration.
- **Service Adapter Pattern**: Uses FeeServiceAdapter to maintain sync tool interfaces while supporting async database operations.
- **Full CRUD Operations**: Complete set of tools to **C**reate, **R**ead (List), **U**pdate (Adjust), and **D**elete fees with database persistence.

## How it Works (Backend Integration)

The Fee Manager uses a streamlined, single-pass approach **by design** (contrasting with Classifier's ReAct multi-turn pattern):

1. **Database Context Setup**
   - Async database connection (MongoDB with Motor driver)
   - Service adapter configuration for sync/async compatibility
   - User-specific context injection

2. **Context Gathering**
   - Retrieves existing fees and available jars from database
   - For follow-ups, includes relevant fee-related conversation history
   - Async prompt building with database data

3. **Tool Selection & Execution**
   - LLM analyzes request and available tools
   - Chooses ONE appropriate tool to execute (intentional direct flow)
   - Tools use service adapters to interact with database
   - Agent always returns the tool's result directly

4. **Follow-up Handling**
   - Only `request_clarification` tool can trigger follow-ups
   - Previous fee-related conversations feed into follow-up context
   - Agent focuses on essential clarifications (amount, schedule) without re-asking about jars

## Agent Components (Backend Migration)

- `main.py`: Core logic implementing direct tool execution with async database context
- `prompt.py`: System prompt with async database integration and conversation history
- `tools.py`: Tool definitions using backend service adapters for database operations
- `interface.py`: Clean orchestrator interface with database context injection
- `config.py`: Configuration management using backend settings infrastructure
- `README.md`: This documentation

## Backend Architecture

The migrated Fee Manager follows the established backend pattern:

```text
┌─────────────────────────────────────────────────────────────┐
│                    API Layer                                │
│  (FastAPI endpoints with database context injection)       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Fee Manager Agent                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  FeeManager(db, user_id)                           │    │
│  │  └─ configure_fee_services(db, user_id)           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Service Adapter Layer                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  FeeServiceAdapter                                 │    │
│  │  └─ Sync interface for tools                      │    │
│  │  └─ Async database operations                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                MongoDB Database                            │
│     (AsyncIOMotorDatabase with user_id context)           │
└─────────────────────────────────────────────────────────────┘
```

## Configuration (Backend Environment)

The agent uses the backend configuration system integrated with the main application settings. Configuration is handled through:

- **Backend Settings**: Uses `backend.core.config.settings` for centralized configuration
- **Base Agent Config**: Inherits from `backend.agents.base_config.BaseAgentConfig`
- **Environment Variables**: Loaded through the main backend environment system

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

## Usage (Backend Integration)

### API Integration

The Fee Manager is integrated into the backend API system:

```python
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.agents.fee.interface import FeeManagerInterface
from backend.models.conversation import ConversationTurnInDB

# Initialize with database context
fee_interface = FeeManagerInterface()

# Process request with async database context
result = await fee_interface.process_task(
    task="Cancel my gym membership subscription",
    db=database,  # AsyncIOMotorDatabase instance
    user_id="user123",
    conversation_history=conversation_turns  # List[ConversationTurnInDB]
)

# Tool result and follow-up status
print(f"Response: {result['response']}")
print(f"Needs follow-up: {result['requires_follow_up']}")
```

### Direct Service Usage

For advanced use cases, you can use the service layer directly:

```python
from backend.services.financial_services import get_fee_service

# Get configured service
fee_service = get_fee_service()

# Direct service calls (after configure_fee_services)
fee_service.create_recurring_fee(
    amount=15.99,
    jar_name="Entertainment", 
    fee_name="Netflix",
    schedule_pattern="monthly"
)
```

---

## Migration Status: ✅ COMPLETE

This Fee Manager has been **successfully migrated** from the lab environment to the backend system:

- ✅ **Direct Flow Preserved**: Intentional single-tool execution pattern maintained
- ✅ **Database Integration**: Full async MongoDB integration with Motor driver
- ✅ **Service Adapters**: Sync tool interfaces with async database operations
- ✅ **Conversation Context**: Backend conversation models integrated
- ✅ **Configuration**: Backend settings system integration
- ✅ **Interface Compatibility**: Exact lab tool interface preservation

**Design Philosophy**: The Fee Manager uses a **direct flow pattern** (vs. Classifier's ReAct pattern) because fee operations are typically straightforward and don't require multi-step reasoning. This design choice optimizes for efficiency and clarity in fee management scenarios.
 