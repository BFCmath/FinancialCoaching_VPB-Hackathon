# AI Assistant Guide - Transaction History Fetcher

## 🤖 Quick Start for AI Assistants

This is a **transaction history fetcher agent** that retrieves and presents transaction data using intelligent tool selection. The agent can handle both **simple and complex queries** by automatically selecting and combining multiple transaction retrieval tools through **LangChain tool binding**, including support for **Vietnamese and multilingual complex queries**.

### Core Understanding
- **Data retrieval service** - Fetches specific transaction subsets based on user queries
- **Multi-tool capability** - Can combine multiple tools for complex requests in single pass
- **6 specialized tools** - Including powerful complex multi-dimensional filtering tool
- **Vietnamese query support** - Handles complex Vietnamese financial queries with translation
- **Intelligent complexity detection** - Automatically chooses simple vs complex tools
- **Structured data return** - Each tool returns data with LLM-provided descriptions
- **Service layer** - Other agents can call this for transaction data
- **LangChain integration** - Uses tool binding for intelligent tool selection

## 🎯 Primary Use Cases

### 1. Simple Transaction Retrieval
Help users get specific transaction data:
- "Show me my groceries spending"
- "All transactions from last month"
- "What did I spend on transportation?"

### 2. Complex Multi-Filter Queries
Handle sophisticated requests requiring multiple dimensions:
- "Show me groceries and meals from last month over $20"
- "Compare my morning entertainment vs evening transportation spending"
- "Large purchases over $50 from manual entries vs bank data"

### 3. Vietnamese Complex Queries
Support Vietnamese financial queries with automatic translation:
- "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"
- "ăn sáng từ 6 giờ đến 10 giờ sáng dưới 15 đô"
- "chi tiêu giải trí tối (sau 6h chiều) trên 30 đô"

### 4. Time-Based Analysis
Retrieve transactions with temporal filtering:
- "Weekend vs weekday spending patterns"
- "Morning purchases compared to evening purchases"
- "Business hours transactions vs after-hours"

### 5. Service Integration
Provide data to other agents in the ecosystem:
- **budget_advisor** calls for spending analysis data
- **jar_manager** calls for category spending totals  
- **fee_manager** calls for transaction pattern data

## 🏗️ Agent Architecture

### **Single-Pass Processing System:**
```
User Query → Context Prompt → LLM Tool Selection → Multi-Tool Execution → Structured Data Return
```

### **Intelligent Tool Selection:**
```
Simple Query (1-2 filters) → Specific Tools (get_jar_transactions, etc.)
Complex Query (3+ filters) → Complex Tool (get_complex_transaction)
Vietnamese Query → Translation + Complex Tool
```

### **LangChain Tool Binding Pattern:**
```python
# All 6 tools bound to LLM for intelligent selection
llm_with_tools = llm.bind_tools(TRANSACTION_TOOLS)

# LLM automatically chooses which tools to call with descriptions
response = llm_with_tools.invoke(messages)
```

### Transaction Data Structure:
```python
TRANSACTION = {
    "amount": float,         # Transaction amount
    "jar": str,             # Budget category/jar name
    "description": str,     # Transaction description
    "date": str,           # Date in YYYY-MM-DD format
    "time": str,           # Time in HH:MM format
    "source": str          # "vpbank_api", "manual_input", "text_input", "image_input"
}

TOOL_RESULT = {
    "data": List[TRANSACTION],  # List of transaction dictionaries
    "description": str          # LLM-provided description of what the data represents
}
```

### LLM Flow:
```
User Input → Complexity Detection → Tool Selection → Execute with Descriptions → Return Structured Data
```

## 🛠️ Transaction Retrieval Tools (6 Tools)

### **SIMPLE TOOLS (1-2 filters):**

### 1. **`get_jar_transactions(jar_name=None, limit=50, description="")`**
**Purpose:** Get all transactions for a specific jar/category or all jars
```python
# Example calls:
"groceries spending" → get_jar_transactions(jar_name="groceries", description="groceries spending")
"all my transactions" → get_jar_transactions(jar_name=None, description="all my transactions")
```

