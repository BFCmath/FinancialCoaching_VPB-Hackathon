reading: [text](for_ai.md)
reading: [text](detail_context.md)

> reading all files I sent
> Always reading to confirm instead of asssuming wrong context
> avoid hallucination efffectively by reading lines by lines and take note as you go

# Jar Manager Agent - Multi-Jar Implementation Specifications

## 🎯 Agent Purpose

The **jar_manager** is an **LLM-powered agent** using **Gemini 2.5 Flash Lite** that analyzes natural language descriptions of jar operations and executes advanced CRUD commands through LangChain tool calling. The system implements **T. Harv Eker's official 6-jar money management system** with **multi-jar operations**, **automatic percentage rebalancing**, and **comprehensive budget validation**.

## 🏺 T. Harv Eker's Official 6-Jar System

### Default Jar Configuration:
```python
DEFAULT_JARS_DATABASE = [
    {
        "name": "necessities",
        "description": "Essential living expenses (rent, utilities, groceries)",
        "percent": 0.55,            # 55% allocation
        "current_percent": 0.0      # No money added yet
    },
    {
        "name": "long_term_savings_for_spending", 
        "description": "Long-term savings for major purchases and goals",
        "percent": 0.10,            # 10% allocation
        "current_percent": 0.0
    },
    {
        "name": "play",
        "description": "Entertainment, dining, hobbies, and fun activities",
        "percent": 0.10,            # 10% allocation
        "current_percent": 0.0
    },
    {
        "name": "education",
        "description": "Learning, courses, books, and skill development",
        "percent": 0.10,            # 10% allocation
        "current_percent": 0.0
    },
    {
        "name": "financial_freedom",
        "description": "Investments and building passive income streams",
        "percent": 0.10,            # 10% allocation
        "current_percent": 0.0
    },
    {
        "name": "give",
        "description": "Charity, donations, and helping others",
        "percent": 0.05,            # 5% allocation
        "current_percent": 0.0
    }
]

TOTAL_INCOME = 5000.0  # Sample income for calculations
```

## 📊 Advanced Data Structure

### Current Jar Implementation:
```python
# Simple dictionary-based storage with decimal percentages
jar_data = {
    "name": str,                # Unique identifier (e.g., "vacation", "emergency")
    "description": str,         # Human-readable description
    "percent": float,          # Budget allocation (0.0-1.0, e.g., 0.1 = 10%)
    "current_percent": float   # Current balance as percentage (0.0-1.0)
}

# Example jar:
{
    "name": "vacation",
    "description": "Summer vacation to Korea",
    "percent": 0.15,           # 15% budget allocation
    "current_percent": 0.08    # 8% currently saved (can exceed percent - overflow allowed)
}
```

### Percentage System (0.0-1.0):
- **All percentages stored as decimals**: 0.1 = 10%, 0.55 = 55%
- **Budget calculated dynamically**: budget = percent × TOTAL_INCOME
- **Current balance calculated**: current_amount = current_percent × TOTAL_INCOME
- **Overflow allowed**: current_percent can exceed percent (with warnings)

### Utility Functions:
```python
def calculate_budget_from_percent(percent: float) -> float:
    return percent * TOTAL_INCOME

def calculate_current_amount_from_percent(current_percent: float) -> float:
    return current_percent * TOTAL_INCOME

def calculate_percent_from_amount(amount: float) -> float:
    return amount / TOTAL_INCOME

def format_percent_display(percent: float) -> str:
    return f"{percent * 100:.1f}%"
```

## 🛠️ Simplified Multi-Jar CRUD Operations (4 Core Tools)

### Core Tools Available:
1. **`create_jar()`** - Create one or multiple jars with automatic rebalancing
2. **`update_jar()`** - Update jar properties and percentages  
3. **`delete_jar()`** - Delete jars with automatic redistribution
4. **`list_jars()`** - Display all jars with status
5. **`request_clarification()`** - Ask for clarification when needed

**Important:** The `add_money_to_jar` tool has been removed. Users who want to add money should use `update_jar` to increase percentage allocations instead.

### 1. **Multi-Jar Creation**

#### `create_jar()` - Create Multiple Jars Simultaneously
```python
@tool
def create_jar(
    name: List[str],                    # List of jar names
    description: List[str],             # List of descriptions
    percent: List[Optional[float]] = None,  # List of percentages (0.0-1.0)
    amount: List[Optional[float]] = None,   # List of dollar amounts
    confidence: int = 85                # LLM confidence (0-100)
) -> str:
    """Create one or multiple jars with automatic percentage rebalancing"""
```

**Single Jar Example:**
```python
create_jar(
    name=["vacation"],
    description=["Summer trip to Korea"],
    percent=[0.15],  # 15%
    confidence=90
)
# Result: ✅ Created vacation jar (15.0%, $750.00 budget). Rebalancing applied to existing jars.
```

