# Transaction History Fetcher - Implementation Context

## 🎯 Project Overview

This is a **transaction history fetcher agent** that provides fast, accurate transaction data retrieval using intelligent tool selection with LLM-provided descriptions and **Vietnamese language support**. The agent uses **LangChain tool binding** to automatically select and combine multiple transaction retrieval tools based on user queries, returning structured data with clear descriptions for both simple requests and complex multi-dimensional filtering.

## 🏗️ System Architecture

### Core Components:
```
📁 transaction_history_fetcher/
├── 🧠 main.py              # LangChain tool binding + execution pipeline with structured data return
├── 🛠️ tools.py             # 6 transaction retrieval tools (5 simple + 1 complex) with description parameters
├── 📝 prompt.py            # Context-rich prompts for intelligent tool selection and Vietnamese support
├── ⚙️ config.py            # Configuration management (API keys, settings)
├── 🧪 test.py             # Multi-tool scenario testing framework + Vietnamese query testing
├── 📋 env.example         # Environment template
└── 📁 cursor_docs/        # Documentation for AI assistants
```

### Single-Pass Processing Flow:
```
User Request ("cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô")
         ↓
Vietnamese Detection & Translation ("lunch 11am-2pm under $20")
         ↓
Complexity Detection (3+ filters: jar + hour + amount)
         ↓
Context Prompt Building (current jars + Vietnamese mappings + tool descriptions)
         ↓
LLM Tool Selection (get_complex_transaction automatically chosen)
         ↓
Tool Execution Pipeline (execute with Vietnamese-derived parameters)
         ↓
Structured Data Return (data with English description for Vietnamese query)
         ↓
Output: {
  "tool_name": "get_complex_transaction",
  "args": {"jar_name": "meals", "start_hour": 11, "end_hour": 14, "max_amount": 20},
  "data": [list_of_lunch_transactions],
  "description": "lunch transactions 11am-2pm under $20"
}
```

### LangChain Tool Binding Implementation:
```python
class TransactionHistoryFetcher:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite-preview-06-17",
            google_api_key=config.google_api_key,
            temperature=0.1
        )
        
        # Bind all 6 transaction tools (including complex tool) with description parameters to LLM
        self.llm_with_tools = self.llm.bind_tools([
            get_jar_transactions,
            get_time_period_transactions,
            get_amount_range_transactions,
            get_hour_range_transactions,
            get_source_transactions,
            get_complex_transaction  # New complex multi-dimensional tool
        ])
    
    def fetch_transaction_history(self, user_query: str) -> List[Dict]:
        # Build rich context prompt with Vietnamese support and complexity detection guidance
        system_prompt = build_history_fetcher_prompt(user_query, current_context)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query)
        ]
        
        # LLM automatically selects appropriate tools with descriptions and Vietnamese support
        response = self.llm_with_tools.invoke(messages)
        
        # Process tool calls and return structured data
        if response.tool_calls:
            return self.process_multi_tool_results(response.tool_calls, user_query)
        else:
            return []
```

## 🗂️ Transaction Data Model

### Complete Transaction Structure:
```python
TRANSACTION = {
    "amount": 25.50,                    # Dollar amount (float)
    "jar": "groceries",                 # Budget category/jar name
    "description": "Weekend grocery shopping", # User description
    "date": "2024-02-15",               # Date in YYYY-MM-DD format
    "time": "10:30",                    # Time in HH:MM (24-hour)
    "source": "vpbank_api",             # Input source type
    "day_of_week": "Thursday",          # Calculated field for analysis
    "hour": 10,                         # Extracted hour for time analysis
    "category": "necessities",          # High-level category grouping
    "tags": ["recurring", "large"]     # Additional metadata tags
}
```

