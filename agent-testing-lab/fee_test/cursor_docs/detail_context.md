# Fee Manager Agent Test Lab - Detailed Context

## 🎯 Project Overview

This is a **fee manager testing lab** for an LLM-powered agent that analyzes natural language descriptions of recurring fees and creates structured schedule patterns using Gemini LLM with LangChain tool calling. The system focuses on pattern recognition accuracy and schedule calculation correctness.

## 🏗️ Current System Architecture

### Core Components:
```
📁 fee_test/
├── 🧠 main.py           # LLM setup, tool execution, debug output
├── 🛠️ tools.py          # LangChain tools, RecurringFee class, mock data
├── 📝 prompt.py         # Fee parsing prompt with pattern examples
├── ⚙️ config.py         # Gemini API configuration and thresholds
├── 🧪 test.py          # Interactive testing interface
├── 📋 requirements.txt  # Dependencies (langchain-google-genai, etc.)
└── 📁 cursor_docs/     # Documentation for AI assistants
```

### LLM-Powered Tool Calling Flow:
```
User Fee Input ("phí đi lại hằng tuần 25k từ thứ 2 đến thứ 6")
         ↓
fetch_existing_fees() + fetch_available_jars()
         ↓
build_fee_manager_prompt(user_input, existing_fees, available_jars)
         ↓
llm_with_tools.invoke([HumanMessage(content=full_prompt)])
         ↓
LLM analyzes pattern and calls: create_recurring_fee(
    name="Phí đi lại hàng tuần", 
    amount=25.0, 
    pattern_type="weekly", 
    pattern_details={"days": [1,2,3,4,5]}, 
    target_jar="transport", 
    confidence=95
)
         ↓
Tool execution + calculate_next_occurrence() + save_recurring_fee()
         ↓
Response: "✅ Created recurring fee: Phí đi lại hàng tuần - $25.0 weekly → transport jar. Next: 2025-07-09 (95% confident)"
```

### Implementation with Confidence-Based Responses:
```python
def process_fee_request(user_input: str, llm_with_tools) -> str:
    # 1. Fetch context data
    existing_fees = fetch_existing_fees()
    available_jars = fetch_available_jars()
    
    # 2. Build complete prompt with pattern examples
    full_prompt = build_fee_manager_prompt(user_input, existing_fees, available_jars)
    
    # 3. Send to Gemini with bound tools
    response = llm_with_tools.invoke([HumanMessage(content=full_prompt)])
    
    # 4. Execute tool calls (handle multiple tool calls)
    if response.tool_calls:
        results = []
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Execute the tool function
            tool_function = get_tool_by_name(tool_name)
            result = tool_function(**tool_args)
            results.append(result)
        
        return combine_results(results)
    else:
        raise ValueError("LLM did not use any tools")
```

## 📅 Current RecurringFee Data Structure

### RecurringFee Class Implementation:
```python
@dataclass
class RecurringFee:
    name: str                  # Human-friendly name (LLM can remember this)
    amount: float              # Amount charged per occurrence
    description: str           # Detailed description of the fee
    target_jar: str            # Budget jar to charge (meals, transport, utilities)
    pattern_type: str          # "daily", "weekly", "monthly", "biweekly"
    pattern_details: dict      # Schedule-specific configuration (validated as dict)
    created_date: datetime     # When fee was created
    next_occurrence: datetime  # Next time fee should be processed
    last_occurrence: Optional[datetime] = None  # Track when last applied
    end_date: Optional[datetime] = None         # Support for finite fees
    is_active: bool = True     # Whether fee is currently active
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'amount': self.amount,
            'description': self.description,
            'target_jar': self.target_jar,
            'pattern_type': self.pattern_type,
            'pattern_details': self.pattern_details,
            'created_date': self.created_date.isoformat(),
            'next_occurrence': self.next_occurrence.isoformat(),
            'last_occurrence': self.last_occurrence.isoformat() if self.last_occurrence else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active
        }
```

### Current Pattern Types and Details:

#### **Daily Pattern:**
```python
RecurringFee(
    pattern_type="daily",
    pattern_details={},  # Empty dict for daily fees
    # Next occurrence: from_date + 1 day
)

# Example: "5 dollar daily for coffee"
```

#### **Weekly Pattern:**
```python
RecurringFee(
    pattern_type="weekly", 
    pattern_details={
        "days": [1, 2, 3, 4, 5]  # Monday=1, Tuesday=2, ..., Sunday=7
    },
    # Next occurrence: next occurrence of any specified day
)

# Example: "phí đi lại hằng tuần 25k từ thứ 2 đến thứ 6" (Monday to Friday)
```