### 2. **`get_time_period_transactions(jar_name=None, start_date="last_month", end_date=None, limit=50, description="")`**
**Purpose:** Get transactions within a time period, optionally filtered by jar
```python
# Example calls:
"last month spending" → get_time_period_transactions(start_date="last_month", description="last month's spending")
"groceries in February" → get_time_period_transactions(jar_name="groceries", start_date="2024-02-01", end_date="2024-02-28", description="February groceries")
```

### 3. **`get_amount_range_transactions(jar_name=None, min_amount=None, max_amount=None, limit=50, description="")`**
**Purpose:** Get transactions within specific amount range, optionally filtered by jar
```python
# Example calls:
"purchases over $50" → get_amount_range_transactions(min_amount=50, description="purchases over $50")
"small entertainment purchases" → get_amount_range_transactions(jar_name="entertainment", max_amount=20, description="small entertainment purchases")
```

### 4. **`get_hour_range_transactions(jar_name=None, start_hour=6, end_hour=22, limit=50, description="")`**
**Purpose:** Get transactions within specific hours of the day for behavioral analysis
```python
# Example calls:
"morning purchases" → get_hour_range_transactions(start_hour=6, end_hour=12, description="morning purchases")
"evening entertainment" → get_hour_range_transactions(jar_name="entertainment", start_hour=18, end_hour=23, description="evening entertainment")
```

### 5. **`get_source_transactions(jar_name=None, source_type="vpbank_api", limit=50, description="")`**
**Purpose:** Get transactions from specific input source, optionally filtered by jar
```python
# Example calls:
"manual entries" → get_source_transactions(source_type="manual_input", description="manual entries")
"bank imported groceries" → get_source_transactions(jar_name="groceries", source_type="vpbank_api", description="bank imported groceries")
```

### **COMPLEX TOOL (3+ filters):**

### 6. **`get_complex_transaction(jar_name=None, start_date=None, end_date=None, min_amount=None, max_amount=None, start_hour=None, end_hour=None, source_type=None, limit=50, description="")`**
**Purpose:** **MULTI-DIMENSIONAL FILTERING** for complex queries with 3+ filter types

**Use ONLY for complex queries requiring multiple filters simultaneously:**

```python
# Vietnamese: "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"
get_complex_transaction(
    jar_name="meals", 
    start_hour=11, 
    end_hour=14, 
    max_amount=20, 
    description="lunch transactions 11am-2pm under $20"
)

# English: "morning grocery shopping under $100 from bank data"
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

## 🇻🇳 Vietnamese Query Support

### **Translation Mapping:**
```python
VIETNAMESE_MAPPINGS = {
    "ăn trưa": {"jar": "meals", "hours": (11, 14)},     # lunch
    "ăn sáng": {"jar": "meals", "hours": (6, 10)},     # breakfast
    "ăn tối": {"jar": "meals", "hours": (18, 22)},     # dinner
    "11h sáng ->2h chiều": {"start_hour": 11, "end_hour": 14},
    "dưới 20 đô": {"max_amount": 20},
    "trên 30 đô": {"min_amount": 30},
    "giải trí": {"jar": "entertainment"},
    "grocery": {"jar": "groceries"},
    "bank data": {"source": "vpbank_api"}
}
```

### **Example Vietnamese Queries:**
1. **"cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"**
   - Translation: "show me lunch information (11am -> 2pm) under $20"
   - Tool: `get_complex_transaction(jar_name="meals", start_hour=11, end_hour=14, max_amount=20)`

2. **"ăn sáng từ 6 giờ đến 10 giờ sáng dưới 15 đô"**
   - Translation: "breakfast from 6am to 10am under $15"
   - Tool: `get_complex_transaction(jar_name="meals", start_hour=6, end_hour=10, max_amount=15)`

## 🧠 Intelligent Tool Selection Logic

### **Complexity Detection:**
```python
SIMPLE_QUERIES = {
    "1 filter": "get_jar_transactions, get_time_period_transactions, etc.",
    "2 filters": "get_time_period_transactions with jar, get_amount_range_transactions with jar"
}

