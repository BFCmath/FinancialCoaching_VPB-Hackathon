# Jar Manager Agent - Multi-Jar System Context

## 🎯 Project Overview

This is a **comprehensive multi-jar manager testing lab** for an LLM-powered agent that analyzes natural language descriptions of jar operations and executes advanced CRUD commands using **Gemini LLM with LangChain tool calling**. The system implements **T. Harv Eker's official 6-jar money management system** with **multi-jar operations**, **automatic percentage rebalancing**, and **enterprise-grade budget validation**.

## 🏗️ Current System Architecture

### Core Components:
```
📁 jar_test/
├── 🧠 main.py           # LLM setup, multi-jar tool execution, enhanced debug output
├── 🛠️ tools.py          # Multi-jar LangChain tools, decimal percentage system, rebalancing
├── 📝 prompt.py         # Enhanced jar operation prompt with multi-jar examples
├── ⚙️ config.py         # Gemini API configuration and confidence thresholds
├── 🧪 test.py          # Interactive testing interface for multi-jar operations
├── 📋 requirements.txt  # Dependencies (langchain-google-genai, google-generativeai)
├── 🔧 env.example      # Environment variables template
└── 📁 cursor_docs/     # Updated documentation for multi-jar system
```

### Enhanced LLM-Powered Multi-Jar Tool Calling Flow:
```
User Multi-Jar Input ("Create vacation and emergency jars with 10% each")
         ↓
fetch_existing_jars() + TOTAL_INCOME context ($5000)
         ↓
build_jar_manager_prompt(user_input, existing_jars, total_income)
         ↓
llm_with_tools.invoke([HumanMessage(content=enhanced_prompt)])
         ↓
LLM analyzes operation and calls: create_jar(
    name=["vacation", "emergency"], 
    description=["Summer vacation", "Emergency savings"], 
    percent=[0.10, 0.10],  # 10% each in decimal format
    confidence=90
)
         ↓
Multi-jar tool execution + comprehensive validation + automatic rebalancing
         ↓
Response: "✅ Created 2 jars: vacation (10.0%, $500.00), emergency (10.0%, $500.00). 
          Total new allocation: 20.0%. Rebalancing applied to existing jars (90% confident)"
```

### Implementation with Enhanced Confidence-Based Responses:
```python
def handle_confidence_flow(user_input: str, llm_with_tools) -> str:
    """Enhanced multi-jar processing with automatic rebalancing"""
    
    # 1. Fetch comprehensive context
    existing_jars = fetch_existing_jars()
    total_income = TOTAL_INCOME
    current_total_percent = sum(jar["percent"] for jar in existing_jars)
    
    # 2. Build enhanced prompt with multi-jar examples
    full_prompt = build_jar_manager_prompt(user_input, existing_jars, total_income)
    
    # 3. Send to Gemini with enhanced multi-jar tools
    response = llm_with_tools.invoke([HumanMessage(content=full_prompt)])
    
    # 4. Execute multi-jar tool calls with comprehensive validation
    if response.tool_calls:
        results = []
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Execute multi-jar tool with validation
            tool_function = get_tool_by_name(tool_name)
            result = tool_function(**tool_args)
            results.append(result)
        
        return combine_multi_jar_results(results)
    else:
        return "❌ LLM did not use any tools"
```

## 🏺 Enhanced Jar Data Structure

### Multi-Jar Implementation with Decimal Percentages:
```python
# Simplified dictionary-based storage optimized for multi-jar operations
jar_data = {
    "name": str,                # Unique identifier (e.g., "vacation", "emergency")
    "description": str,         # Human-readable description
    "percent": float,          # Budget allocation (0.0-1.0, e.g., 0.1 = 10%)
    "current_percent": float   # Current balance as percentage (0.0-1.0, can exceed percent)
}

# Sample income for realistic calculations
TOTAL_INCOME = 5000.0

# Utility functions for percentage/amount conversions
def calculate_budget_from_percent(percent: float) -> float:
    return percent * TOTAL_INCOME

def calculate_current_amount_from_percent(current_percent: float) -> float:
    return current_percent * TOTAL_INCOME

def calculate_percent_from_amount(amount: float) -> float:
    return amount / TOTAL_INCOME

def format_percent_display(percent: float) -> str:
    return f"{percent * 100:.1f}%"
```

