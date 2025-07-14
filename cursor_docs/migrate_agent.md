# Agent Migration Guide: Lab to Backend 🔄

This document outlines the systematic approach for migrating agents from the lab environment to the production backend with full database integration.

## Overview

The migration process involves adapting agents that were designed to work with in-memory storage (lab environment) to work with the async MongoDB backend while maintaining the exact same tool interfaces that the agents expect.

## ✅ Migration Status

### Completed Migrations:
1. **Classifier Agent** - Successfully migrated with full database integration
2. **Fee Manager Agent** - Successfully migrated following the established pattern

### Pattern Validated:
The migration approach has been proven successful across multiple agent types, maintaining exact tool interface compatibility while adding backend database integration.

## 📚 Required Reference Files

**CRITICAL**: Before migrating any agent, always read these lab reference files to understand the original implementation:

1. **`agent-testing-lab\full_multi_agent\database.py`** - Lab data structures and storage patterns
2. **`agent-testing-lab\full_multi_agent\service.py`** - Lab service layer with method signatures that backend must match
3. **`agent-testing-lab\full_multi_agent\utils.py`** - Lab utility functions for database operations
4. **`agent-testing-lab\[agent]_test\tools.py`** - Specific agent's tool interface that must be preserved
5. **`agent-testing-lab\[agent]_test\prompt.py`** - Agent's prompt patterns for context understanding

**IMPORTANT**: Always use the `read_file` tool to read these reference files during migration to ensure exact interface compatibility.

These files define the exact interfaces that migrated agents expect to work with.

## Migration Pattern Used for Classifier Agent ✅

### 1. Import Path Updates

#### Before (Lab):
```python
# agents/classifier/tools.py
from service import get_transaction_service, get_communication_service
from utils import get_all_jars
from database import ConversationTurn
```

#### After (Backend):
```python
# backend/agents/classifier/tools.py
from backend.services.financial_services import get_transaction_service, get_communication_service
from backend.models.conversation import ConversationTurnInDB
from backend.utils.db_utils import get_all_jars_for_user
```

### 2. Service Adapter Implementation

The key insight is that lab tools expect **synchronous** function calls without database parameters:
```python
# Lab expectation
transaction_service.add_money_to_jar_with_confidence(amount, jar_name, confidence)
```

But backend services are **async** and require database context:
```python
# Backend reality
await transaction_service.add_money_to_jar_with_confidence(db, user_id, amount, jar_name, confidence)
```

#### Solution: Create Adapter Layer

```python
# backend/services/financial_services.py

class ClassifierServiceAdapter:
    """
    Adapter that provides the exact interface that classifier tools.py expects.
    This bridges the gap between lab interface and backend database requirements.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id
        self.transaction_service = TransactionService()
        self.communication_service = AgentCommunicationService()
    
    def add_money_to_jar_with_confidence(self, amount: float, jar_name: str, confidence: int) -> str:
        """Lab-compatible interface that handles async calls internally."""
        import asyncio
        
        try:
            # Handle async call in sync context using various strategies
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, use executor
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(
                                self.transaction_service.add_money_to_jar_with_confidence(
                                    self.db, self.user_id, amount, jar_name, confidence
                                )
                            )
                        )
                        return future.result()
                else:
                    # Run in current loop
                    return loop.run_until_complete(
                        self.transaction_service.add_money_to_jar_with_confidence(
                            self.db, self.user_id, amount, jar_name, confidence
                        )
                    )
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(
                    self.transaction_service.add_money_to_jar_with_confidence(
                        self.db, self.user_id, amount, jar_name, confidence
                    )
                )
        except Exception as e:
            return f"❌ Error adding transaction: {str(e)}"
```

### 3. Global Service Configuration

Create global service instances that tools can access:

```python
# Global variables to hold service instances configured with database context
_classifier_transaction_service = None
_classifier_communication_service = None

def configure_classifier_services(db: AsyncIOMotorDatabase, user_id: str):
    """
    Configure global service instances for classifier tools.py compatibility.
    This must be called before classifier tools are used.
    """
    global _classifier_transaction_service, _classifier_communication_service
    
    adapter = ClassifierServiceAdapter(db, user_id)
    _classifier_transaction_service = adapter
    _classifier_communication_service = adapter

def get_transaction_service():
    """
    Get transaction service instance for classifier tools.py.
    This function signature matches exactly what classifier tools.py expects.
    """
    if _classifier_transaction_service is None:
        raise RuntimeError(
            "Classifier services not configured. Call configure_classifier_services() first."
        )
    return _classifier_transaction_service

def get_communication_service():
    """
    Get communication service instance for classifier tools.py.
    This function signature matches exactly what classifier tools.py expects.
    """
    if _classifier_communication_service is None:
        raise RuntimeError(
            "Classifier services not configured. Call configure_classifier_services() first."
        )
    return _classifier_communication_service
```

### 4. Missing Service Methods

Implement any missing methods that lab tools expect:

