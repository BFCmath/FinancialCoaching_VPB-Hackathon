# AI Assistant Guide - Fee Manager Agent Test Lab

## 🤖 Quick Start for AI Assistants

This is a **fee manager testing lab** for an LLM-powered agent that analyzes recurring fee descriptions and creates structured schedule patterns using Gemini LLM with tool calling.

### Core Understanding
- **LLM-powered fee manager** - Gemini analyzes natural language and calls tools
- **Focus:** Test fee pattern recognition and schedule calculation accuracy
- **User philosophy:** Extreme simplicity, no over-engineering, development-focused debugging

## 🎯 Primary Use Cases

### 1. Fee Pattern Recognition Testing
Help users test fee parsing by:
- Running interactive tests via `python test.py`
- Testing natural language → structured pattern conversion
- Verifying schedule calculation logic

### 2. Tool Integration Testing  
Help users test LLM tool calling by:
- Testing fee creation via `create_recurring_fee()` tool
- Testing fee adjustment via `adjust_recurring_fee()` tool
- Testing fee deletion via `delete_recurring_fee()` tool
- Testing fee listing via `list_recurring_fees()` tool

### 3. Debug Output Analysis
Help users analyze system behavior by:
- Enhanced `get_fee_summary()` with detailed debug output
- No fallback error handling - all errors are exposed for development
- Complete data type and value tracking

## 🏗️ Current System Architecture

### LLM-Powered Tool Calling System:
- **Gemini 2.5 Flash Lite** analyzes natural language fee descriptions
- **LangChain tool binding** connects LLM to fee management functions
- **Confidence-based responses** with different output formats
- **No fallback error handling** - all errors exposed for debugging
- **Enhanced debug output** tracks all data transformations

### Main Components:
```
📁 fee_test/
├── 🧠 main.py           # LLM setup + tool execution + debug output
├── 🛠️ tools.py          # Tool definitions + RecurringFee class + mock data
├── 📝 prompt.py         # Fee parsing prompt with pattern examples
├── ⚙️ config.py         # Gemini API configuration
├── 🧪 test.py          # Interactive testing interface
└── 📋 requirements.txt  # Dependencies (langchain-google-genai, etc.)
```

### LLM Tool Calling Flow:
```
User Input ("phí đi lại hằng tuần 25k từ thứ 2 đến thứ 6")
         ↓
build_fee_manager_prompt(user_input, existing_fees, available_jars)
         ↓
llm_with_tools.invoke([HumanMessage(content=full_prompt)])
         ↓
LLM analyzes and calls: create_recurring_fee(name="Phí đi lại hàng tuần", amount=25.0, 
    pattern_type="weekly", pattern_details={"days": [1,2,3,4,5]}, target_jar="transport", confidence=95)
         ↓
Tool execution with schedule calculation
         ↓ 
Response: "✅ Created recurring fee: Phí đi lại hàng tuần - $25.0 weekly → transport jar. Next: 2025-07-09 (95% confident)"
```

## 🧪 RecurringFee Data Structure

### Current Implementation:
```python
@dataclass
class RecurringFee:
    name: str                  # Human-friendly name (LLM can remember this)
    amount: float              # Amount per occurrence
    description: str           # Detailed description
    target_jar: str            # Budget jar to charge
    pattern_type: str          # "daily", "weekly", "monthly", "biweekly"
    pattern_details: dict      # Schedule specifics (validated as dict)
    created_date: datetime     # When fee was created
    next_occurrence: datetime  # Next time fee is due
    last_occurrence: Optional[datetime] = None  # Track when last applied
    end_date: Optional[datetime] = None         # Support for finite fees
    is_active: bool = True     # Whether fee is currently active
```

### Current Pattern Support:

#### **Daily Patterns:**
```python
"5 dollar daily for coffee" → {
    pattern_type: "daily",
    pattern_details: {}  # Empty dict for daily
}
```

#### **Weekly Patterns:**
```python
"phí đi lại hằng tuần 25k từ thứ 2 đến thứ 6" → {
    pattern_type: "weekly", 
    pattern_details: {"days": [1,2,3,4,5]}  # Monday=1 to Friday=5
}
```

#### **Monthly Patterns:**
```python
"50 dollar every 15th for insurance" → {
    pattern_type: "monthly",
    pattern_details: {"date": 15}  # 15th of every month
}
```

#### **Bi-weekly Patterns:**
```python
"30 dollar every other Monday for cleaning" → {
    pattern_type: "biweekly",
    pattern_details: {"day": 1, "start_date": "2024-02-19"}
}
```

## 🛠️ Current LLM Tools