#### **Monthly Pattern:**
```python
RecurringFee(
    pattern_type="monthly",
    pattern_details={
        "date": 15  # 15th of every month
    },
    # Next occurrence: 15th of next month
)

# Example: "50 dollar every 15th for insurance"
```

#### **Bi-weekly Pattern:**
```python
RecurringFee(
    pattern_type="biweekly",
    pattern_details={
        "day": 1,  # Monday (1=Mon, 2=Tue, ..., 7=Sun)
        "start_date": "2024-02-19"  # Reference start date
    },
    # Next occurrence: every 2 weeks from start_date on specified day
)

# Example: "30 dollar every other Monday for cleaning service"
```

## 🛠️ Current LLM Tools Implementation

### Core Fee Management Tools:
```python
@tool
def create_recurring_fee(
    name: str,           # Human-friendly name for the fee
    amount: float,       # Amount per occurrence
    description: str,    # Detailed description of the fee
    pattern_type: str,   # "daily", "weekly", "monthly", "biweekly"
    pattern_details: dict, # Schedule configuration (validated as dict)
    target_jar: str,     # Budget jar to charge
    confidence: int      # LLM confidence in pattern recognition (0-100)
) -> str:
    """Create a new recurring fee with specified schedule pattern"""
    
    # Validate pattern_details type (no fallbacks in development)
    if isinstance(pattern_details, str):
        pattern_details = json.loads(pattern_details)  # Let this fail if invalid JSON
    
    if not isinstance(pattern_details, dict):
        raise TypeError(f"create_recurring_fee: pattern_details must be dict, got {type(pattern_details)}: {pattern_details}")
    
    # Create and save fee
    fee = RecurringFee(
        name=name.strip(),
        amount=amount,
        description=description,
        target_jar=target_jar,
        pattern_type=pattern_type,
        pattern_details=pattern_details,
        created_date=datetime.now(),
        next_occurrence=calculate_next_occurrence(pattern_type, pattern_details),
        is_active=True
    )
    
    save_recurring_fee(fee)
    
    # Return confidence-based response
    if confidence >= 90:
        return f"✅ Created recurring fee: {name} - ${amount} {pattern_type} → {target_jar} jar. Next: {fee.next_occurrence.strftime('%Y-%m-%d')} ({confidence}% confident)"
    elif confidence >= 70:
        return f"⚠️ Created recurring fee: {name} - ${amount} {pattern_type} → {target_jar} jar. Next: {fee.next_occurrence.strftime('%Y-%m-%d')} ({confidence}% confident - moderate certainty)"
    else:
        return f"❓ Created recurring fee: {name} - ${amount} {pattern_type} → {target_jar} jar. Next: {fee.next_occurrence.strftime('%Y-%m-%d')} ({confidence}% confident - please verify)"

@tool
def adjust_recurring_fee(
    fee_name: str,
    new_amount: Optional[float] = None,
    new_description: Optional[str] = None,
    new_pattern_type: Optional[str] = None,
    new_pattern_details: Optional[dict] = None,
    new_target_jar: Optional[str] = None,
    disable: bool = False,
    confidence: int = 85
) -> str:
    """Adjust an existing recurring fee"""

@tool
def delete_recurring_fee(fee_name: str, reason: str) -> str:
    """Delete (deactivate) a recurring fee"""

@tool
def list_recurring_fees(active_only: bool = True, target_jar: Optional[str] = None) -> str:
    """List all recurring fees with optional filters"""

@tool
def request_clarification(question: str, suggestions: Optional[str] = None) -> str:
    """Ask user for clarification when input is unclear"""
```

### Current Budget Jars Database:
```python
JARS_DATABASE = [
    {
        "name": "meals", 
        "budget": 500, 
        "current": 212, 
        "description": "Dining out, food delivery, and coffee shop purchases"
    },
    {
        "name": "transport", 
        "budget": 300, 
        "current": 89, 
        "description": "Public transportation, ride-sharing, gas, and parking fees"
    },
    {
        "name": "utilities", 
        "budget": 200, 
        "current": 156, 
        "description": "Internet, phone, streaming subscriptions, and insurance"
    }
]
```

