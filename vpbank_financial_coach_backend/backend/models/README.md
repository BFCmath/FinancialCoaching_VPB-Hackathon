# Models and Utils Documentation

## Overview

This document provides comprehensive documentation for the backend models and utilities of the VPBank Financial Coach application. All components have been reviewed and verified for consistency and correctness.

## Directory Structure

```
backend/
├── models/
│   ├── conversation.py     # Conversation history and metadata models
│   ├── fee.py             # Recurring fee management models
│   ├── jar.py             # Budget jar allocation models
│   ├── plan.py            # Budget planning models
│   ├── token.py           # JWT authentication tokens
│   ├── transaction.py     # Financial transaction models
│   ├── user.py            # User account and authentication models
│   └── user_settings.py   # User configuration models
└── utils/
    └── db_utils.py        # Database operations and utilities
```

## Models Documentation

### 1. Conversation Models (`conversation.py`)

**Purpose**: Handle conversation history and agent interaction metadata.

**Key Features**:
- ✅ Enhanced metadata support for agent stage information
- ✅ Agent lock tracking for conversation continuity
- ✅ Tool call logging for debugging and analytics

**Models**:
- `ConversationTurnBase`: Base model with common fields
- `ConversationTurnCreate`: Input model for new conversation turns
- `ConversationTurnInDB`: Database storage model with ID and timestamps

**Usage Example**:
```python
from backend.models.conversation import ConversationTurnCreate

turn = ConversationTurnCreate(
    user_input="I want to save for vacation",
    agent_output="Let me help you create a savings plan",
    agent_list=["orchestrator", "plan"],
    tool_call_list=["propose_plan(goal='vacation')"],
    metadata={"plan_stage": "1", "agent_context": "budget_planning"}
)
```

### 2. Fee Models (`fee.py`)

**Purpose**: Manage recurring fees and subscription tracking.

**Key Features**:
- ✅ Pattern-based recurrence (daily, weekly, monthly)
- ✅ Target jar allocation for automatic budgeting
- ✅ Active/inactive status for fee management
- ✅ Next occurrence calculation support

**Models**:
- `RecurringFeeBase`: Core fee information
- `RecurringFeeCreate`: Input model for new fees
- `RecurringFeeUpdate`: Partial update model
- `RecurringFeeInDB`: Database storage with calculated fields

**Usage Example**:
```python
from backend.models.fee import RecurringFeeCreate

netflix_fee = RecurringFeeCreate(
    name="Netflix Subscription",
    amount=15.99,
    description="Monthly streaming subscription",
    target_jar="play",
    pattern_type="monthly",
    pattern_details=[1]  # First day of month
)
```

### 3. Jar Models (`jar.py`)

**Purpose**: Budget jar allocation and balance tracking.

**Key Features**:
- ✅ Percentage and amount allocation support
- ✅ Current balance tracking
- ✅ Flexible jar creation (percent OR amount input)
- ✅ Automatic calculation validation

**Models**:
- `JarBase`: Core jar information
- `JarCreate`: Flexible input model (percent OR amount)
- `JarUpdate`: Partial update model
- `JarInDB`: Complete storage model with calculations

**Usage Example**:
```python
from backend.models.jar import JarCreate

necessities_jar = JarCreate(
    name="Necessities",
    description="Essential living costs like rent and groceries",
    percent=0.55  # 55% of total income
)
```

### 4. Plan Models (`plan.py`)

**Purpose**: Budget planning and goal tracking.

**Key Features**:
- ✅ Plan status tracking (active, completed, paused)
- ✅ Jar recommendation integration
- ✅ Detailed descriptions and creation dates
- ✅ Compatible with plan agent workflows

**Models**:
- `BudgetPlanBase`: Core plan information
- `BudgetPlanCreate`: Input model for new plans
- `BudgetPlanUpdate`: Partial update model
- `BudgetPlanInDB`: Database storage model