### Tool Result Structure:
```python
TOOL_RESULT = {
    "data": List[TRANSACTION],          # List of transaction dictionaries
    "description": str                  # LLM-provided description of what the data represents
}

MULTI_TOOL_RESULT = List[TOOL_RESULT]   # Multiple tool results for complex queries

# New structure for Vietnamese and complex queries
COMPLEX_TOOL_RESULT = {
    "tool_name": "get_complex_transaction",
    "args": {
        "jar_name": "meals",
        "start_hour": 11,
        "end_hour": 14,
        "max_amount": 20,
        "description": "lunch transactions 11am-2pm under $20"
    },
    "data": List[TRANSACTION],
    "description": "lunch transactions 11am-2pm under $20"
}
```

### Source Types for Analysis:
- **`vpbank_api`**: Bank-imported transactions (usually reliable, complete data)
- **`manual_input`**: User-entered transactions (may have more context)
- **`text_input`**: Voice/text processed transactions (conversational context)
- **`image_input`**: Receipt-scanned transactions (detailed item breakdowns)

### Sample Dataset for Testing:
```python
SAMPLE_TRANSACTIONS = [
    {
        "amount": 85.60, "jar": "groceries", "description": "Weekly grocery shopping at Market",
        "date": "2024-02-15", "time": "10:30", "source": "vpbank_api"
    },
    {
        "amount": 12.50, "jar": "meals", "description": "Coffee and croissant",
        "date": "2024-02-15", "time": "08:15", "source": "manual_input"
    },
    {
        "amount": 45.00, "jar": "meals", "description": "Lunch with colleagues",
        "date": "2024-02-14", "time": "12:45", "source": "text_input"
    },
    {
        "amount": 120.00, "jar": "entertainment", "description": "Movie tickets and dinner",
        "date": "2024-02-13", "time": "19:30", "source": "vpbank_api"
    }
]
```

## 🛠️ Transaction Retrieval Tools (6 Specialized Tools)

### **SIMPLE TOOLS (1-2 filters):**

### 1. **`get_jar_transactions(jar_name: str = None, limit: int = 50, description: str = "")`**

**Implementation:**
```python
@tool
def get_jar_transactions(jar_name: str = None, limit: int = 50, description: str = "") -> Dict:
    """Retrieve all transactions for a specific budget jar/category or all jars.
    
    Args:
        jar_name: The jar/category name to filter by, or None for all jars
        limit: Maximum number of transactions to return
        description: Description of what you're retrieving (e.g., "groceries spending")
    
    Returns:
        Dict with "data" (list of transactions) and "description" (intent description)
    """
    
    # Handle None case for all jars
    if jar_name is None:
        matches = list(all_transactions)
    else:
        # Fuzzy matching for jar names
        jar_aliases = {
            "food": ["groceries", "meals", "dining"],
            "transport": ["transportation", "gas", "fuel", "uber"],
            "fun": ["entertainment", "hobbies", "leisure"]
        }
        
        matches = []
        for transaction in all_transactions:
            if fuzzy_match_jar(transaction["jar"], jar_name, jar_aliases):
                matches.append(transaction)
    
    # Sort by date (newest first) and limit results
    filtered_data = sorted(matches, key=lambda t: t["date"], reverse=True)[:limit]
    
    # Auto-generate description if not provided
    auto_description = f"transactions from {jar_name or 'all'} jar"
    final_description = description if description else auto_description
    
    return {
        "data": filtered_data,
        "description": final_description
    }
```

**Use Cases:**
- "Show me all grocery spending" → `get_jar_transactions(jar_name="groceries", description="grocery spending")`
- "All my transactions" → `get_jar_transactions(jar_name=None, description="all my transactions")`
- "List transportation expenses" → `get_jar_transactions(jar_name="transportation", description="transportation expenses")`

### 2. **`get_time_period_transactions(jar_name: str = None, start_date: str = "last_month", end_date: str = None, limit: int = 50, description: str = "")`**

