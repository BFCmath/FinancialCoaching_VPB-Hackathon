# AI Assistant Guide - Multi-Jar Manager System

## 🤖 Quick Start for AI Assistants

This is a **comprehensive multi-jar manager testing lab** featuring an LLM-powered agent that analyzes natural language jar operations and executes advanced CRUD commands using **Gemini LLM with LangChain tool calling**. The system implements **T. Harv Eker's official 6-jar money management system** with **multi-jar operations**, **automatic percentage rebalancing**, and **enterprise-grade validation**.

### Core Understanding
- **Multi-jar LLM system** - Gemini analyzes natural language and performs batch jar operations
- **T. Harv Eker's 6-jar system** - Official percentages with decimal format (0.0-1.0)
- **Automatic rebalancing** - Maintains 100% allocation across all jars
- **Multi-jar operations** - Create, update, and delete multiple jars simultaneously
- **Sample income** - $5,000 for realistic budget calculations
- **Simplified tool set** - Focus on core CRUD operations only

## 🎯 Primary Use Cases

### 1. Multi-Jar CRUD Operation Testing
Help users test advanced jar management by:
- **Single operations**: `"Create vacation jar with 15%"`
- **Multi-jar operations**: `"Create vacation and emergency jars with 10% each"`
- **Batch updates**: `"Update vacation to 8% and emergency to 12%"`
- **Multi-deletion**: `"Delete vacation and car repair jars"`

### 2. T. Harv Eker System Testing
Help users test the official 6-jar system by:
- **Default jars**: necessities (55%), long_term_savings (10%), play (10%), education (10%), financial_freedom (10%), give (5%)
- **Percentage validation**: Ensures total allocation equals 100%
- **Automatic rebalancing**: Proportional adjustment when jars are added/removed
- **Overflow handling**: Current amounts can exceed budget with warnings

### 3. Advanced Rebalancing Testing
Help users test automatic rebalancing by:
- **New jar creation**: Other jars scale down proportionally
- **Jar deletion**: Freed percentage redistributed to remaining jars
- **Percentage updates**: Automatic adjustment to maintain 100% total
- **Multi-jar operations**: Batch rebalancing for multiple simultaneous changes

## 🏗️ Current System Architecture

### Enhanced Multi-Jar Tool Calling System:
- **Gemini 2.5 Flash Lite** analyzes complex multi-jar operations
- **List-based inputs** for all CRUD operations (names, descriptions, percentages)
- **Atomic operations** - all succeed or all fail with rollback capability
- **Decimal percentages** - 0.0-1.0 format (0.1 = 10%, 0.55 = 55%)
- **Sample income** - $5,000 for realistic budget calculations

### Main Components:
```
📁 jar_test/
├── 🧠 main.py           # LLM setup + multi-jar tool execution + enhanced debug
├── 🛠️ tools.py          # Multi-jar tool definitions + rebalancing algorithms + T. Harv Eker system
├── 📝 prompt.py         # Enhanced prompt with multi-jar examples and rebalancing context
├── ⚙️ config.py         # Gemini API configuration + confidence thresholds
├── 🧪 test.py          # Interactive testing interface for multi-jar operations
├── 📋 requirements.txt  # Dependencies (langchain-google-genai, google-generativeai)
├── 🔧 env.example      # Environment variables template (GOOGLE_API_KEY, etc.)
└── 📁 cursor_docs/     # Updated documentation for multi-jar system
```

### Enhanced LLM Tool Calling Flow:
```
User Input ("Create vacation and emergency jars with $500 each")
         ↓
build_jar_manager_prompt(user_input, existing_jars, TOTAL_INCOME=$5000)
         ↓
llm_with_tools.invoke([HumanMessage(content=enhanced_prompt)])
         ↓
LLM analyzes and calls: create_jar(
    name=["vacation", "emergency"], 
    description=["Summer vacation", "Emergency savings"], 
    amount=[500, 500],  # $500 each = 10% each of $5000
    confidence=90
)
         ↓
Multi-jar tool execution + comprehensive validation + automatic rebalancing
         ↓ 
Response: "✅ Created 2 jars: vacation (10.0%, $500.00), emergency (10.0%, $500.00). 
          Rebalanced existing jars proportionally (90% confident)"
```