**Usage Example**:
```python
from backend.models.plan import BudgetPlanCreate

vacation_plan = BudgetPlanCreate(
    name="Save for Vacation",
    detail_description="Plan to save $2000 for a trip to Japan next year",
    day_created="2025-07-14",
    jar_recommendations="Increase 'long_term_savings' jar by 5%"
)
```

### 5. Token Models (`token.py`)

**Purpose**: JWT authentication token handling.

**Key Features**:
- ✅ Standard JWT token structure
- ✅ Token data validation
- ✅ Bearer token type specification

**Models**:
- `Token`: JWT response model
- `TokenData`: Token payload model

**Usage Example**:
```python
from backend.models.token import Token

token_response = Token(
    access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    token_type="bearer"
)
```

### 6. Transaction Models (`transaction.py`)

**Purpose**: Financial transaction recording and tracking.

**Key Features**:
- ✅ Multiple input sources (API, manual, text, image)
- ✅ Jar-based categorization
- ✅ Date and time tracking (string and datetime formats)
- ✅ Positive amount validation

**Models**:
- `TransactionBase`: Core transaction data
- `TransactionCreate`: Input model for new transactions
- `TransactionInDB`: Database storage with user reference

**Usage Example**:
```python
from backend.models.transaction import TransactionCreate

grocery_transaction = TransactionCreate(
    amount=75.50,
    jar="necessities",
    description="Grocery shopping at supermarket",
    date="2025-07-14",
    time="14:30",
    source="manual_input"
)
```

### 7. User Models (`user.py`)

**Purpose**: User account management and authentication.

**Key Features**:
- ✅ Email and username validation
- ✅ Password hashing integration
- ✅ Public user information model (no password exposure)
- ✅ MongoDB _id handling

**Models**:
- `UserBase`: Common user fields
- `UserCreate`: Registration input model
- `UserUpdate`: Profile update model
- `UserInDB`: Database storage with hashed password
- `UserPublic`: Safe public information model

**Usage Example**:
```python
from backend.models.user import UserCreate

new_user = UserCreate(
    username="john_doe",
    email="john@example.com",
    password="secure_password123"
)
```

### 8. User Settings Models (`user_settings.py`)

**Purpose**: User-specific financial configuration.

**Key Features**:
- ✅ Total income tracking for percentage calculations
- ✅ User-scoped settings
- ✅ Validation for positive income values

**Models**:
- `UserSettingsBase`: Core settings data
- `UserSettingsUpdate`: Update input model
- `UserSettingsInDB`: Database storage with user reference

**Usage Example**:
```python
from backend.models.user_settings import UserSettingsUpdate

settings_update = UserSettingsUpdate(
    total_income=5500.0  # Updated monthly income
)
```

## Database Utilities Documentation

### Database Utilities (`db_utils.py`)

**Purpose**: Comprehensive data access layer for MongoDB operations.

**Key Features**:
- ✅ Async MongoDB operations for all models
- ✅ User-scoped data isolation
- ✅ Consistent error handling
- ✅ Advanced query utilities
- ✅ Agent lock management for conversation continuity
- ✅ Calculation and validation utilities

### Core Operations

#### User Operations
- `get_user_by_username()` / `get_user_by_email()`: User lookup
- `create_user()`: New user registration with password hashing

#### User Settings Operations
- `get_user_settings()` / `create_or_update_user_settings()`: Income configuration

#### Conversation Lock Operations
- `set_agent_lock_for_user()` / `get_agent_lock_for_user()`: Agent conversation locks
- TTL-based automatic lock expiration (5 minutes)

#### Conversation History Operations
- `add_conversation_turn_for_user()`: Log new conversation turns
- `get_conversation_history_for_user()`: Retrieve conversation history

#### CRUD Operations (Jars, Transactions, Fees, Plans)
- Full CRUD support for all financial entities
- User-scoped operations with data isolation
- Case-insensitive name searches
- Soft delete support for fees (active/inactive)

### Advanced Query Utilities