**Implementation:**
```python
@tool
def get_time_period_transactions(jar_name: str = None, start_date: str = "last_month", end_date: str = None, limit: int = 50, description: str = "") -> Dict:
    """Retrieve transactions within a time period, optionally filtered by jar.
    
    Args:
        jar_name: The jar/category name to filter by, or None for all jars
        start_date: Start date (YYYY-MM-DD format) or relative ("last_month", "last_week")
        end_date: End date (optional, defaults to today)
        limit: Maximum number of transactions to return
        description: Description of what you're retrieving (e.g., "last month groceries")
    
    Returns:
        Dict with "data" (list of transactions) and "description" (intent description)
    """
    
    # Smart date parsing
    parsed_start = parse_flexible_date(start_date)
    parsed_end = parse_flexible_date(end_date) if end_date else datetime.now().date()
    
    # Filter by date range
    time_filtered = [
        t for t in all_transactions
        if parsed_start <= datetime.strptime(t["date"], "%Y-%m-%d").date() <= parsed_end
    ]
    
    # Apply jar filter if specified
    if jar_name is not None:
        time_filtered = [t for t in time_filtered if t["jar"].lower() == jar_name.lower()]
    
    filtered_data = sorted(time_filtered, key=lambda t: t["date"], reverse=True)[:limit]
    
    # Auto-generate description if not provided
    auto_description = f"transactions from {start_date} to {end_date or 'today'}"
    if jar_name:
        auto_description += f" for {jar_name}"
    final_description = description if description else auto_description
    
    return {
        "data": filtered_data,
        "description": final_description
    }

def parse_flexible_date(date_str: str) -> date:
    """Parse various date formats including relative dates."""
    relative_dates = {
        "today": datetime.now().date(),
        "yesterday": datetime.now().date() - timedelta(days=1),
        "last_week": datetime.now().date() - timedelta(weeks=1),
        "last_month": datetime.now().date() - timedelta(days=30),
        "this_month": datetime.now().replace(day=1).date(),
        "last_year": datetime.now().date() - timedelta(days=365)
    }
    
    if date_str.lower() in relative_dates:
        return relative_dates[date_str.lower()]
    else:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
```

**Use Cases:**
- "Show me last month's spending" → `get_time_period_transactions(start_date="last_month", description="last month's spending")`
- "February groceries" → `get_time_period_transactions(jar_name="groceries", start_date="2024-02-01", end_date="2024-02-28", description="February groceries")`

### **COMPLEX TOOL (3+ filters):**

### 6. **`get_complex_transaction(...)`** - **NEW MULTI-DIMENSIONAL TOOL**

