# Transaction History Fetcher - Detailed Specifications

## 🎯 Agent Purpose

The **transaction_history_fetcher** is a **data-focused transaction retrieval agent** that fetches and presents transaction data using intelligent tool selection. It uses **LangChain tool binding** to automatically select and combine multiple transaction retrieval tools for both simple and complex queries, returning structured data with LLM-provided descriptions. **Now includes Vietnamese language support for complex financial queries.**

## 🧠 Multi-Tool Intelligence System

### Core Capabilities:
- **Smart Tool Selection**: LLM automatically chooses appropriate tools based on query analysis
- **Complexity Detection**: Automatically detects simple (1-2 filters) vs complex (3+ filters) queries
- **Vietnamese Query Support**: Handles Vietnamese financial queries with automatic translation
- **Multi-Tool Combination**: Handles complex queries requiring multiple data sources in single pass
- **LLM-Provided Descriptions**: Each tool call includes intent description for clarity
- **Structured Data Return**: Returns data with descriptions for user and agent understanding
- **Context-Aware Processing**: Understands current transaction landscape and user intent
- **Flexible Parameter Extraction**: Natural language to tool parameters conversion

### Single-Pass Architecture:
```
User Query → Complexity Detection → LLM Tool Selection → Multi-Tool Execution → Structured Data Return
```

## 🗂️ Transaction Data Model

### Transaction Structure:
```python
TRANSACTION = {
    "amount": float,         # Transaction amount in dollars
    "jar": str,             # Budget category/jar name
    "description": str,     # Transaction description
    "date": str,           # Date in YYYY-MM-DD format  
    "time": str,           # Time in HH:MM format (24-hour)
    "source": str          # Input source type
}
```

### Tool Result Structure:
```python
TOOL_RESULT = {
    "data": List[TRANSACTION],  # List of transaction dictionaries
    "description": str          # LLM-provided description of what the data represents
}
```

### Source Types:
- **`vpbank_api`**: Imported from VPBank API
- **`manual_input`**: Manually entered by user
- **`text_input`**: Text-based voice input
- **`image_input`**: Receipt/image processing

### Example Transactions:
```python
[
    {
        "amount": 25.50,
        "jar": "groceries", 
        "description": "Weekend grocery shopping",
        "date": "2024-02-15",
        "time": "10:30",
        "source": "vpbank_api"
    },
    {
        "amount": 12.00,
        "jar": "meals",
        "description": "Coffee and pastry",
        "date": "2024-02-15", 
        "time": "08:15",
        "source": "manual_input"
    }
]
```

## 🛠️ Transaction Retrieval Tools (6 Core Tools)

### **SIMPLE TOOLS (1-2 filters):**

### 1. **`get_jar_transactions(jar_name: str = None, limit: int = 50, description: str = "")`**

**Purpose:** Retrieve all transactions for a specific budget jar/category or all jars

**Parameters:**
- `jar_name`: Name of the jar (e.g., "groceries", "entertainment") or None for all jars
- `limit`: Maximum number of transactions to return (default: 50)
- `description`: LLM-provided description of what is being retrieved

**Returns:** `{"data": List[Dict], "description": str}` - Structured result with transactions and description

**Use Cases:**
- "Show me all my grocery spending" → `get_jar_transactions(jar_name="groceries", description="grocery spending")`
- "All transactions across all categories" → `get_jar_transactions(jar_name=None, description="all my transactions")`
- "List all transactions in my transportation jar" → `get_jar_transactions(jar_name="transportation", description="transportation spending")`

**LangChain Tool Implementation:**
```python
@tool
def get_jar_transactions(jar_name: str = None, limit: int = 50, description: str = "") -> Dict:
    """Get all transactions for a specific jar/category or all jars.
    
    Args:
        jar_name: The jar/category name to filter by, or None for all jars
        limit: Maximum number of transactions to return
        description: Description of what you're retrieving (e.g., "groceries spending")
    
    Returns:
        Dict with "data" (list of transactions) and "description" (intent description)
    """
    filtered_transactions = [
        t for t in all_transactions 
        if jar_name is None or t["jar"].lower() == jar_name.lower()
    ]
    
    auto_description = f"transactions from {jar_name or 'all'} jar"
    final_description = description if description else auto_description
    
    return {
        "data": filtered_transactions[:limit],
        "description": final_description
    }
```

### 2. **`get_time_period_transactions(jar_name: str = None, start_date: str = "last_month", end_date: str = None, limit: int = 50, description: str = "")`**

**Purpose:** Retrieve transactions within a specific time period, optionally filtered by jar