### Core Fee Management Tools:
```python
@tool
def create_recurring_fee(
    name: str,           # Human-friendly name for the fee
    amount: float,       # Amount per occurrence  
    description: str,    # Detailed description
    pattern_type: str,   # "daily", "weekly", "monthly", "biweekly"
    pattern_details: dict, # Schedule configuration
    target_jar: str,     # Budget jar to charge
    confidence: int      # LLM confidence (0-100)
) -> str

@tool
def adjust_recurring_fee(
    fee_name: str,                      # Name of fee to adjust
    new_amount: Optional[float] = None, # New amount
    new_description: Optional[str] = None, # New description
    new_pattern_type: Optional[str] = None, # New pattern
    new_pattern_details: Optional[dict] = None, # New schedule
    new_target_jar: Optional[str] = None, # New jar
    disable: bool = False,              # Whether to disable
    confidence: int = 85                # LLM confidence
) -> str

@tool
def delete_recurring_fee(fee_name: str, reason: str) -> str

@tool
def list_recurring_fees(active_only: bool = True, target_jar: Optional[str] = None) -> str

@tool
def request_clarification(question: str, suggestions: Optional[str] = None) -> str
```

### Current Budget Jars (Database Structure):
```python
JARS_DATABASE = [
    {"name": "meals", "budget": 500, "current": 212, "description": "Dining out, food delivery, and coffee shop purchases"},
    {"name": "transport", "budget": 300, "current": 89, "description": "Public transportation, ride-sharing, gas, and parking fees"},
    {"name": "utilities", "budget": 200, "current": 156, "description": "Internet, phone, streaming subscriptions, and insurance"}
]
```

## 🧪 Current Testing Scenarios

### Vietnamese Language Support:
```python
Input: "phí đi lại hằng tuần 25k từ thứ 2 đến thứ 6"
LLM Analysis:
- Amount: 25.0 (k = thousand)
- Pattern: "thứ 2 đến thứ 6" → pattern_type="weekly", days=[1,2,3,4,5]
- Description: "phí đi lại" (transport fee) → target_jar="transport"
Result: ✅ Created recurring fee: Phí đi lại hàng tuần - $25.0 weekly → transport jar. Next: 2025-07-09 (95% confident)
```

### High Confidence Pattern Recognition:
```python
Input: "5 dollar daily for coffee"
Result: ✅ Created recurring fee: Daily coffee - $5.0 daily → meals jar. Next: 2025-07-09 (95% confident)

Input: "10 dollar every Monday and Friday for commute"  
Result: ✅ Created recurring fee: Weekly commute - $10.0 weekly → transport jar. Next: 2025-07-11 (90% confident)
```

### Confidence-Based Output Formatting:
- **≥90% confident**: ✅ Green checkmark, direct confirmation
- **70-89% confident**: ⚠️ Orange warning, moderate certainty note
- **<70% confident**: ❓ Question mark, "please verify" note

## 🔧 Development Features

### Enhanced Debug Output:
```python
def get_fee_summary() -> str:
    # Prints detailed debug information:
    # 🔍 DEBUG: Total fees in storage: 3
    # 🔍 DEBUG Fee 1: Daily coffee
    #    Type: <class 'dict'> = {}
    #    Pattern: daily
    #    Amount: $5.0
    #    Jar: meals
    #    Monthly calc (daily): $5.0 * 30 = $150.0
```

### No Fallback Error Handling:
```python
# All functions raise actual errors instead of returning error strings
if not isinstance(pattern_details, dict):
    raise TypeError(f"pattern_details must be dict, got {type(pattern_details)}: {pattern_details}")

# Exception details printed for development
except Exception as e:
    import traceback
    error_details = traceback.format_exc()
    print(f"\n🐛 DEVELOPMENT ERROR:\n{error_details}")
    raise e  # Re-raise instead of masking
```

### Pattern Details Type Safety:
```python
# Handle LangChain serialization issues
if isinstance(pattern_details, str):
    pattern_details = json.loads(pattern_details)  # Let this fail if invalid JSON

if not isinstance(pattern_details, dict):
    raise TypeError(f"pattern_details must be dict, got {type(pattern_details)}: {pattern_details}")
```

## 🚨 Development Do's and Don'ts

### ✅ DO
- **Expose all errors** - no fallback masking during development
- **Use detailed debug output** - track all data transformations
- **Test pattern edge cases** - complex weekly patterns, Vietnamese language
- **Verify schedule calculations** - check next_occurrence logic
- **Test tool calling** - ensure LLM uses correct tools with proper parameters

### ❌ DON'T  
- **Add fallback error handling** - errors must be visible during development
- **Assume pattern_details types** - validate dict type after LangChain serialization
- **Create persistent storage** - use in-memory mock data only
- **Over-complicate patterns** - stick to basic daily/weekly/monthly/biweekly
- **Add production features** - this is a testing lab only

## 🎯 Success Criteria

The fee manager agent is working well when:
- ✅ **LLM correctly parses** natural language into structured patterns
- ✅ **Tools execute properly** with correct parameter types
- ✅ **Schedule calculation accurate** for all pattern types
- ✅ **Vietnamese language support** works correctly
- ✅ **Debug output helpful** for tracking system behavior
- ✅ **No hidden errors** - all issues exposed for development

Remember: This is a **development testing lab** for LLM-powered fee pattern recognition!