### T. Harv Eker's Official 6-Jar System:
```python
DEFAULT_JARS_DATABASE = [
    {
        "name": "necessities",
        "description": "Essential living expenses (rent, utilities, groceries, basic needs)",
        "percent": 0.55,            # 55% allocation
        "current_percent": 0.0      # No money added initially
    },
    {
        "name": "long_term_savings_for_spending", 
        "description": "Long-term savings for major purchases and future goals",
        "percent": 0.10,            # 10% allocation
        "current_percent": 0.0
    },
    {
        "name": "play",
        "description": "Entertainment, dining, hobbies, travel, and fun activities",
        "percent": 0.10,            # 10% allocation
        "current_percent": 0.0
    },
    {
        "name": "education",
        "description": "Learning, courses, books, training, and skill development",
        "percent": 0.10,            # 10% allocation
        "current_percent": 0.0
    },
    {
        "name": "financial_freedom",
        "description": "Investments, passive income, and building wealth",
        "percent": 0.10,            # 10% allocation
        "current_percent": 0.0
    },
    {
        "name": "give",
        "description": "Charity, donations, gifts, and helping others",
        "percent": 0.05,            # 5% allocation
        "current_percent": 0.0
    }
]
```

### Multi-Jar System Advantages:

#### **Batch Operations:**
- Create multiple jars simultaneously with consistent validation
- Update multiple jars with automatic rebalancing 
- Delete multiple jars with proportional redistribution
- Add money to multiple jars in a single operation

#### **Atomic Transactions:**
- All operations succeed or all fail (no partial updates)
- Pre-validation prevents invalid states
- Rollback capability for failed operations

#### **Intelligent Rebalancing:**
- Automatic percentage redistribution when jars are added/removed
- Proportional scaling to maintain 100% total allocation
- Overflow handling with clear warnings

## 🛠️ Simplified Multi-Jar Tool Implementation (4 Core Tools)

### Core Tools Overview:
1. **`create_jar()`** - Create one or multiple jars with automatic rebalancing
2. **`update_jar()`** - Update jar properties with percentage adjustments
3. **`delete_jar()`** - Delete jars with automatic redistribution
4. **`list_jars()`** - Display all jars with status
5. **`request_clarification()`** - Ask for clarification when needed

**Note:** The `add_money_to_jar` tool has been removed for simplicity. Users should use `update_jar` to modify percentage allocations instead.

### 1. **Multi-Jar Creation Tool**

#### `create_jar()` - Enhanced for Multiple Jars
```python
@tool
def create_jar(
    name: List[str],                    # List of jar names to create
    description: List[str],             # List of descriptions
    percent: List[Optional[float]] = None,  # List of percentages (0.0-1.0)
    amount: List[Optional[float]] = None,   # List of dollar amounts
    confidence: int = 85                # LLM confidence (0-100)
) -> str:
    """Create one or multiple jars with automatic percentage rebalancing"""
    
    # Key Features:
    # - Multi-jar batch creation with validation
    # - Automatic rebalancing to maintain 100% allocation
    # - Supports both percentage and amount inputs
    # - Atomic operations (all succeed or all fail)
    
    # Validation logic ensures:
    # - List lengths match across all parameters
    # - Either percent OR amount specified (not both)
    # - New jars don't exceed 100% even with rebalancing
        return "❌ Must provide either 'percent' list (0.0-1.0) or 'amount' list (dollars)"
    
    if percent is not None and amount is not None:
        return "❌ Provide either 'percent' OR 'amount' list, not both"
    
    # Convert amounts to percentages if needed
    if amount is not None:
        percent = [calculate_percent_from_amount(amt) for amt in amount]
    
    # Pre-validate all operations
    total_new_percent = sum(percent)
    current_total_percent = sum(jar["percent"] for jar in fetch_existing_jars())
    
    if current_total_percent + total_new_percent > 1.0:
        overflow = current_total_percent + total_new_percent - 1.0
        return f"❌ Total allocation would exceed 100% by {format_percent_display(overflow)}"
    
    # Atomic creation of all jars
    created_jars = []
    try:
        for i in range(num_jars):
            # Validate individual jar
            is_valid, error_msg = validate_jar_name(name[i])
            if not is_valid:
                raise ValueError(f"Jar {i+1}: {error_msg}")
            
            if percent[i] <= 0:
                raise ValueError(f"Jar {i+1}: Percent must be positive, got {percent[i]}")
            
            # Create jar data
            jar_data = {
                "name": name[i].strip(),
                "description": description[i],
                "percent": percent[i],
                "current_percent": 0.0
            }
            
            save_jar(jar_data)
            created_jars.append(jar_data)
        
        # Apply rebalancing after all jars created
        rebalance_message = rebalance_multiple_new_jars(total_new_percent)
        
        # Format response
        if num_jars == 1:
            jar = created_jars[0]
            budget = calculate_budget_from_percent(jar["percent"])
            base_message = f"✅ Created {jar['name']} jar ({format_percent_display(jar['percent'])}, ${budget:.2f} budget)"
        else:
            jar_summaries = []
            for jar in created_jars:
                budget = calculate_budget_from_percent(jar["percent"])
                jar_summaries.append(f"{jar['name']} ({format_percent_display(jar['percent'])}, ${budget:.2f})")
            
            jar_summary = ", ".join(jar_summaries)
            base_message = f"✅ Created {num_jars} jars: {jar_summary}. Total new allocation: {format_percent_display(total_new_percent)}"
        
        # Add rebalancing info and confidence
        if rebalance_message:
            base_message += f"\n{rebalance_message}"
        
        if confidence >= 90:
            return f"{base_message} ({confidence}% confident)"
        elif confidence >= 70:
            return f"⚠️ {base_message} ({confidence}% confident - moderate certainty)"
        else:
            return f"❓ {base_message} ({confidence}% confident - please verify)"
    
    except Exception as e:
        # Rollback any created jars
        for jar in created_jars:
            delete_jar_from_storage(jar["name"])
        return f"❌ Failed to create jars: {e}"
```