**Multi-Jar Example:**
```python
create_jar(
    name=["vacation", "emergency"], 
    description=["Summer trip", "Emergency fund"],
    percent=[0.05, 0.10],  # 5% and 10%
    confidence=85
)
# Result: ✅ Created 2 jars: vacation (5.0%, $250.00), emergency (10.0%, $500.00). 
#         Total new allocation: 15.0%. Rebalancing applied to existing jars.
```

**Amount-Based Creation:**
```python
create_jar(
    name=["car_repair"],
    description=["Car maintenance fund"],
    amount=[1000],  # $1000 = 20% of $5000 income
    confidence=88
)
# Result: ✅ Created car_repair jar (20.0%, $1000.00 budget). Rebalancing applied.
```

### 2. **Multi-Jar Updates**

#### `update_jar()` - Update Multiple Jars with Rebalancing
```python
@tool
def update_jar(
    jar_name: List[str],                        # List of jar names to update
    new_name: List[Optional[str]] = None,       # List of new names
    new_description: List[Optional[str]] = None, # List of new descriptions
    new_percent: List[Optional[float]] = None,   # List of new percentages
    new_amount: List[Optional[float]] = None,    # List of new amounts
    confidence: int = 85                        # LLM confidence
) -> str:
    """Update one or multiple jars with automatic rebalancing"""
```

**Multi-Jar Percentage Update:**
```python
update_jar(
    jar_name=["vacation", "emergency"],
    new_percent=[0.08, 0.12],  # Change to 8% and 12%
    confidence=90
)
# Result: ✅ Updated 2 jars: vacation (15.0% → 8.0%), emergency (10.0% → 12.0%). 
#         Net change: -5.0%. Rebalancing applied to other jars.
```

### 3. **Multi-Jar Deletion**

#### `delete_jar()` - Delete Multiple Jars with Rebalancing
```python
@tool
def delete_jar(
    jar_name: List[str],     # List of jar names to delete
    reason: str              # Reason for deletion
) -> str:
    """Delete one or multiple jars and redistribute percentages to remaining jars"""
```

**Multi-Jar Deletion:**
```python
delete_jar(
    jar_name=["vacation", "emergency"],
    reason="Goals changed"
)
# Result: ✅ Deleted 2 jars: vacation (8.0%, $400.00), emergency (12.0%, $600.00). 
#         Total freed: 20.0%. Redistributed proportionally to remaining jars.
```

### 4. **Multi-Jar Money Addition**

#### `add_money_to_jar()` - Add Money to Multiple Jars
```python
@tool
def add_money_to_jar(
    jar_name: List[str],                    # List of jar names
    percent: List[Optional[float]] = None,  # List of percentages to add
    amount: List[Optional[float]] = None,   # List of dollar amounts to add
    description: str = "Money added"        # Description of addition
) -> str:
    """Add money to one or multiple jars (overflow allowed)"""
```

**Multi-Jar Money Addition:**
```python
add_money_to_jar(
    jar_name=["play", "education"],
    amount=[100, 150],  # $100 to play, $150 to education
    description="Monthly savings"
)
# Result: ✅ Added money to 2 jars: play: +$100.00 (2.0%) → $600.00 (12.0%); 
#         education: +$150.00 (3.0%) → $650.00 (13.0%) ⚠️ Overflow: $150.00 (3.0%). Monthly savings
```

## 🔄 Automatic Rebalancing System

### Rebalancing Logic:

#### **New Jar Creation:**
```python
def rebalance_jar_percentages(new_jar_percent: float) -> str:
    """Proportionally reduce all existing jars to make room for new jar"""
    
    # Calculate scaling factor
    scale_factor = (1.0 - new_jar_percent) / current_total_percent
    
    # Apply to all existing jars
    for jar in existing_jars:
        jar["percent"] *= scale_factor
```

#### **Jar Deletion:**
```python
def redistribute_deleted_jar_percentage(deleted_percent: float) -> str:
    """Proportionally distribute freed percentage to remaining jars"""
    
    # Calculate distribution factor
    distribution_factor = 1.0 + (deleted_percent / remaining_total_percent)
    
    # Apply to all remaining jars
    for jar in remaining_jars:
        jar["percent"] *= distribution_factor
```

#### **Multi-Jar Operations:**
```python
def rebalance_multiple_new_jars(total_new_percent: float) -> str:
    """Handle rebalancing when creating multiple jars simultaneously"""

def rebalance_after_multiple_updates(updated_jars: List[tuple], total_percent_change: float) -> str:
    """Handle rebalancing after updating multiple jars"""
```

## 🧠 LLM Tool Calling Process

### Enhanced Input Processing Examples:

#### **Single Operations:**
```python
"Create vacation jar with 15%"                    # Single jar creation
"Update vacation jar to 12%"                      # Single jar update
"Delete vacation jar because trip cancelled"      # Single jar deletion
"Add $200 to vacation jar"                        # Single money addition
```

