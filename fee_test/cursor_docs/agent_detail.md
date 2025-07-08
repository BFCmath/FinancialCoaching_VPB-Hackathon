reading: [text](for_ai.md)
reading: [text](detail_context.md)

> reading all files I sent
> Always reading to confirm instead of asssuming wrong context
> avoid hallucination efffectively by reading lines by lines and take note as you go

# Fee Manager Agent - Detailed Specifications

## 🎯 Agent Purpose

The **fee_manager** is an **LLM-powered agent** using **Gemini 2.5 Flash Lite** that analyzes natural language descriptions of recurring fees and creates structured schedule patterns through LangChain tool calling. The LLM processes fee descriptions, determines appropriate patterns, and calls tools to manage RecurringFee objects with calculated schedules.

## 🧠 Current LLM Implementation

### How It Works:
- **Natural language parsing**: Extract amount, pattern, and purpose from user input
- **Context fetching**: Get current recurring fees and available budget jars
- **Prompt building**: Combine user input + existing context + pattern examples + available tools
- **Gemini tool calling**: LLM analyzes input and calls appropriate fee management tools
- **Schedule calculation**: Tools calculate next occurrence dates based on pattern types
- **Confidence-based responses**: Different output formats based on LLM confidence levels

### Current System Process:
1. **Input Analysis**: Parse fee descriptions in English and Vietnamese
2. **Context Gathering**: Fetch existing fees and available jars from database
3. **LLM Processing**: Send complete prompt to Gemini with bound tools
4. **Tool Execution**: Execute LLM-selected tools with validated parameters
5. **Schedule Calculation**: Calculate next occurrence dates for all pattern types
6. **Response Generation**: Return confidence-based confirmations

## 🔍 Current LLM Tool Calling Process

### Input Processing Examples:
```python
# English patterns
"5 dollar daily for coffee"                        # Daily pattern
"10 dollar every Monday and Friday for commute"    # Weekly pattern with specific days
"50 dollar every 15th for insurance"              # Monthly pattern with date

# Vietnamese patterns  
"phí đi lại hằng tuần 25k từ thứ 2 đến thứ 6"     # Weekly Monday-Friday transport
"30k mỗi thứ hai cho xe buýt"                     # Weekly Monday bus fare

# Complex patterns
"every other Tuesday 25 dollar for cleaning"       # Bi-weekly pattern
"20 dollar weekdays for lunch"                     # Weekly Monday-Friday pattern
```

### Current Implementation Flow:
```python
def process_fee_request(user_input: str, llm_with_tools) -> str:
    # 1. Fetch all necessary context
    existing_fees = fetch_existing_fees()
    available_jars = fetch_available_jars()
    
    # 2. Build complete prompt with pattern examples and tool descriptions
    full_prompt = build_fee_manager_prompt(user_input, existing_fees, available_jars)
    
    # 3. Send to Gemini with tools bound via LangChain
    response = llm_with_tools.invoke([HumanMessage(content=full_prompt)])
    
    # 4. Execute tool calls with parameter validation
    if response.tool_calls:
        results = []
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Find and execute the tool function
            tool_function = get_tool_function_by_name(tool_name)
            result = tool_function(**tool_args)
            results.append(result)
        
        return combine_tool_results(results)
    else:
        raise ValueError("LLM did not use any tools")
```

## 🛠️ Current Tool Implementation

### 1. **Core Fee Management Tools (LLM calls these)**