### 2. **Multi-Jar Update Tool**

#### `update_jar()` - Enhanced for Multiple Updates
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
    
    # Similar comprehensive validation and atomic operations
    # ... (detailed implementation with rebalancing logic)
```

### 3. **Multi-Jar Deletion Tool**

#### `delete_jar()` - Enhanced for Multiple Deletions
```python
@tool
def delete_jar(
    jar_name: List[str],     # List of jar names to delete
    reason: str              # Reason for deletion
) -> str:
    """Delete one or multiple jars and redistribute percentages to remaining jars"""
    
    # Find all jars to delete
    jars_to_delete = []
    total_deleted_percent = 0.0
    
    for jar_name_item in jar_name:
        jar = get_jar_by_name(jar_name_item)
        if not jar:
            return f"❌ Jar '{jar_name_item}' not found"
        jars_to_delete.append(jar)
        total_deleted_percent += jar["percent"]
    
    # Delete all jars and redistribute percentages
    deleted_jars_info = []
    for jar in jars_to_delete:
        deleted_percent = jar["percent"]
        deleted_budget = calculate_budget_from_percent(deleted_percent)
        deleted_name = jar["name"]
        
        delete_jar_from_storage(jar["name"])
        deleted_jars_info.append({
            'name': deleted_name,
            'percent': deleted_percent,
            'budget': deleted_budget
        })
    
    # Apply redistribution
    rebalance_message = redistribute_deleted_jar_percentage(total_deleted_percent)
    
    # Format comprehensive response
    # ... (detailed response formatting)
```

### 4. **Multi-Jar Money Addition Tool**

#### `add_money_to_jar()` - Enhanced for Multiple Additions
```python
@tool
def add_money_to_jar(
    jar_name: List[str],                    # List of jar names
    percent: List[Optional[float]] = None,  # List of percentages to add
    amount: List[Optional[float]] = None,   # List of dollar amounts to add
    description: str = "Money added"        # Description of addition
) -> str:
    """Add money to one or multiple jars (overflow allowed with warnings)"""
    
    # Comprehensive validation for multi-jar money addition
    # Atomic operations with overflow detection
    # Enhanced response formatting with individual jar status
    # ... (detailed implementation)
```

## 🔄 Advanced Rebalancing System

### Rebalancing Algorithms:

#### **1. New Jar Creation Rebalancing:**
```python
def rebalance_jar_percentages(new_jar_percent: float) -> str:
    """Proportionally reduce all existing jars to make room for new jar"""
    
    existing_jars = fetch_existing_jars()
    current_total = sum(jar["percent"] for jar in existing_jars)
    
    # Calculate scaling factor to maintain 100% total
    remaining_percent = 1.0 - new_jar_percent
    scale_factor = remaining_percent / current_total
    
    rebalanced_jars = []
    for jar in existing_jars:
        old_percent = jar["percent"]
        jar["percent"] = old_percent * scale_factor
        
        rebalanced_jars.append({
            'name': jar["name"],
            'old_percent': old_percent,
            'new_percent': jar["percent"]
        })
    
    # Format rebalancing message
    rebalance_details = []
    for rebalanced in rebalanced_jars:
        rebalance_details.append(
            f"{rebalanced['name']} ({format_percent_display(rebalanced['old_percent'])} → "
            f"{format_percent_display(rebalanced['new_percent'])})"
        )
    
    return f"📊 Rebalancing applied: {', '.join(rebalance_details)}"