## 🏺 Enhanced Jar Data Structure

### Current Multi-Jar Implementation:
```python
# Simplified dictionary-based storage optimized for multi-jar operations
jar_data = {
    "name": str,                # Unique identifier (e.g., "vacation", "emergency")
    "description": str,         # Human-readable description
    "percent": float,          # Budget allocation (0.0-1.0, e.g., 0.15 = 15%)
    "current_percent": float   # Current balance as percentage (0.0-1.0, can exceed percent)
}

# Sample income for realistic calculations
TOTAL_INCOME = 5000.0

# Key conversion functions
calculate_budget_from_percent(0.15)      # Returns $750.00 (15% of $5000)
calculate_current_amount_from_percent(0.08)  # Returns $400.00 (8% of $5000)
calculate_percent_from_amount(500.0)     # Returns 0.10 (10% of $5000)
format_percent_display(0.15)            # Returns "15.0%"
```

### T. Harv Eker's Official 6-Jar System:
```python
DEFAULT_JARS = [
    {"name": "necessities", "description": "Essential living expenses", "percent": 0.55},           # 55%
    {"name": "long_term_savings", "description": "Major purchases", "percent": 0.10},               # 10%
    {"name": "play", "description": "Entertainment and fun activities", "percent": 0.10},          # 10%
    {"name": "education", "description": "Learning and skill development", "percent": 0.10},       # 10%
    {"name": "financial_freedom", "description": "Investments and passive income", "percent": 0.10}, # 10%
    {"name": "give", "description": "Charity and helping others", "percent": 0.05}                 # 5%
]
```

## 🛠️ Simplified Multi-Jar LLM Tools (4 Core Tools)

### Core Multi-Jar Management Tools:
```python
@tool
def create_jar(
    name: List[str],                    # List of jar names ["vacation", "emergency"]
    description: List[str],             # List of descriptions ["Summer trip", "Emergency fund"]
    percent: List[Optional[float]] = None,  # List of percentages [0.10, 0.15] (10%, 15%)
    amount: List[Optional[float]] = None,   # List of dollar amounts [500, 750]
    confidence: int = 85                # LLM confidence (0-100)
) -> str

@tool
def update_jar(
    jar_name: List[str],                        # List of jar names to update
    new_name: List[Optional[str]] = None,       # List of new names
    new_description: List[Optional[str]] = None, # List of new descriptions
    new_percent: List[Optional[float]] = None,   # List of new percentages
    new_amount: List[Optional[float]] = None,    # List of new amounts
    confidence: int = 85                        # LLM confidence
) -> str

@tool
def delete_jar(
    jar_name: List[str],     # List of jar names to delete ["vacation", "emergency"]
    reason: str              # Reason for deletion
) -> str

@tool
def list_jars() -> str    # Show all jars with percentages and calculated amounts

@tool
def request_clarification(question: str, suggestions: Optional[str] = None) -> str
```

**Note:** The `add_money_to_jar` tool has been removed for simplicity. Users who want to add money should use `update_jar` to increase percentage allocations instead.

### Enhanced Default Data:
```python
# T. Harv Eker's 6-jar system initialized by default
JARS_STORAGE = {
    "necessities": {"name": "necessities", "description": "Essential living expenses", "percent": 0.55, "current_percent": 0.33},
    "long_term_savings": {"name": "long_term_savings", "description": "Major purchases", "percent": 0.10, "current_percent": 0.04},
    "play": {"name": "play", "description": "Entertainment and fun", "percent": 0.10, "current_percent": 0.06},
    "education": {"name": "education", "description": "Learning and development", "percent": 0.10, "current_percent": 0.03},
    "financial_freedom": {"name": "financial_freedom", "description": "Investments", "percent": 0.10, "current_percent": 0.015},
    "give": {"name": "give", "description": "Charity and helping", "percent": 0.05, "current_percent": 0.005}
}
```

## 🧪 Multi-Jar Testing Scenarios

### Single Jar Operations:
```python
single_operations = [
    "List my jars",                                     # Show current 6-jar setup
    "Create vacation jar with 15%",                    # Single creation with percentage
    "Create emergency fund with $1000 budget",         # Single creation with amount
    "Update vacation jar to 12%",                      # Single percentage update
    "Delete vacation jar because trip cancelled",      # Single deletion
]
```