#### **Multi-Jar Operations:**
```python
"Create vacation and emergency jars with 10% each"           # Multi-jar creation
"Update vacation to 8% and emergency to 15%"                # Multi-jar updates
"Delete vacation and car repair jars"                       # Multi-jar deletion
"Add $100 to play jar and $200 to education jar"           # Multi-jar money addition
```

#### **Vietnamese Language Support:**
```python
"Tạo hũ du lịch và hũ khẩn cấp với 10% mỗi cái"           # Create vacation and emergency jars
"Thêm 200 đô vào hũ giải trí"                             # Add $200 to play jar
"Xóa hũ du lịch vì hủy chuyến đi"                         # Delete vacation jar
```

### Current Implementation Flow:
```python
def handle_confidence_flow(user_input: str, llm_with_tools) -> str:
    """Enhanced flow with multi-jar support and rebalancing"""
    
    # 1. Fetch current context
    existing_jars = fetch_existing_jars()
    total_income = TOTAL_INCOME
    
    # 2. Build comprehensive prompt
    full_prompt = build_jar_manager_prompt(user_input, existing_jars, total_income)
    
    # 3. Send to Gemini with multi-jar tools
    response = llm_with_tools.invoke([HumanMessage(content=full_prompt)])
    
    # 4. Execute multi-jar operations with validation
    if response.tool_calls:
        results = []
        for tool_call in response.tool_calls:
            # Validate list inputs for multi-jar operations
            tool_result = execute_validated_tool_call(tool_call)
            results.append(tool_result)
        
        return combine_tool_results(results)
    else:
        return "❌ LLM did not use any tools"
```

## 📋 Enhanced Tool Responses

### Confidence-Based Output:
```python
# High confidence (90%+)
"✅ Created vacation jar (15.0%, $750.00 budget). Rebalancing applied."

# Moderate confidence (70-89%)
"⚠️ Created vacation jar (15.0%, $750.00 budget) - moderate certainty. Rebalancing applied."

# Low confidence (<70%)
"❓ Created vacation jar (15.0%, $750.00 budget) - please verify. Rebalancing applied."
```

### Multi-Jar Response Examples:
```python
# Multi-jar creation
"✅ Created 2 jars: vacation (5.0%, $250.00), emergency (10.0%, $500.00). Total new allocation: 15.0%. 
📊 Rebalancing applied: necessities (55.0% → 46.8%), play (10.0% → 8.5%), education (10.0% → 8.5%), 
financial_freedom (10.0% → 8.5%), give (5.0% → 4.3%), long_term_savings_for_spending (10.0% → 8.5%)"

# Multi-jar updates with overflow
"✅ Updated 2 jars: play: 10.0% → 15.0%, education: 10.0% → 20.0%. 
📊 Rebalancing applied: Total increased by 15.0%, other jars scaled down proportionally."

# Multi-jar money addition with overflow
"✅ Added money to 2 jars: play: +$100.00 (2.0%) → $600.00 (12.0%) ⚠️ Overflow: $100.00 (2.0%); 
education: +$150.00 (3.0%) → $650.00 (13.0%) ⚠️ Overflow: $150.00 (3.0%). Monthly savings"
```

## 🔍 System Validation & Error Handling

### Comprehensive Validation:
```python
# List length validation
if len(jar_name) != len(description):
    return "❌ List lengths must match: jar names and descriptions"

# Percentage overflow prevention
total_new_percent = sum(percent_list)
if current_total + total_new_percent > 1.0:
    return f"❌ Total allocation would exceed 100% (current: {format_percent_display(current_total)}, 
             adding: {format_percent_display(total_new_percent)})"

# Atomic operations
try:
    # Pre-validate all operations
    validate_all_operations()
    # Execute all operations
    execute_all_operations()
except Exception as e:
    # Rollback all changes
    rollback_operations()
    return f"❌ Operation failed: {e}"
```

### Enhanced Debug Output:
```python
def get_jar_summary() -> str:
    """Enhanced summary with total validation and rebalancing status"""
    
    total_percent = sum(jar["percent"] for jar in jars)
    total_current = sum(jar["current_percent"] for jar in jars)
    
    return f"""📋 Budget Jars ({len(jars)} jars) - Total Income: ${TOTAL_INCOME:.2f}
{jar_list}
💰 Totals: ${total_current_amount:.2f}/${total_budget_amount:.2f} 
({format_percent_display(total_current)}/{format_percent_display(total_percent)})
{"✅ Balanced allocation" if abs(total_percent - 1.0) < 0.001 else "⚠️ Unbalanced allocation"}"""
```

This comprehensive multi-jar system provides enterprise-grade jar management with automatic rebalancing, overflow handling, and full T. Harv Eker 6-jar system implementation.