```

#### **2. Multi-Jar Creation Rebalancing:**
```python
def rebalance_multiple_new_jars(total_new_percent: float) -> str:
    """Handle rebalancing when creating multiple jars simultaneously"""
    
    if total_new_percent <= 0:
        return ""
    
    existing_jars = fetch_existing_jars()
    if not existing_jars:
        return ""
    
    current_total = sum(jar["percent"] for jar in existing_jars)
    
    # Calculate scaling factor for all existing jars
    remaining_percent = 1.0 - total_new_percent
    scale_factor = remaining_percent / current_total
    
    # Apply scaling to all existing jars
    rebalanced_jars = []
    for jar in existing_jars:
        old_percent = jar["percent"]
        jar["percent"] = old_percent * scale_factor
        
        rebalanced_jars.append({
            'name': jar["name"],
            'old_percent': old_percent,
            'new_percent': jar["percent"]
        })
    
    # Format comprehensive rebalancing message
    rebalance_details = []
    for rebalanced in rebalanced_jars:
        rebalance_details.append(
            f"{rebalanced['name']} ({format_percent_display(rebalanced['old_percent'])} → "
            f"{format_percent_display(rebalanced['new_percent'])})"
        )
    
    return f"📊 Rebalancing applied: {', '.join(rebalance_details)}"
```

#### **3. Jar Deletion Redistribution:**
```python
def redistribute_deleted_jar_percentage(deleted_percent: float) -> str:
    """Proportionally distribute freed percentage to remaining jars"""
    
    if deleted_percent <= 0:
        return ""
    
    remaining_jars = fetch_existing_jars()
    if not remaining_jars:
        return ""
    
    current_total = sum(jar["percent"] for jar in remaining_jars)
    
    # Calculate distribution factor
    distribution_factor = 1.0 + (deleted_percent / current_total)
    
    # Apply to all remaining jars
    redistributed_jars = []
    for jar in remaining_jars:
        old_percent = jar["percent"]
        jar["percent"] = old_percent * distribution_factor
        
        redistributed_jars.append({
            'name': jar["name"],
            'old_percent': old_percent,
            'new_percent': jar["percent"]
        })
    
    # Format redistribution message
    redistribution_details = []
    for redistributed in redistributed_jars:
        redistribution_details.append(
            f"{redistributed['name']} ({format_percent_display(redistributed['old_percent'])} → "
            f"{format_percent_display(redistributed['new_percent'])})"
        )
    
    return f"📊 Percentage redistributed: {', '.join(redistribution_details)}"
```

## 📋 Enhanced System Responses

### Multi-Jar Operation Examples:

#### **Multi-Jar Creation:**
```
Input: "Create vacation and emergency jars with $500 each"
Output: "✅ Created 2 jars: vacation (10.0%, $500.00), emergency (10.0%, $500.00). 
         Total new allocation: 20.0%. 
         📊 Rebalancing applied: necessities (55.0% → 44.0%), play (10.0% → 8.0%), 
         education (10.0% → 8.0%), financial_freedom (10.0% → 8.0%), give (5.0% → 4.0%), 
         long_term_savings_for_spending (10.0% → 8.0%) (90% confident)"
```

#### **Multi-Jar Updates:**
```
Input: "Update vacation to 15% and emergency to 12%"
Output: "✅ Updated 2 jars: vacation (10.0% → 15.0%), emergency (10.0% → 12.0%). 
         Net change: +7.0%. 
         📊 Rebalancing applied: other jars scaled down proportionally to accommodate increase 
         (85% confident)"
```

#### **Multi-Jar Money Addition with Overflow:**
```
Input: "Add $200 to play jar and $300 to education jar"
Output: "✅ Added money to 2 jars: play: +$200.00 (4.0%) → $600.00 (12.0%) ⚠️ Overflow: $100.00 (2.0%); 
         education: +$300.00 (6.0%) → $800.00 (16.0%) ⚠️ Overflow: $300.00 (6.0%). Money added"
```

## 🧪 Testing Scenarios

### Enhanced Test Cases:

#### **Single Operations:**
```python
test_scenarios = [
    "List my jars",                                    # Show current state
    "Create vacation jar with $750 budget",           # Single creation
    "Update vacation jar to 12%",                     # Single update
    "Add $100 to vacation jar",                       # Single money addition
    "Delete vacation jar because trip cancelled",     # Single deletion
]
```

#### **Multi-Jar Operations:**
```python
multi_jar_scenarios = [
    "Create vacation and emergency jars with 8% each",              # Multi creation
    "Update vacation to 10% and emergency to 15%",                 # Multi update
    "Add $150 to play jar and $200 to education jar",             # Multi money addition
    "Delete vacation and emergency jars because priorities changed", # Multi deletion
]
```

#### **Vietnamese Language Support:**
```python
vietnamese_scenarios = [
    "Tạo hũ du lịch và hũ khẩn cấp với 10% mỗi cái",              # Create vacation and emergency
    "Thêm 200 đô vào hũ giải trí và 150 đô vào hũ học tập",       # Add money to play and education
    "Cập nhật hũ du lịch lên 15%",                                 # Update vacation to 15%
]
```

This enhanced multi-jar system provides comprehensive jar management with enterprise-grade validation, automatic rebalancing, and full support for T. Harv Eker's 6-jar money management philosophy.