### Utility Functions:
```python
def calculate_next_occurrence(pattern_type: str, pattern_details: dict, from_date: datetime = None) -> datetime:
    """Calculate when fee should next occur based on pattern"""
    
    # Handle LangChain serialization issues
    if isinstance(pattern_details, str):
        pattern_details = json.loads(pattern_details)  # Let this fail if invalid JSON
    
    if not isinstance(pattern_details, dict):
        raise TypeError(f"pattern_details must be dict, got {type(pattern_details)}: {pattern_details}")
    
    if from_date is None:
        from_date = datetime.now()
    
    if pattern_type == "daily":
        return from_date + timedelta(days=1)
        
    elif pattern_type == "weekly":
        days = pattern_details.get("days", [1])  # Default to Monday
        current_weekday = from_date.weekday() + 1  # Monday=1
        
        # Find next occurrence of any specified day
        next_days = [d for d in days if d > current_weekday]
        if next_days:
            days_until = min(next_days) - current_weekday
        else:
            # Next week, first day
            days_until = 7 - current_weekday + min(days)
        return from_date + timedelta(days=days_until)
        
    elif pattern_type == "monthly":
        target_date = pattern_details.get("date", from_date.day)
        if from_date.day < target_date:
            # This month
            try:
                return from_date.replace(day=target_date)
            except ValueError:
                # Handle month-end edge cases (e.g., Feb 31st)
                next_month = from_date.replace(day=1) + timedelta(days=32)
                last_day = (next_month.replace(day=1) - timedelta(days=1)).day
                return from_date.replace(day=min(target_date, last_day))
        else:
            # Next month
            next_month = from_date.replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)
            try:
                return next_month.replace(day=target_date)
            except ValueError:
                # Handle month-end edge cases
                month_after = next_month.replace(day=1) + timedelta(days=32)
                last_day = (month_after.replace(day=1) - timedelta(days=1)).day
                return next_month.replace(day=min(target_date, last_day))
            
    elif pattern_type == "biweekly":
        target_day = pattern_details.get("day", 1)  # Monday
        start_date_str = pattern_details.get("start_date", from_date.isoformat()[:10])
        start_date = datetime.fromisoformat(start_date_str)
        
        # Calculate weeks since start
        weeks_since = (from_date - start_date).days // 7
        next_occurrence_week = ((weeks_since // 2) + 1) * 2
        
        return start_date + timedelta(weeks=next_occurrence_week)
    
    # Default fallback
    return from_date + timedelta(days=1)
```

## 🧪 Current LLM Pattern Recognition Scenarios

### Vietnamese Language Support:
```python
Input: "phí đi lại hằng tuần 25k từ thứ 2 đến thứ 6"
LLM Process:
1. Parses "25k" → amount: 25.0 (k = thousand in Vietnamese context)
2. Parses "hằng tuần" → pattern_type: "weekly"
3. Parses "từ thứ 2 đến thứ 6" → pattern_details: {"days": [1,2,3,4,5]}
4. Parses "phí đi lại" → description: "transport fee", target_jar: "transport"
5. Calls create_recurring_fee(name="Phí đi lại hàng tuần", amount=25.0, description="transport fee", pattern_type="weekly", pattern_details={"days": [1,2,3,4,5]}, target_jar="transport", confidence=95)

Result: ✅ Created recurring fee: Phí đi lại hàng tuần - $25.0 weekly → transport jar. Next: 2025-07-09 (95% confident)
```

### Complex Weekly Pattern:
```python
Input: "10 dollar every Monday and Friday for commute"
LLM Process:
1. Parses "10 dollar" → amount: 10.0
2. Parses "Monday and Friday" → pattern_type: "weekly", pattern_details: {"days": [1, 5]}
3. Parses "commute" → description: "commute", target_jar: "transport"
4. Calls create_recurring_fee(..., confidence=90)

Result: ✅ Created recurring fee: Weekly commute - $10.0 weekly → transport jar. Next: 2025-07-11 (90% confident)
```

### Monthly Pattern with Specific Date:
```python
Input: "50 dollar every 15th for insurance"
LLM Process:
1. Parses "50 dollar" → amount: 50.0
2. Parses "every 15th" → pattern_type: "monthly", pattern_details: {"date": 15}
3. Parses "insurance" → description: "insurance", target_jar: "utilities"
4. Calls create_recurring_fee(..., confidence=85)

Result: ✅ Created recurring fee: Insurance fee - $50.0 monthly → utilities jar. Next: 2025-08-15 (85% confident)
```

## 🔧 Development Features