**Implementation:**
```python
@tool
def get_complex_transaction(
    jar_name: str = None,
    start_date: str = None,
    end_date: str = None,
    min_amount: float = None,
    max_amount: float = None,
    start_hour: int = None,
    end_hour: int = None,
    source_type: str = None,
    limit: int = 50,
    description: str = ""
) -> Dict[str, Any]:
    """
    MULTI-DIMENSIONAL FILTERING for complex queries requiring 3+ filter types.
    
    Use ONLY for complex queries with multiple filters simultaneously.
    Perfect for Vietnamese queries like "ăn trưa (11h-2h) dưới 20 đô".
    
    Args:
        jar_name: Budget jar name or None
        start_date: Start date filter (supports relative dates)
        end_date: End date filter  
        min_amount: Minimum amount filter
        max_amount: Maximum amount filter
        start_hour: Starting hour filter (24-hour format)
        end_hour: Ending hour filter (24-hour format)
        source_type: Transaction source filter
        limit: Maximum number of transactions
        description: LLM-provided description
        
    Returns:
        Dict with "data" (filtered transactions) and "description"
        
    Vietnamese Examples:
        "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"
        → jar_name="meals", start_hour=11, end_hour=14, max_amount=20
        
        "ăn sáng từ 6 giờ đến 10 giờ sáng dưới 15 đô"  
        → jar_name="meals", start_hour=6, end_hour=10, max_amount=15
    """
    
    filtered = []
    
    # Apply all filters step by step (comprehensive filtering)
    for transaction in MOCK_TRANSACTIONS:
        # 1. Check jar filter
        if jar_name is not None and transaction["jar"].lower() != jar_name.lower():
            continue
            
        # 2. Check date range filter
        if start_date is not None:
            parsed_start = parse_flexible_date(start_date)
            parsed_end = parse_flexible_date(end_date) if end_date else datetime.now().date()
            
            transaction_date = datetime.strptime(transaction["date"], "%Y-%m-%d").date()
            if not (parsed_start <= transaction_date <= parsed_end):
                continue
        
        # 3. Check amount range filter
        amount = transaction["amount"]
        if min_amount is not None and amount < min_amount:
            continue
        if max_amount is not None and amount > max_amount:
            continue
            
        # 4. Check hour range filter
        if start_hour is not None and end_hour is not None:
            if "time" not in transaction or not time_in_range(transaction["time"], start_hour, end_hour):
                continue
        elif start_hour is not None:
            # Only start hour specified
            try:
                hour = int(transaction["time"].split(":")[0])
                if hour < start_hour:
                    continue
            except (ValueError, IndexError, KeyError):
                continue
        elif end_hour is not None:
            # Only end hour specified
            try:
                hour = int(transaction["time"].split(":")[0])
                if hour > end_hour:
                    continue
            except (ValueError, IndexError, KeyError):
                continue
        
        # 5. Check source filter
        if source_type is not None and transaction.get("source") != source_type:
            continue
            
        # If we get here, transaction passed all filters
        filtered.append(transaction.copy())
    
    # Sort by date (newest first) and limit
    filtered.sort(key=lambda t: t["date"], reverse=True)
    limited_filtered = filtered[:limit]
    
    # Use provided description or generate comprehensive one if empty
    if description.strip():
        final_description = description.strip()
    else:
        # Auto-generate comprehensive description based on active filters
        filter_parts = []
        
        if jar_name:
            filter_parts.append(f"{jar_name} transactions")
        else:
            filter_parts.append("all transactions")
            
        if start_date or end_date:
            if start_date and end_date:
                filter_parts.append(f"from {start_date} to {end_date}")
            elif start_date:
                filter_parts.append(f"from {start_date}")
            elif end_date:
                filter_parts.append(f"until {end_date}")
        
        if min_amount is not None and max_amount is not None:
            filter_parts.append(f"between ${min_amount}-${max_amount}")
        elif min_amount is not None:
            filter_parts.append(f"over ${min_amount}")
        elif max_amount is not None:
            filter_parts.append(f"under ${max_amount}")
            
        if start_hour is not None and end_hour is not None:
            filter_parts.append(f"between {start_hour}:00-{end_hour}:00")
        elif start_hour is not None:
            filter_parts.append(f"after {start_hour}:00")
        elif end_hour is not None:
            filter_parts.append(f"before {end_hour}:00")
            
        if source_type:
            source_names = {
                "vpbank_api": "bank data",
                "manual_input": "manual entries", 
                "text_input": "voice input",
                "image_input": "scanned receipts"
            }
            filter_parts.append(f"from {source_names.get(source_type, source_type)}")
        
        final_description = "Complex filtering: " + " ".join(filter_parts)
        
        if limit < len(filtered):
            final_description += f" (showing {limit} of {len(filtered)} matches)"
    
    return {
        "data": limited_filtered,
        "description": final_description
    }
```

## 🇻🇳 Vietnamese Language Support System

### **Translation Engine:**
```python
VIETNAMESE_TRANSLATION_MAPPINGS = {
    # Meal categories with default time ranges
    "ăn trưa": {
        "jar_name": "meals",
        "start_hour": 11,
        "end_hour": 14,
        "description_prefix": "lunch"
    },
    "ăn sáng": {
        "jar_name": "meals", 
        "start_hour": 6,
        "end_hour": 10,
        "description_prefix": "breakfast"
    },
    "ăn tối": {
        "jar_name": "meals",
        "start_hour": 18, 
        "end_hour": 22,
        "description_prefix": "dinner"
    },
    
    # Time expressions
    "11h sáng ->2h chiều": {"start_hour": 11, "end_hour": 14},
    "từ 6 giờ đến 10 giờ sáng": {"start_hour": 6, "end_hour": 10},
    "buổi sáng": {"start_hour": 6, "end_hour": 12},
    "buổi chiều": {"start_hour": 12, "end_hour": 18},
    "buổi tối": {"start_hour": 18, "end_hour": 23},
    "sau 6h chiều": {"start_hour": 18},
    
    # Amount expressions  
    "dưới 20 đô": {"max_amount": 20},
    "dưới 15 đô": {"max_amount": 15},
    "trên 30 đô": {"min_amount": 30},
    "từ 10 đến 50 đô": {"min_amount": 10, "max_amount": 50},
    
    # Categories
    "giải trí": {"jar_name": "entertainment"},
    "grocery": {"jar_name": "groceries"},
    "mua sắm": {"jar_name": "groceries"},
    "chi tiêu": {"description_prefix": "spending"},
    
    # Sources
    "bank data": {"source_type": "vpbank_api"},
    "từ bank": {"source_type": "vpbank_api"},
    "manual entry": {"source_type": "manual_input"}
}
```