COMPLEX_QUERIES = {
    "3+ filters": "get_complex_transaction",
    "Vietnamese": "translate + get_complex_transaction",
    "Multi-dimensional": "get_complex_transaction"
}
```

### **Tool Selection Examples:**

#### **Simple Queries (Use Specific Tools):**
```
"groceries spending" → get_jar_transactions(jar_name="groceries")
"last month transactions" → get_time_period_transactions(start_date="last_month")
"purchases over $50" → get_amount_range_transactions(min_amount=50)
```

#### **Complex Queries (Use Complex Tool):**
```
"Vietnamese lunch query" → get_complex_transaction(jar="meals", hour=11-14, amount<20)
"morning grocery under $100 from bank" → get_complex_transaction(jar+hour+amount+source)
"evening entertainment over $30" → get_complex_transaction(jar+hour+amount)
```

## 🏷️ Description Parameter System

### **Critical Feature: LLM-Provided Descriptions**
Every tool includes a `description` parameter where the LLM specifies what it's retrieving:

```python
# For Vietnamese query: "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"
get_complex_transaction(
    jar_name="meals",
    start_hour=11,
    end_hour=14,
    max_amount=20,
    description="lunch transactions 11am-2pm under $20"
)
```

### **Benefits:**
- **Clear Intent** - Each tool call has explicit purpose
- **User-Friendly** - Descriptions explain what each dataset represents
- **Vietnamese Support** - Clear English descriptions for Vietnamese queries
- **Agent-Ready** - Other agents can easily understand the data context
- **Multi-Tool Clarity** - Complex queries return multiple clearly labeled datasets

## 📊 Structured Data Return Format

### **Single Tool Result:**
```python
{
    "data": [
        {
            "amount": 12.0,
            "jar": "meals", 
            "description": "Quick lunch",
            "date": "2024-03-03",
            "time": "12:15",
            "source": "manual_input"
        },
        # ... more transactions
    ],
    "description": "lunch transactions 11am-2pm under $20"  # LLM-provided description
}
```

### **Multi-Tool Result:**
```python
[
    {
        "tool_name": "get_complex_transaction",
        "args": {"jar_name": "meals", "start_hour": 11, "end_hour": 14, "max_amount": 20},
        "data": [...],  # List of transactions
        "description": "lunch transactions 11am-2pm under $20"
    }
]
```

## 🎯 Tool Selection Examples

### **Parameter Detection Rules:**
```python
TOOL_SELECTION_LOGIC = {
    "single_jar": "get_jar_transactions",
    "jar + time": "get_time_period_transactions",
    "jar + amount": "get_amount_range_transactions", 
    "jar + hours": "get_hour_range_transactions",
    "jar + source": "get_source_transactions",
    "3+ filters": "get_complex_transaction",
    "vietnamese_complex": "get_complex_transaction"
}
```

### **Example Mappings:**
- "groceries spending" → `get_jar_transactions("groceries")`
- "groceries last month" → `get_time_period_transactions(jar_name="groceries", start_date="last_month")`
- "Vietnamese lunch query" → `get_complex_transaction(jar="meals", start_hour=11, end_hour=14, max_amount=20)`
- "morning grocery under $100 from bank" → `get_complex_transaction(jar+hour+amount+source)`

## 🚨 Critical Guidelines

### ✅ DO
- **Detect query complexity** - Count filter types before tool selection
- **Use complex tool for 3+ filters** - Don't use multiple simple tools when complex tool is better
- **Handle Vietnamese queries** - Translate and extract parameters correctly
- **Always provide descriptions** - Use the description parameter to clarify intent
- **Support comparison queries** - Handle "vs", "compare", "difference between" requests

### ❌ DON'T  
- **Use complex tool for simple queries** - Use specific tools for 1-2 filters
- **Skip Vietnamese translation** - Always extract proper parameters
- **Give financial advice** - Focus purely on data retrieval and presentation
- **Make recommendations** - Present data objectively without suggestions
- **Ignore tool combination opportunities** - Recognize when multiple tools enhance results

## 🎯 Success Criteria

The transaction history fetcher is working well when:
- ✅ **Accurate complexity detection** and tool selection
- ✅ **Vietnamese query support** with proper translation
- ✅ **Clear descriptions** provided for every tool call
- ✅ **Intelligent parameter extraction** from natural language
- ✅ **Effective multi-dimensional filtering** for complex requests
- ✅ **Structured data presentation** with descriptions and transaction lists
- ✅ **Fast response times** through single-pass processing
- ✅ **Service integration** capability for other agents

Remember: This agent provides the **data foundation** that powers informed financial decision-making across the entire system through fast, accurate transaction retrieval with clear descriptions and Vietnamese language support! 🇻🇳💰