#### `create_recurring_fee()`
```python
@tool
def create_recurring_fee(
    name: str,           # Human-friendly name for the fee
    amount: float,       # Amount per occurrence
    description: str,    # Detailed description
    pattern_type: str,   # "daily", "weekly", "monthly", "biweekly"
    pattern_details: dict, # Schedule configuration (validated as dict)
    target_jar: str,     # Budget jar to charge
    confidence: int      # LLM confidence (0-100)
) -> str:
    """Create a new recurring fee with specified schedule pattern"""
    
    # Type validation (no fallbacks - errors exposed for development)
    if isinstance(pattern_details, str):
        pattern_details = json.loads(pattern_details)  # Let this fail if invalid JSON
    
    if not isinstance(pattern_details, dict):
        raise TypeError(f"create_recurring_fee: pattern_details must be dict, got {type(pattern_details)}: {pattern_details}")
    
    # Create RecurringFee object
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
    
    # Save to in-memory storage
    save_recurring_fee(fee)
    
    # Return confidence-based response
    if confidence >= 90:
        return f"✅ Created recurring fee: {name} - ${amount} {pattern_type} → {target_jar} jar. Next: {fee.next_occurrence.strftime('%Y-%m-%d')} ({confidence}% confident)"
    elif confidence >= 70:
        return f"⚠️ Created recurring fee: {name} - ${amount} {pattern_type} → {target_jar} jar. Next: {fee.next_occurrence.strftime('%Y-%m-%d')} ({confidence}% confident - moderate certainty)"
    else:
        return f"❓ Created recurring fee: {name} - ${amount} {pattern_type} → {target_jar} jar. Next: {fee.next_occurrence.strftime('%Y-%m-%d')} ({confidence}% confident - please verify)"
```

#### `adjust_recurring_fee()`
```python
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
) -> str:
    """Adjust an existing recurring fee"""
```

#### `delete_recurring_fee()`
```python
@tool
def delete_recurring_fee(fee_name: str, reason: str) -> str:
    """Delete (deactivate) a recurring fee"""
```

#### `list_recurring_fees()`
```python
@tool
def list_recurring_fees(active_only: bool = True, target_jar: Optional[str] = None) -> str:
    """List all recurring fees with optional filters"""
```

#### `request_clarification()`
```python
@tool
def request_clarification(question: str, suggestions: Optional[str] = None) -> str:
    """Ask user for clarification when input is unclear"""
```

### 2. **Context Fetching Functions (Feed data to LLM)**

#### `fetch_existing_fees()`
```python
def fetch_existing_fees() -> List[RecurringFee]:
    """Get all current recurring fees for LLM context"""
    return list(FEES_STORAGE.values())
```

#### `fetch_available_jars()`
```python
def fetch_available_jars() -> List[Dict]:
    """Get available budget jars with descriptions for LLM context"""
    return [
        {"name": "meals", "budget": 500, "current": 212, "description": "Dining out, food delivery, and coffee shop purchases"},
        {"name": "transport", "budget": 300, "current": 89, "description": "Public transportation, ride-sharing, gas, and parking fees"},
        {"name": "utilities", "budget": 200, "current": 156, "description": "Internet, phone, streaming subscriptions, and insurance"}
    ]
```

### 3. **Schedule Calculation Logic**

#### `calculate_next_occurrence()`
```python
def calculate_next_occurrence(pattern_type: str, pattern_details: dict, from_date: datetime = None) -> datetime:
    """Calculate when fee should next occur based on pattern"""
    
    # Handle LangChain serialization issues (no fallbacks)
    if isinstance(pattern_details, str):
        pattern_details = json.loads(pattern_details)  # Let this fail if invalid JSON
    
    if not isinstance(pattern_details, dict):
        raise TypeError(f"pattern_details must be dict, got {type(pattern_details)}: {pattern_details}")
    
    if from_date is None:
        from_date = datetime.now()
    
    if pattern_type == "daily":
        return from_date + timedelta(days=1)
        
    elif pattern_type == "weekly":
        days = pattern_details.get("days", [1])  # Monday=1, ..., Sunday=7
        current_weekday = from_date.weekday() + 1
        
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
        # Handle month-end edge cases (e.g., Feb 31st)
        if from_date.day < target_date:
            try:
                return from_date.replace(day=target_date)
            except ValueError:
                next_month = from_date.replace(day=1) + timedelta(days=32)
                last_day = (next_month.replace(day=1) - timedelta(days=1)).day
                return from_date.replace(day=min(target_date, last_day))
        else:
            next_month = from_date.replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)
            try:
                return next_month.replace(day=target_date)
            except ValueError:
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

### Vietnamese Pattern - Working Example:
```python
Input: "phí đi lại hằng tuần 25k từ thứ 2 đến thứ 6"
LLM Analysis:
- Amount: 25.0 (k = thousand in Vietnamese context)
- Pattern: "hằng tuần" + "từ thứ 2 đến thứ 6" → pattern_type="weekly", pattern_details={"days": [1,2,3,4,5]}
- Description: "phí đi lại" (transport fee) → target_jar="transport"
- Confidence: High (95%) due to clear pattern