**Parameters:**
- `jar_name`: Name of the jar or None for all jars
- `start_date`: Start date (YYYY-MM-DD format) or relative ("last_month", "last_week")
- `end_date`: End date (optional, defaults to today)
- `limit`: Maximum number of transactions to return (default: 50)
- `description`: LLM-provided description of what is being retrieved

**Returns:** `{"data": List[Dict], "description": str}` - Structured result with transactions and description

**Use Cases:**
- "Show me last month's transactions" → `get_time_period_transactions(start_date="last_month", description="last month's transactions")`
- "What did I spend on groceries in February?" → `get_time_period_transactions(jar_name="groceries", start_date="2024-02-01", end_date="2024-02-28", description="February groceries")`
- "All entertainment expenses from last week" → `get_time_period_transactions(jar_name="entertainment", start_date="last_week", description="last week's entertainment")`

**Special Date Handling:**
```python
RELATIVE_DATES = {
    "today": datetime.now().date(),
    "yesterday": datetime.now().date() - timedelta(days=1),
    "last_week": datetime.now().date() - timedelta(weeks=1),
    "last_month": datetime.now().date() - timedelta(days=30),
    "this_month": datetime.now().replace(day=1).date()
}
```

### 3. **`get_amount_range_transactions(jar_name: str = None, min_amount: float = None, max_amount: float = None, limit: int = 50, description: str = "")`**

**Purpose:** Retrieve transactions within a specific amount range, optionally filtered by jar

**Parameters:**
- `jar_name`: Name of the jar or None for all jars
- `min_amount`: Minimum transaction amount (inclusive), None for no minimum
- `max_amount`: Maximum transaction amount (inclusive), None for no maximum
- `limit`: Maximum number of transactions (default: 50)
- `description`: LLM-provided description of what is being retrieved

**Returns:** `{"data": List[Dict], "description": str}` - Structured result with transactions and description

**Use Cases:**
- "Show me all purchases over $50" → `get_amount_range_transactions(min_amount=50, description="purchases over $50")`
- "Small entertainment transactions under $20" → `get_amount_range_transactions(jar_name="entertainment", max_amount=20, description="small entertainment purchases")`
- "Mid-range grocery spending between $30-80" → `get_amount_range_transactions(jar_name="groceries", min_amount=30, max_amount=80, description="mid-range grocery purchases")`

**Special Amount Handling:**
```python
# Handle None values for unlimited ranges
def filter_by_amount(transaction, min_amount, max_amount):
    amount = transaction["amount"]
    if min_amount is not None and amount < min_amount:
        return False
    if max_amount is not None and amount > max_amount:
        return False
    return True
```

### 4. **`get_hour_range_transactions(jar_name: str = None, start_hour: int = 6, end_hour: int = 22, limit: int = 50, description: str = "")`**

**Purpose:** Retrieve transactions within specific hours of the day for behavioral analysis

**Parameters:**
- `jar_name`: Name of the jar or None for all jars
- `start_hour`: Starting hour (0-23, 24-hour format)
- `end_hour`: Ending hour (0-23, inclusive)
- `limit`: Maximum number of transactions (default: 50)
- `description`: LLM-provided description of what is being retrieved

**Returns:** `{"data": List[Dict], "description": str}` - Structured result with transactions and description

**Use Cases:**
- "What do I buy in the morning?" → `get_hour_range_transactions(start_hour=6, end_hour=12, description="morning purchases")`
- "Evening entertainment spending patterns" → `get_hour_range_transactions(jar_name="entertainment", start_hour=18, end_hour=23, description="evening entertainment")`
- "Business hours vs after-hours transactions" → Multiple calls with appropriate descriptions

**Time Period Mapping:**
```python
TIME_PERIODS = {
    "morning": (6, 12),
    "afternoon": (12, 18), 
    "evening": (18, 23),
    "night": (23, 6),  # Special handling for overnight
    "business_hours": (9, 17),
    "weekend_hours": (10, 22)
}
```

### 5. **`get_source_transactions(jar_name: str = None, source_type: str = "vpbank_api", limit: int = 50, description: str = "")`**

**Purpose:** Retrieve transactions by input source/method, optionally filtered by jar

**Parameters:**
- `jar_name`: Name of the jar or None for all jars
- `source_type`: Type of transaction source
- `limit`: Maximum number of transactions (default: 50)
- `description`: LLM-provided description of what is being retrieved

**Valid Source Types:**
- `vpbank_api` - Bank imported transactions
- `manual_input` - Manually entered by user
- `text_input` - Voice/text input processing
- `image_input` - Receipt/image processing