### **Vietnamese Query Processing Flow:**
```python
def process_vietnamese_query(query: str) -> Dict:
    """
    Process Vietnamese query and extract parameters for complex tool.
    
    Example:
    Input: "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"
    Output: {
        "jar_name": "meals",
        "start_hour": 11,
        "end_hour": 14, 
        "max_amount": 20,
        "description": "lunch transactions 11am-2pm under $20",
        "use_complex_tool": True
    }
    """
    
    parameters = {}
    description_parts = []
    
    # Extract meal type
    if "ăn trưa" in query.lower():
        parameters.update(VIETNAMESE_TRANSLATION_MAPPINGS["ăn trưa"])
        description_parts.append("lunch transactions")
    elif "ăn sáng" in query.lower():
        parameters.update(VIETNAMESE_TRANSLATION_MAPPINGS["ăn sáng"])
        description_parts.append("breakfast transactions")
    elif "ăn tối" in query.lower():
        parameters.update(VIETNAMESE_TRANSLATION_MAPPINGS["ăn tối"])
        description_parts.append("dinner transactions")
    
    # Extract time range
    time_patterns = [
        (r"(\d+)h sáng ->(\d+)h chiều", lambda m: {"start_hour": int(m.group(1)), "end_hour": int(m.group(2)) + 12}),
        (r"từ (\d+) giờ đến (\d+) giờ", lambda m: {"start_hour": int(m.group(1)), "end_hour": int(m.group(2))}),
        (r"sau (\d+)h", lambda m: {"start_hour": int(m.group(1))})
    ]
    
    for pattern, extractor in time_patterns:
        match = re.search(pattern, query.lower())
        if match:
            time_params = extractor(match)
            parameters.update(time_params)
            description_parts.append(f"{time_params['start_hour']}:00-{time_params.get('end_hour', '∞')}:00")
            break
    
    # Extract amount range
    amount_patterns = [
        (r"dưới (\d+) đô", lambda m: {"max_amount": int(m.group(1))}),
        (r"trên (\d+) đô", lambda m: {"min_amount": int(m.group(1))}),
        (r"từ (\d+) đến (\d+) đô", lambda m: {"min_amount": int(m.group(1)), "max_amount": int(m.group(2))})
    ]
    
    for pattern, extractor in amount_patterns:
        match = re.search(pattern, query.lower())
        if match:
            amount_params = extractor(match)
            parameters.update(amount_params)
            if "max_amount" in amount_params:
                description_parts.append(f"under ${amount_params['max_amount']}")
            elif "min_amount" in amount_params:
                description_parts.append(f"over ${amount_params['min_amount']}")
            break
    
    # Generate final description
    parameters["description"] = " ".join(description_parts)
    parameters["use_complex_tool"] = len([k for k in parameters.keys() if k in ["jar_name", "start_hour", "end_hour", "min_amount", "max_amount"]]) >= 3
    
    return parameters
```