LLM Tool Call: create_recurring_fee(
    name="Phí đi lại hàng tuần",
    amount=25.0,
    description="Weekly transport fee from Monday to Friday",
    pattern_type="weekly",
    pattern_details={"days": [1,2,3,4,5]},
    target_jar="transport",
    confidence=95
)

System Response: "✅ Created recurring fee: Phí đi lại hàng tuần - $25.0 weekly → transport jar. Next: 2025-07-09 (95% confident)"
```

### Daily Pattern - Simple Creation:
```python
Input: "5 dollar daily for coffee"
LLM Analysis:
- Amount: 5.0
- Pattern: "daily" → pattern_type="daily", pattern_details={}
- Description: "coffee" → target_jar="meals"
- Confidence: High (95%) due to simple clear pattern

LLM Tool Call: create_recurring_fee(
    name="Daily coffee",
    amount=5.0,
    description="Daily coffee expense",
    pattern_type="daily",
    pattern_details={},
    target_jar="meals",
    confidence=95
)

System Response: "✅ Created recurring fee: Daily coffee - $5.0 daily → meals jar. Next: 2025-07-09 (95% confident)"
```

### Weekly Pattern with Multiple Days:
```python
Input: "10 dollar every Monday and Friday for commute"
LLM Analysis:
- Amount: 10.0
- Pattern: "Monday and Friday" → pattern_type="weekly", pattern_details={"days": [1, 5]}
- Description: "commute" → target_jar="transport"
- Confidence: High (90%) due to clear days specification

LLM Tool Call: create_recurring_fee(
    name="Weekly commute",
    amount=10.0,
    description="Commute fare on Monday and Friday",
    pattern_type="weekly",
    pattern_details={"days": [1, 5]},
    target_jar="transport",
    confidence=90
)

System Response: "✅ Created recurring fee: Weekly commute - $10.0 weekly → transport jar. Next: 2025-07-11 (90% confident)"
```

### Monthly Pattern with Specific Date:
```python
Input: "50 dollar every 15th for insurance"
LLM Analysis:
- Amount: 50.0
- Pattern: "every 15th" → pattern_type="monthly", pattern_details={"date": 15}
- Description: "insurance" → target_jar="utilities"
- Confidence: Medium (85%) due to clear monthly pattern

LLM Tool Call: create_recurring_fee(
    name="Insurance payment",
    amount=50.0,
    description="Monthly insurance payment",
    pattern_type="monthly",
    pattern_details={"date": 15},
    target_jar="utilities",
    confidence=85
)

System Response: "✅ Created recurring fee: Insurance payment - $50.0 monthly → utilities jar. Next: 2025-08-15 (85% confident)"
```

### Bi-weekly Pattern:
```python
Input: "30 dollar every other Monday for cleaning service"
LLM Analysis:
- Amount: 30.0
- Pattern: "every other Monday" → pattern_type="biweekly", pattern_details={"day": 1, "start_date": "2025-07-07"}
- Description: "cleaning service" → target_jar="utilities"
- Confidence: Medium (80%) due to biweekly complexity

LLM Tool Call: create_recurring_fee(
    name="Cleaning service",
    amount=30.0,
    description="Bi-weekly cleaning service",
    pattern_type="biweekly",
    pattern_details={"day": 1, "start_date": "2025-07-07"},
    target_jar="utilities",
    confidence=80
)