### Enhanced Debug Output in get_fee_summary():
```python
def get_fee_summary() -> str:
    """Get a detailed summary of all current fees for development tracking"""
    
    fees = fetch_existing_fees()
    active_fees = [f for f in fees if f.is_active]
    inactive_fees = [f for f in fees if not f.is_active]
    
    print(f"\n🔍 DEBUG: Total fees in storage: {len(fees)}")
    print(f"🔍 DEBUG: Active fees: {len(active_fees)}")
    print(f"🔍 DEBUG: Inactive fees: {len(inactive_fees)}")
    
    for i, fee in enumerate(active_fees):
        print(f"\n🔍 DEBUG Fee {i+1}: {fee.name}")
        print(f"   Type: {type(fee.pattern_details)} = {fee.pattern_details}")
        print(f"   Pattern: {fee.pattern_type}")
        print(f"   Amount: ${fee.amount}")
        print(f"   Jar: {fee.target_jar}")
        
        # Show monthly calculations for each pattern type
        if fee.pattern_type == "weekly":
            pattern_details = fee.pattern_details
            print(f"   Raw pattern_details: {type(pattern_details)} = {pattern_details}")
            days_count = len(pattern_details.get("days", [1]))
            monthly_amount = fee.amount * days_count * 4
            print(f"   Monthly calc (weekly): ${fee.amount} * {days_count} * 4 = ${monthly_amount}")
```

### No Fallback Error Handling:
```python
# All functions raise actual errors instead of returning error strings
except Exception as e:
    # During development, show full error details
    import traceback
    error_details = traceback.format_exc()
    print(f"\n🐛 DEVELOPMENT ERROR:\n{error_details}")
    raise e  # Re-raise the exception instead of returning a string
```

### Type Safety for Pattern Details:
```python
# Handle LangChain tool parameter serialization issues
if isinstance(pattern_details, str):
    pattern_details = json.loads(pattern_details)  # Let this fail if invalid JSON

if not isinstance(pattern_details, dict):
    raise TypeError(f"pattern_details must be dict, got {type(pattern_details)}: {pattern_details}")
```

## 📊 Current Mock Data

### Sample Existing Fees:
```python
def initialize_mock_data():
    """Initialize some mock fees for testing"""
    
    now = datetime.now()
    
    # Daily coffee
    fee1 = RecurringFee(
        name="Daily coffee",
        amount=5.0,
        description="Morning coffee from the office cafe",
        target_jar="meals",
        pattern_type="daily",
        pattern_details={},
        created_date=now,
        next_occurrence=calculate_next_occurrence("daily", {}, now),
        is_active=True
    )
    
    # Weekly bus fare (weekdays)
    fee2 = RecurringFee(
        name="Bus fare",
        amount=10.0,
        description="Bus fare for work commute - weekdays only",
        target_jar="transport",
        pattern_type="weekly",
        pattern_details={"days": [1, 2, 3, 4, 5]},
        created_date=now,
        next_occurrence=calculate_next_occurrence("weekly", {"days": [1, 2, 3, 4, 5]}, now),
        is_active=True
    )
    
    # Monthly YouTube Premium
    fee3 = RecurringFee(
        name="YouTube Premium",
        amount=15.99,
        description="YouTube Premium subscription for ad-free videos",
        target_jar="utilities",
        pattern_type="monthly",
        pattern_details={"date": 5},
        created_date=now,
        next_occurrence=calculate_next_occurrence("monthly", {"date": 5}, now),
        is_active=True
    )
```

## 🎯 Current Testing Focus Areas

### Pattern Recognition Accuracy:
- **Vietnamese language support** - "phí đi lại hằng tuần 25k từ thứ 2 đến thứ 6"
- **Complex weekly patterns** - "Monday and Friday" vs "weekdays"
- **Monthly date handling** - edge cases like Feb 31st
- **Amount format parsing** - "25k", "10 dollar", various currencies

### Schedule Calculation Correctness:
- **Next occurrence logic** - accurate date calculations for all pattern types
- **Edge case handling** - month-end dates, leap years
- **Pattern synchronization** - bi-weekly start date alignment

### Tool Calling Consistency:
- **Parameter type validation** - ensure pattern_details is always a dict
- **Confidence score usage** - appropriate confidence levels for different scenarios
- **Error handling** - all errors exposed for development debugging

### Development Debugging:
- **Enhanced debug output** - track all data transformations
- **Type safety validation** - prevent LangChain serialization issues
- **No fallback masking** - all errors visible for debugging

Remember: This is a **development testing lab** for LLM-powered fee pattern recognition and schedule management!