### Multi-Jar Operations:
```python
multi_operations = [
    # Multi-jar creation
    "Create vacation and emergency jars with 10% each",
    "Create car repair and home improvement jars with $500 each",
    
    # Multi-jar updates
    "Update vacation to 8% and emergency to 15%",
    "Change vacation jar to 12% and emergency jar to $1200",
    
    # Multi-jar deletion
    "Delete vacation and car repair jars because plans changed",
]
```

### T. Harv Eker System Operations:
```python
harv_eker_operations = [
    "Set up the 6-jar system",                         # Initialize complete system
    "Reset to T. Harv Eker's default jars",           # Reset to default configuration
    "Show jar summary",                                 # Display all 6 jars with status
]
```

### Vietnamese Language Support:
```python
vietnamese_operations = [
    "Tạo hũ du lịch với 15%",                          # Create vacation jar with 15%
    "Tạo hũ du lịch và hũ khẩn cấp với 10% mỗi cái",  # Create vacation and emergency jars with 10% each
    "Cập nhật hũ du lịch thành 12%",                   # Update vacation jar to 12%
]
```

## 📊 Automatic Rebalancing System

### Rebalancing Triggers:
1. **New jar creation** - Existing jars scale down proportionally to make room
2. **Jar deletion** - Freed percentage redistributed to remaining jars proportionally
3. **Percentage updates** - Other jars adjust to maintain 100% total

### Rebalancing Algorithm:
```python
def rebalance_jar_percentages(new_jar_percent: float) -> str:
    # Get existing jars (exclude newly created)
    existing_jars = [jar for jar in all_jars if jar != new_jar]
    existing_total = sum(jar['percent'] for jar in existing_jars)
    remaining_percent = 1.0 - new_jar_percent
    
    # Scale existing jars proportionally
    scale_factor = remaining_percent / existing_total
    for jar in existing_jars:
        jar['percent'] = max(0.01, jar['percent'] * scale_factor)  # Min 1%
    
    # Ensure total exactly equals 1.0
    adjust_rounding_errors()
```

### Example Rebalancing Scenario:
```
Initial State: necessities(55%), play(10%), education(10%), give(5%) = 80%
Add: vacation(20%)
Result: necessities(44%), play(8%), education(8%), give(4%), vacation(20%) = 100%
```

## 🔧 Enhanced Debug Features

### Function Call Tracing:
```python
🔧 AI Function Calls (1 call(s)):
==================================================

📞 Call 1: create_jar()
📋 Parameters:
   • name: ['vacation']
   • description: ['Summer vacation fund']
   • percent: [0.15]
   • confidence: 95

✅ Result: ✅ Created jar: vacation (15.0%, $750.00) (95% confident)
Rebalanced existing jars proportionally
==================================================
```

### Enhanced Error Messages:
- **Validation errors** with specific parameter details
- **Rebalancing notifications** with before/after percentages
- **Confidence scoring** with uncertainty warnings
- **Vietnamese language support** with proper UTF-8 handling

## 💡 AI Assistant Tips

### For Helping Users:
1. **Start with simple operations** - Single jar creation before multi-jar
2. **Explain rebalancing** - Users should understand automatic scaling
3. **Use clear examples** - Show both percentage and dollar amounts
4. **Test Vietnamese inputs** - Ensure UTF-8 support works correctly
5. **Focus on CRUD only** - No money addition tool anymore

### For Debugging:
1. **Check function calls** - Enhanced logging shows exact parameters
2. **Verify percentages** - Should always total 100% after operations
3. **Test edge cases** - Large percentages, negative amounts, empty inputs
4. **Validate rebalancing** - Ensure proportional scaling works correctly

### Common User Patterns:
- **"Create vacation jar with 15%"** → Single jar creation
- **"Create vacation and emergency jars with 10% each"** → Multi-jar creation
- **"Update vacation to 12%"** → Single jar update
- **"Delete vacation jar"** → Single jar deletion with rebalancing
- **"Show my jars"** → List current state

This system provides a robust foundation for testing multi-jar budget management with enterprise-level validation and user-friendly natural language processing.