System Response: "⚠️ Created recurring fee: Cleaning service - $30.0 biweekly → utilities jar. Next: 2025-07-21 (80% confident - moderate certainty)"
```

### Ambiguous Pattern - Clarification Request:
```python
Input: "subscription for stuff"
LLM Analysis:
- Amount: unclear
- Pattern: unclear (could be monthly, but not specified)
- Description: "subscription for stuff" (too vague)
- Confidence: Low (30%) due to multiple ambiguities

LLM Tool Call: request_clarification(
    question="Could you provide more details about this subscription?",
    suggestions="Please specify: 1) How much does it cost? 2) How often is it charged? 3) What service is it for?"
)

System Response: "❓ Could you provide more details about this subscription?\n💡 Suggestions: Please specify: 1) How much does it cost? 2) How often is it charged? 3) What service is it for?"
```

## 🔧 Current Development Features

### Enhanced Debug Output:
```python
def get_fee_summary() -> str:
    """Get a detailed summary with debug information for development"""
    
    # Prints detailed debug information during execution:
    # 🔍 DEBUG: Total fees in storage: 3
    # 🔍 DEBUG: Active fees: 3
    # 🔍 DEBUG: Inactive fees: 0
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
except Exception as e:
    # During development, show full error details
    import traceback
    error_details = traceback.format_exc()
    print(f"\n🐛 DEVELOPMENT ERROR:\n{error_details}")
    raise e  # Re-raise the exception instead of masking
```

### Type Safety for Tool Parameters:
```python
# Handle LangChain tool parameter serialization issues
if isinstance(pattern_details, str):
    pattern_details = json.loads(pattern_details)  # Let this fail if invalid JSON

if not isinstance(pattern_details, dict):
    raise TypeError(f"pattern_details must be dict, got {type(pattern_details)}: {pattern_details}")
```

## 📅 Current RecurringFee Data Structure

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

### Current Pattern Types:

#### **Daily Pattern:**
```python
pattern_type: "daily"
pattern_details: {}  # Empty dict for daily fees
# Next occurrence: from_date + 1 day
```

#### **Weekly Pattern:**
```python
pattern_type: "weekly"
pattern_details: {"days": [1, 2, 3, 4, 5]}  # Monday=1 to Friday=5
# Next occurrence: next occurrence of any specified day
```

#### **Monthly Pattern:**
```python
pattern_type: "monthly"
pattern_details: {"date": 15}  # 15th of every month
# Next occurrence: 15th of next month (handles month-end edge cases)
```

#### **Bi-weekly Pattern:**
```python
pattern_type: "biweekly"
pattern_details: {"day": 1, "start_date": "2025-07-07"}  # Every other Monday
# Next occurrence: every 2 weeks from start_date on specified day
```

## 🎯 Current Testing Focus Areas

### Pattern Recognition Accuracy:
- **Vietnamese language support** - "phí đi lại hằng tuần 25k từ thứ 2 đến thứ 6"
- **Complex weekly patterns** - "Monday and Friday", "weekdays", specific day combinations
- **Monthly date handling** - edge cases like Feb 31st, end-of-month dates
- **Amount format parsing** - "25k", "10 dollar", various currency formats
- **Pattern ambiguity handling** - when to request clarification vs make assumptions

### Schedule Calculation Correctness:
- **Next occurrence logic** - accurate date calculations for all pattern types
- **Edge case handling** - month-end dates, leap years, weekend handling
- **Pattern synchronization** - bi-weekly start date alignment
- **Timezone considerations** - consistent datetime handling

### Tool Calling Consistency:
- **Parameter type validation** - ensure pattern_details is always a dict after LangChain serialization
- **Confidence score appropriateness** - LLM provides realistic confidence levels
- **Tool selection logic** - LLM chooses appropriate tools for different scenarios
- **Error handling transparency** - all errors exposed for development debugging

### Development Debugging Capabilities:
- **Enhanced debug output** - track all data transformations and calculations
- **Type safety validation** - prevent LangChain serialization issues
- **No fallback error masking** - all errors visible for debugging
- **Complete data inspection** - verify pattern_details structure and content

Remember: This is a **development testing lab** for LLM-powered fee pattern recognition, not a production recurring payment system!