#### Extended Operations
- `get_user_transactions()`: Paginated transaction retrieval
- `calculate_jar_spending_total()`: Jar spending calculations
- `get_fees_due_today()`: Due date filtering
- `get_transactions_by_amount_range_for_user()`: Amount-based filtering
- `get_agent_specific_history()`: Agent-filtered conversation history

#### Calculation Utilities
- `calculate_percent_from_amount()` / `calculate_amount_from_percent()`: Income percentage conversions
- `format_currency()` / `format_percentage()`: Display formatting
- `validate_percentage_range()` / `validate_positive_amount()`: Input validation

#### Recurring Fee Utilities
- `calculate_next_fee_occurrence()`: Smart recurrence calculation
- Support for daily, weekly, and monthly patterns
- Pattern detail interpretation (specific days/dates)

#### Validation Utilities
- `validate_jar_data()`: Comprehensive jar validation
- `validate_transaction_data()`: Transaction input validation
- Amount-percentage consistency checks

### Database Statistics
- `get_database_stats()`: Comprehensive user statistics
- Jar allocation analysis
- Transaction summaries
- Fee status tracking
- Plan progress monitoring

## Technical Specifications

### Database Collections
- `users`: User accounts and authentication
- `user_settings`: User-specific configuration
- `jars`: Budget jar allocations
- `transactions`: Financial transaction records
- `fees`: Recurring fee definitions
- `plans`: Budget planning documents
- `conversation_history`: Agent conversation logs
- `agent_locks`: Conversation continuity locks

### Field Naming Conventions
- ✅ **Consistent**: `jar` field in transactions matches model definition
- ✅ **Consistent**: `date` field matches transaction model
- ✅ **MongoDB Standard**: `_id` fields with alias mapping to `id`
- ✅ **Timestamp**: ISO format datetime strings where appropriate

### Validation Rules
- **Amounts**: Must be positive values
- **Percentages**: Must be between 0.0 and 1.0
- **Names**: Minimum length requirements with case-insensitive searches
- **Dates**: YYYY-MM-DD string format with datetime alternatives
- **Emails**: Pydantic EmailStr validation

### Error Handling
- ✅ **Optional Returns**: None for not-found cases
- ✅ **Validation Errors**: Pydantic model validation
- ✅ **Type Safety**: Full type annotations throughout
- ✅ **Async Safety**: Proper async/await patterns

## Best Practices

### Model Usage
1. **Input Validation**: Use Create models for API inputs
2. **Database Storage**: Use InDB models for persistence
3. **Public Response**: Use Public models for API responses
4. **Updates**: Use Update models for partial modifications

### Database Operations
1. **User Isolation**: Always include user_id in queries
2. **Async Operations**: Use async/await for all database calls
3. **Error Handling**: Check for None returns and handle gracefully
4. **Performance**: Use appropriate indexes on frequently queried fields

### Security Considerations
1. **Password Handling**: Never store plain text passwords
2. **User Isolation**: Enforce user-scoped data access
3. **Input Validation**: Validate all user inputs before database operations
4. **Token Security**: Implement proper JWT expiration and validation

## Dependencies

### Required Python Packages
- `pydantic`: Model validation and serialization
- `motor`: Async MongoDB driver
- `pymongo`: MongoDB operations and constants
- `datetime`: Date and time handling

### Optional Dependencies
- `python-dotenv`: Environment variable loading
- `passlib`: Password hashing utilities
- `python-jose`: JWT token handling

## Migration and Compatibility

### Database Migration Notes
- ✅ Field names aligned between models and database queries
- ✅ MongoDB constants properly imported
- ✅ Return document parameters standardized
- ✅ Timezone handling simplified (removed pytz dependency)

### Backward Compatibility
- ✅ Existing API endpoints remain functional
- ✅ Legacy date formats supported
- ✅ Graceful handling of missing metadata fields
- ✅ Optional field additions don't break existing data

This documentation covers all aspects of the models and utilities components, ensuring proper usage and maintenance of the VPBank Financial Coach backend system.