**Returns:** `{"data": List[Dict], "description": str}` - Structured result with transactions and description

**Use Cases:**
- "Show me all manually entered transactions" → `get_source_transactions(source_type="manual_input", description="manually entered transactions")`
- "Bank imported grocery data only" → `get_source_transactions(jar_name="groceries", source_type="vpbank_api", description="bank imported groceries")`
- "Transactions from receipt scanning for entertainment" → `get_source_transactions(jar_name="entertainment", source_type="image_input", description="entertainment receipts")`

### **COMPLEX TOOL (3+ filters):**

### 6. **`get_complex_transaction(jar_name=None, start_date=None, end_date=None, min_amount=None, max_amount=None, start_hour=None, end_hour=None, source_type=None, limit=50, description="")`**

**Purpose:** **MULTI-DIMENSIONAL FILTERING** for complex queries requiring 3+ filter types simultaneously

**Use ONLY for complex queries with multiple filters:**

**Parameters:**
- `jar_name`: Budget jar name or None
- `start_date`: Start date filter (optional) - supports relative dates
- `end_date`: End date filter (optional)
- `min_amount`: Minimum amount filter (optional)
- `max_amount`: Maximum amount filter (optional)
- `start_hour`: Starting hour filter (24-hour format, optional)
- `end_hour`: Ending hour filter (24-hour format, optional)
- `source_type`: Transaction source filter (optional)
- `limit`: Maximum number of transactions (default: 50)
- `description`: LLM-provided description of what is being retrieved

**Returns:** `{"data": List[Dict], "description": str}` - Structured result with transactions matching ALL filters

**Vietnamese Query Examples:**

**1. "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"**
```python
# Translation: "show me lunch information (11am -> 2pm) under $20"
get_complex_transaction(
    jar_name="meals",
    start_hour=11,
    end_hour=14,
    max_amount=20,
    description="lunch transactions 11am-2pm under $20"
)
```

**2. "ăn sáng từ 6 giờ đến 10 giờ sáng dưới 15 đô"**
```python
# Translation: "breakfast from 6am to 10am under $15"
get_complex_transaction(
    jar_name="meals",
    start_hour=6,
    end_hour=10,
    max_amount=15,
    description="breakfast spending 6am-10am under $15"
)
```

**3. "mua sắm grocery buổi sáng dưới 100 đô từ bank data"**
```python
# Translation: "morning grocery shopping under $100 from bank data"
get_complex_transaction(
    jar_name="groceries",
    start_hour=6,
    end_hour=12,
    max_amount=100,
    source_type="vpbank_api",
    description="morning grocery shopping under $100 from bank"
)
```

**WHEN TO USE:**
- ✅ 3+ different filter types (jar + time + amount + hour)
- ✅ Vietnamese/multilingual complex queries  
- ✅ Time-specific category queries with amounts
- ✅ Multi-dimensional analysis requests

**WHEN NOT TO USE (use specific tools instead):**
- ❌ Simple single-filter queries: "groceries spending"
- ❌ Simple two-filter queries: "groceries last month"

**Implementation Example:**
```python
@tool
def get_complex_transaction(jar_name=None, start_date=None, end_date=None, 
                          min_amount=None, max_amount=None, start_hour=None, 
                          end_hour=None, source_type=None, limit=50, description="") -> Dict:
    """Multi-dimensional transaction filtering for complex queries."""
    
    filtered = []
    
    # Apply all filters step by step
    for transaction in MOCK_TRANSACTIONS:
        # 1. Check jar filter
        if jar_name is not None and transaction["jar"].lower() != jar_name.lower():
            continue
            
        # 2. Check date range filter
        if start_date is not None:
            # ... date filtering logic
            
        # 3. Check amount range filter
        if min_amount is not None and transaction["amount"] < min_amount:
            continue
        if max_amount is not None and transaction["amount"] > max_amount:
            continue
            
        # 4. Check hour range filter
        if start_hour is not None and end_hour is not None:
            # ... hour filtering logic
            
        # 5. Check source filter
        if source_type is not None and transaction.get("source") != source_type:
            continue
            
        filtered.append(transaction.copy())
    
    # Generate description and return structured result
    final_description = description if description else generate_auto_description(...)
    
    return {
        "data": filtered[:limit],
        "description": final_description
    }
```

## 🇻🇳 Vietnamese Language Support

### **Translation System:**
The agent automatically translates Vietnamese financial queries into appropriate tool parameters:

```python
VIETNAMESE_MAPPINGS = {
    # Meal times
    "ăn trưa": {"jar": "meals", "start_hour": 11, "end_hour": 14},  # lunch
    "ăn sáng": {"jar": "meals", "start_hour": 6, "end_hour": 10},   # breakfast
    "ăn tối": {"jar": "meals", "start_hour": 18, "end_hour": 22},   # dinner
    
    # Time expressions
    "11h sáng ->2h chiều": {"start_hour": 11, "end_hour": 14},
    "buổi sáng": {"start_hour": 6, "end_hour": 12},
    "buổi tối": {"start_hour": 18, "end_hour": 23},
    
    # Amount expressions
    "dưới 20 đô": {"max_amount": 20},
    "trên 30 đô": {"min_amount": 30},
    "từ 10 đến 50 đô": {"min_amount": 10, "max_amount": 50},
    
    # Categories
    "giải trí": {"jar": "entertainment"},
    "grocery": {"jar": "groceries"},
    "transportation": {"jar": "transportation"},
    
    # Sources
    "bank data": {"source_type": "vpbank_api"},
    "manual entry": {"source_type": "manual_input"}
}
```

### **Supported Vietnamese Patterns:**
- **Time periods**: "buổi sáng", "buổi chiều", "buổi tối"
- **Meal times**: "ăn sáng", "ăn trưa", "ăn tối"
- **Amount ranges**: "dưới X đô", "trên X đô", "từ X đến Y đô"
- **Categories**: "giải trí", "grocery", "transportation"
- **Mixed language**: Vietnamese with English terms (common usage)

## 🏷️ Description Parameter System

### **Critical Feature: LLM-Provided Descriptions**
Every tool now includes a `description` parameter where the LLM specifies what it's trying to retrieve. This enables:

#### **Multi-Tool Clarity Example:**
```python
# For query: "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"
get_complex_transaction(
    jar_name="meals",
    start_hour=11,
    end_hour=14,
    max_amount=20,
    description="lunch transactions 11am-2pm under $20"
)
# Result: {"data": [...], "description": "lunch transactions 11am-2pm under $20"}
```

#### **Benefits:**
- **Clear Intent** - Each tool call has explicit purpose
- **Vietnamese Support** - English descriptions for Vietnamese queries
- **User-Friendly** - Descriptions explain what each dataset represents
- **Agent-Ready** - Other agents can easily understand the data context
- **Multi-Tool Clarity** - Complex queries return multiple clearly labeled datasets

#### **Auto-Description Fallback:**
If no description is provided, tools auto-generate basic descriptions:
```python
auto_description = f"transactions from {jar_name or 'all'} jar"
if start_date:
    auto_description += f" from {start_date}"
if min_amount or max_amount:
    auto_description += f" with amount {min_amount}-{max_amount}"
final_description = description if description else auto_description
```

## 🧠 LangChain Tool Binding & Multi-Tool Intelligence

### **Tool Binding Implementation:**
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

# Bind all 6 tools to LLM
TRANSACTION_TOOLS = [
    get_jar_transactions,
    get_time_period_transactions,
    get_amount_range_transactions,
    get_hour_range_transactions,
    get_source_transactions,
    get_complex_transaction  # New complex tool
]

llm_with_tools = llm.bind_tools(TRANSACTION_TOOLS)
```

### **Intelligent Tool Selection Logic:**
```python
def select_appropriate_tool(query_complexity, filter_count, language):
    if filter_count >= 3 or language == "vietnamese":
        return "get_complex_transaction"
    elif filter_count == 2:
        return specific_tool_based_on_filters()
    else:  # filter_count == 1
        return simple_tool_based_on_filter_type()
```

### **Processing Flow:**
```
Vietnamese Query → Translation → Parameter Extraction → Complexity Detection → Tool Selection → Execution
```

## 🎯 Success Criteria

The transaction history fetcher is working well when:
- ✅ **Accurate complexity detection** and tool selection
- ✅ **Vietnamese query support** with proper translation and parameter extraction
- ✅ **Clear descriptions** provided for every tool call
- ✅ **Intelligent parameter extraction** from natural language
- ✅ **Effective multi-dimensional filtering** for complex requests
- ✅ **Structured data presentation** with descriptions and transaction lists
- ✅ **Fast response times** through single-pass processing
- ✅ **Service integration** capability for other agents

Remember: This agent provides the **data foundation** that powers informed financial decision-making across the entire system through fast, accurate transaction retrieval with clear descriptions and Vietnamese language support! 🇻🇳