```python
class AgentCommunicationService:
    @staticmethod
    async def call_transaction_fetcher(db: AsyncIOMotorDatabase, user_id: str, 
                                     user_query: str, description: str = "") -> Dict[str, Any]:
        """
        Call transaction fetcher service to get transaction history.
        This matches the lab interface for classifier agent compatibility.
        """
        try:
            query_service = TransactionQueryService()
            
            result = await query_service.get_jar_transactions(
                db=db,
                user_id=user_id,
                jar_name=None,  # Could parse jar from query in future
                limit=50,
                description=description or f"transaction query: {user_query}"
            )
            
            return result
            
        except Exception as e:
            return {
                "data": [],
                "error": f"Failed to fetch transactions: {str(e)}",
                "description": description
            }
```

### 5. Agent Main Class Updates

Update the main agent class to handle database context:

```python
class ReActClassifierAgent:
    def __init__(self, db: AsyncIOMotorDatabase = None, user_id: str = None):
        """Initialize the agent with LLM and tools."""
        self.db = db
        self.user_id = user_id
        # ...existing code...
        
        # Configure services if database context is provided
        if db and user_id:
            configure_classifier_services(db, user_id)
```

### 6. Prompt Building Updates

Update prompt building to be async and use real database data:

```python
async def build_react_classifier_prompt(user_query: str, conversation_history: List[ConversationTurnInDB], 
                                       db: AsyncIOMotorDatabase, user_id: str) -> str:
    """Async prompt building with database context."""
    
    # Fetch current jar information to include in the prompt
    jars = await get_all_jars_for_user(db, user_id)
    jar_info_parts = []
    if jars:
        for jar in jars:
            jar_info_parts.append(
                f"- **{jar.name}**: Allocated ${jar.amount:.2f} ({jar.percent:.0%}). Description: {jar.description}"
            )
    # ...rest of prompt building...
```

### 7. Interface Layer Updates

Update the interface to support both sync and async modes:

```python
class ClassifierInterface(BaseWorkerInterface):
    def __init__(self, db: AsyncIOMotorDatabase = None, user_id: str = None):
        """Initialize with optional database context."""
        self.db = db
        self.user_id = user_id

    def process_task(self, task: str, conversation_history: List[ConversationTurnInDB]) -> Dict[str, Any]:
        """Synchronous wrapper for backward compatibility."""
        return classifier_main.process_task(task, conversation_history)

    async def process_task_async(self, task: str, conversation_history: List[ConversationTurnInDB]) -> Dict[str, Any]:
        """Async version that provides full database functionality."""
        return await classifier_main.process_task_async(task, conversation_history, self.db, self.user_id)
```

## Key Principles for Agent Migration

### 1. **Preserve Lab Interface**
- Never change what tools expect - they should call exactly the same functions with the same parameters
- Create adapters that bridge the gap between lab expectations and backend reality

### 2. **Database Context Injection**
- Add optional database context to main classes: `__init__(self, db=None, user_id=None)`
- Configure services early: `configure_[agent]_services(db, user_id)`
- Provide fallbacks when database unavailable

### 3. **Async/Sync Compatibility** 
- Lab tools expect sync functions, backend uses async
- Use asyncio event loop handling to bridge the gap
- Provide both sync wrappers and async methods

### 4. **Service Layer Completion**
- Ensure all lab service methods are implemented in backend
- Maintain exact same return formats and error handling
- Add any missing methods (like `call_transaction_fetcher`)

### 5. **Model Updates**
- Update imports from lab models to backend models
- Change `ConversationTurn` → `ConversationTurnInDB`
- Update database function calls: `get_all_jars()` → `get_all_jars_for_user(db, user_id)`

## Migration Checklist

For each agent, verify:

- [ ] **Import paths updated** to use backend modules
- [ ] **Service adapter created** with lab-compatible interface  
- [ ] **Global service configuration** functions implemented
- [ ] **Missing service methods** added to backend services
- [ ] **Agent main class** updated with database context
- [ ] **Prompt building** made async with real database data
- [ ] **Interface layer** supports both sync/async modes
- [ ] **Error handling** works with and without database
- [ ] **All tools import** successfully without errors
- [ ] **README.md updated** with new architecture and usage

## Files to Modify for Each Agent

1. **`{agent}/tools.py`**: Update imports to backend services
2. **`{agent}/prompt.py`**: Make async, use backend models and db functions  
3. **`{agent}/main.py`**: Add database context handling
4. **`{agent}/interface.py`**: Add async methods and database context
5. **`backend/services/financial_services.py`**: Add agent-specific adapter and service methods
6. **`{agent}/README.md`**: Update documentation

## Testing Migration Success

```python
# Test imports work
from backend.agents.{agent}.tools import get_all_{agent}_tools
from backend.agents.{agent}.interface import get_agent_interface

# Test service configuration  
from backend.services.financial_services import configure_{agent}_services
configure_{agent}_services(db, user_id)

# Test both sync and async modes
interface = get_agent_interface(db, user_id)
result = interface.process_task(task, history)
result = await interface.process_task_async(task, history)
```

This migration pattern ensures that agents maintain their lab functionality while gaining full backend database integration! 🎉