### **Prompt Integration for Vietnamese Support:**
```python
def build_vietnamese_aware_prompt(user_query: str, available_jars: list) -> str:
    """Build prompt with Vietnamese query detection and translation guidance."""
    
    vietnamese_guidance = """
**VIETNAMESE QUERY HANDLING:**
Detect Vietnamese financial queries and translate parameters:

Vietnamese Patterns → Tool Parameters:
• "ăn trưa" → jar_name="meals", start_hour=11, end_hour=14
• "ăn sáng" → jar_name="meals", start_hour=6, end_hour=10  
• "ăn tối" → jar_name="meals", start_hour=18, end_hour=22
• "11h sáng ->2h chiều" → start_hour=11, end_hour=14
• "dưới 20 đô" → max_amount=20
• "trên 30 đô" → min_amount=30
• "giải trí" → jar_name="entertainment"
• "grocery/mua sắm" → jar_name="groceries"
• "bank data" → source_type="vpbank_api"

**COMPLEXITY DETECTION:**
• 1-2 filters → Use specific tools (get_jar_transactions, etc.)
• 3+ filters OR Vietnamese complex query → Use get_complex_transaction

**VIETNAMESE EXAMPLE:**
Query: "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"
Analysis: 3 filters (jar=meals + hour=11-14 + amount<20) → COMPLEX
Tool: get_complex_transaction(jar_name="meals", start_hour=11, end_hour=14, max_amount=20, description="lunch transactions 11am-2pm under $20")
"""
    
    return f"""You are a transaction history fetcher with Vietnamese language support...
    
{vietnamese_guidance}

USER INPUT: "{user_query}"
...
"""
```

## 🏷️ Description Parameter System

### **Critical Feature: LLM-Provided Descriptions**
Every tool now includes a `description` parameter where the LLM specifies what it's trying to retrieve. This enables:

#### **Vietnamese Query Example:**
```python
# Vietnamese: "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"
# LLM detects: 3 filters (jar + hour + amount) → Use complex tool
get_complex_transaction(
    jar_name="meals",
    start_hour=11,
    end_hour=14,
    max_amount=20,
    description="lunch transactions 11am-2pm under $20"  # English description for Vietnamese query
)
# Result: {"data": [...], "description": "lunch transactions 11am-2pm under $20"}
```

#### **Benefits:**
- **Clear Intent** - Each tool call has explicit purpose
- **Vietnamese Support** - English descriptions for Vietnamese queries enable international compatibility
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

## 🧪 Testing Framework Integration

### **Vietnamese Query Test Suite:**
```python
VIETNAMESE_TEST_QUERIES = [
    {
        "query": "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô",
        "expected_tool": "get_complex_transaction",
        "expected_params": {
            "jar_name": "meals",
            "start_hour": 11,
            "end_hour": 14,
            "max_amount": 20
        },
        "description": "Vietnamese lunch query with time and amount filters"
    },
    {
        "query": "ăn sáng từ 6 giờ đến 10 giờ sáng dưới 15 đô",
        "expected_tool": "get_complex_transaction", 
        "expected_params": {
            "jar_name": "meals",
            "start_hour": 6,
            "end_hour": 10,
            "max_amount": 15
        },
        "description": "Breakfast time filtering with amount"
    },
    {
        "query": "mua sắm grocery buổi sáng dưới 100 đô từ bank data",
        "expected_tool": "get_complex_transaction",
        "expected_params": {
            "jar_name": "groceries",
            "start_hour": 6,
            "end_hour": 12,
            "max_amount": 100,
            "source_type": "vpbank_api"
        },
        "description": "Complex 4-filter query: jar + time + amount + source"
    }
]
```

## 🎯 Success Criteria

The transaction history fetcher is working well when:
- ✅ **Accurate complexity detection** and tool selection based on filter count
- ✅ **Vietnamese query support** with proper translation and parameter extraction
- ✅ **Clear descriptions** provided for every tool call (English for Vietnamese queries)
- ✅ **Intelligent parameter extraction** from natural language and Vietnamese
- ✅ **Effective multi-dimensional filtering** for complex requests using the complex tool
- ✅ **Structured data presentation** with descriptions and transaction lists
- ✅ **Fast response times** through single-pass processing
- ✅ **Service integration** capability for other agents in the ecosystem

Remember: This agent provides the **data foundation** that powers informed financial decision-making across the entire system through fast, accurate transaction retrieval with clear descriptions and **comprehensive Vietnamese language support**! 🇻🇳💰
