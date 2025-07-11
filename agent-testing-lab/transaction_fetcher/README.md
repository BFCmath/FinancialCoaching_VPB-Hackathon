# 🔍 Transaction History Fetcher

A sophisticated **transaction history fetcher agent** that provides fast, accurate transaction data retrieval using intelligent tool selection with **Vietnamese language support** and **6 specialized retrieval tools** including a powerful multi-dimensional filtering tool for complex queries.

## 🎯 Purpose

The Transaction History Fetcher is a **data-focused transaction retrieval agent** that:
- **Retrieves transaction data** using 6 specialized filtering tools (5 simple + 1 complex)
- **Handles Vietnamese financial queries** with automatic translation and parameter extraction
- **Uses intelligent complexity detection** to choose appropriate tools automatically  
- **Provides structured data** with LLM-provided descriptions for clear intent
- **Serves as data foundation** for other agents in the financial ecosystem

## 🏗️ Architecture

### Single-Pass Processing System
```
User Request → Complexity Detection → Tool Selection → Data Retrieval → Structured Response
     ↓              ↓                   ↓              ↓              ↓
Vietnamese:     Simple (1-2 filters)   5 Specific    Raw Transaction  Data + Description
"ăn trưa        vs Complex (3+ filters) Tools vs      Data from       {"data": [...],
11h-2h<20đô"   Auto-detect Vietnamese   Complex Tool  Mock Database   "description": "..."}
```

### Vietnamese Query Support
```
"cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"
                            ↓
Translation: jar=meals + start_hour=11 + end_hour=14 + max_amount=20
                            ↓
Complexity Detection: 3+ filters → Use get_complex_transaction
                            ↓
Result: {"data": [...], "description": "lunch transactions 11am-2pm under $20"}
```

### Core Components
- **`main.py`**: LangChain tool binding with intelligent tool selection
- **`tools.py`**: 6 transaction retrieval tools with description parameters
- **`prompt.py`**: Vietnamese-aware prompts for complexity detection and tool selection
- **`config.py`**: Configuration management (API keys, settings)
- **`test.py`**: Interactive testing with Vietnamese query support

## 🛠️ Transaction Retrieval Tools (6 Core Tools)

### **SIMPLE TOOLS (1-2 filters):**

### 1. `get_jar_transactions(jar_name, limit=50, description="")`
**Purpose:** Get all transactions for a specific budget category
```python
# Examples:
"Show me all grocery spending" → get_jar_transactions("groceries", description="grocery spending")
"Entertainment expenses" → get_jar_transactions("entertainment", description="entertainment expenses")
```

### 2. `get_time_period_transactions(jar_name=None, start_date="last_month", end_date=None, limit=50, description="")`
**Purpose:** Get transactions within a time period
```python
# Examples:
"Last month's transactions" → get_time_period_transactions(start_date="last_month", description="last month's transactions")
"February spending" → get_time_period_transactions(start_date="2024-02-01", end_date="2024-02-28", description="February spending")
```

### 3. `get_amount_range_transactions(jar_name=None, min_amount=None, max_amount=None, limit=50, description="")`
**Purpose:** Get transactions within specific amount ranges
```python
# Examples:
"Purchases over $50" → get_amount_range_transactions(min_amount=50, description="purchases over $50")
"Small transactions under $10" → get_amount_range_transactions(max_amount=10, description="small transactions under $10")
```

### 4. `get_hour_range_transactions(jar_name=None, start_hour=6, end_hour=22, limit=50, description="")`
**Purpose:** Get transactions during specific hours (behavioral analysis)
```python
# Examples:
"Morning purchases" → get_hour_range_transactions(start_hour=6, end_hour=12, description="morning purchases")
"Evening spending" → get_hour_range_transactions(start_hour=18, end_hour=23, description="evening spending")
```

### 5. `get_source_transactions(jar_name=None, source_type="vpbank_api", limit=50, description="")`
**Purpose:** Get transactions by input source/method
```python
# Examples:
"Manual entries" → get_source_transactions(source_type="manual_input", description="manual entries")
"Bank imported data" → get_source_transactions(source_type="vpbank_api", description="bank imported data")
```

### **COMPLEX TOOL (3+ filters):**

### 6. `get_complex_transaction(jar_name=None, start_date=None, end_date=None, min_amount=None, max_amount=None, start_hour=None, end_hour=None, source_type=None, limit=50, description="")` - **NEW!**
**Purpose:** **MULTI-DIMENSIONAL FILTERING** for complex queries requiring 3+ filter types

**Use ONLY for complex queries with multiple filters simultaneously:**

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

## 🇻🇳 Vietnamese Language Support

### **Supported Vietnamese Patterns:**
```python
VIETNAMESE_MAPPINGS = {
    "ăn trưa": {"jar": "meals", "start_hour": 11, "end_hour": 14},     # lunch
    "ăn sáng": {"jar": "meals", "start_hour": 6, "end_hour": 10},     # breakfast
    "ăn tối": {"jar": "meals", "start_hour": 18, "end_hour": 22},     # dinner
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

3. **"chi tiêu giải trí tối (sau 6h chiều) trên 30 đô"**
   - Translation: "evening entertainment spending (after 6pm) over $30"
   - Tool: `get_complex_transaction(jar_name="entertainment", start_hour=18, min_amount=30)`

## 🧠 Intelligent Tool Selection & Complexity Detection

### **Tool Selection Logic:**
```python
TOOL_SELECTION_RULES = {
    "1 filter": "Use specific tool (get_jar_transactions, get_time_period_transactions, etc.)",
    "2 filters": "Use specific tool with jar parameter (get_time_period_transactions with jar, etc.)",
    "3+ filters": "Use get_complex_transaction",
    "Vietnamese complex": "Translate + use get_complex_transaction",
    "Multi-dimensional": "Use get_complex_transaction"
}
```

### **Examples:**
- "groceries spending" → `get_jar_transactions("groceries")` (1 filter)
- "groceries last month" → `get_time_period_transactions(jar_name="groceries", start_date="last_month")` (2 filters)
- "Vietnamese lunch query" → `get_complex_transaction(jar="meals", hour=11-14, amount<20)` (3+ filters)
- "morning grocery under $100 from bank" → `get_complex_transaction(jar+hour+amount+source)` (4 filters)

## 📊 Response Examples

### Data Response Format:
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

### Vietnamese Query Response:
```
Vietnamese Input: "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"

Response: 
{
  "tool_name": "get_complex_transaction",
  "args": {
    "jar_name": "meals",
    "start_hour": 11,
    "end_hour": 14,
    "max_amount": 20,
    "description": "lunch transactions 11am-2pm under $20"
  },
  "data": [
    {"amount": 12.0, "jar": "meals", "description": "Quick lunch", "date": "2024-03-03", "time": "12:15"},
    {"amount": 18.50, "jar": "meals", "description": "Lunch meeting", "date": "2024-03-02", "time": "13:30"}
  ],
  "description": "lunch transactions 11am-2pm under $20"
}
```

## 🚀 Quick Start

### 1. Installation
```bash
# Clone and navigate to directory
cd transaction_fetcher

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env with your GOOGLE_API_KEY
```

### 2. Configuration
```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional settings
DEBUG_MODE=true           # Enable detailed logging
MOCK_DATA_MODE=true       # Use sample data for testing
MAX_TRANSACTIONS=200      # Maximum transactions per query
```

### 3. Testing Options

#### Interactive Testing
```bash
python test.py
```
**Features:**
- 💬 Interactive chat mode
- 🧪 Predefined test scenarios including Vietnamese queries
- 📊 Quick data retrieval tests
- 🔧 Individual tool testing
- 🇻🇳 Vietnamese query testing
- ⚙️ Configuration validation

#### Vietnamese Query Testing
```bash
python test.py
# Select option 6: "Vietnamese Complex Query Testing"
```

#### Direct Usage
```python
from main import TransactionHistoryFetcher

fetcher = TransactionHistoryFetcher()

# English query
result = fetcher.fetch_transaction_history("show me groceries last month")

# Vietnamese query
result = fetcher.fetch_transaction_history("cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô")
```

## 📁 Project Structure

```
transaction_fetcher/
├── 🧠 main.py              # LangChain tool binding + execution pipeline
├── 🛠️ tools.py             # 6 transaction retrieval tools (5 simple + 1 complex)
├── 📝 prompt.py            # Vietnamese-aware prompts for intelligent tool selection
├── ⚙️ config.py            # Configuration management
├── 🧪 test.py              # Interactive testing with Vietnamese support
├── 📋 requirements.txt     # Dependencies
├── 📋 env.example          # Environment template
├── 📖 README.md            # This file
└── 📁 cursor_docs/         # AI assistant documentation
    ├── for_ai.md           # Quick start guide for AI
    ├── agent_detail.md     # Detailed specifications
    └── detail_context.md   # Comprehensive context
```

## 🔧 Configuration Options

### LLM Settings
- **`GOOGLE_API_KEY`**: Required for Gemini LLM access
- **`MODEL_NAME`**: Gemini model version (default: gemini-2.5-flash-lite-preview-06-17)
- **`LLM_TEMPERATURE`**: Response creativity (0.0-1.0, default: 0.1)

### Processing Limits
- **`MAX_TRANSACTIONS`**: Maximum transactions per query (default: 200)
- **`DEFAULT_TRANSACTION_LIMIT`**: Default limit for tools (default: 50)

### Feature Toggles
- **`ENABLE_VIETNAMESE_SUPPORT`**: Enable Vietnamese query processing (default: true)
- **`ENABLE_COMPLEX_TOOL`**: Enable multi-dimensional filtering tool (default: true)

### Development Settings
- **`DEBUG_MODE`**: Enable detailed logging (default: false)
- **`MOCK_DATA_MODE`**: Use sample data for testing (default: true)

## 🎯 Use Cases

### Direct User Interaction
- **Simple Data Queries**: "How much did I spend on groceries last month?"
- **Vietnamese Complex Queries**: "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"
- **Multi-dimensional Analysis**: "Show me morning grocery purchases under $100 from bank data"

### Service Integration
- **Budget Advisor**: Calls for spending analysis before creating budgets
- **Jar Manager**: Gets category spending patterns for jar optimization
- **Fee Manager**: Analyzes recurring transaction patterns

### Behavioral Analysis
- **Time-based patterns**: Morning vs evening spending habits
- **Amount patterns**: Large vs small purchase behaviors  
- **Source analysis**: Manual vs automated transaction patterns
- **Category insights**: Spending consistency across different jars

## 🇻🇳 Vietnamese Query Examples

### Meal-based Queries:
- "ăn trưa hôm nay" → lunch today
- "ăn sáng tuần này dưới 10 đô" → breakfast this week under $10
- "ăn tối cuối tuần trên 25 đô" → weekend dinner over $25

### Time-based Queries:
- "mua sắm buổi sáng" → morning shopping
- "chi tiêu buổi tối" → evening spending
- "giao dịch sau 6h chiều" → transactions after 6pm

### Complex Multi-filter Queries:
- "grocery buổi sáng dưới 50 đô từ bank" → morning grocery under $50 from bank
- "giải trí tối cuối tuần trên 30 đô" → weekend evening entertainment over $30
- "ăn trưa trong tuần từ 20 đến 40 đô" → weekday lunch $20-40

## 🚨 Important Guidelines

### ✅ What the Agent Does
- **Provides fast transaction data retrieval** using intelligent tool selection
- **Handles Vietnamese financial queries** with automatic translation
- **Uses complexity detection** to choose appropriate tools automatically
- **Returns structured data** with clear descriptions for all queries
- **Supports multi-dimensional filtering** for complex analysis requests

### ❌ What the Agent Doesn't Do
- **Give financial advice** - That's budget_advisor's responsibility
- **Make jar allocation decisions** - That's jar_manager's job
- **Provide investment recommendations** - Stays focused on data retrieval
- **Store conversation state** - Each request is independent
- **Create budget plans** - Provides data for other agents to use

## 🎉 Success Criteria

The transaction history fetcher is working well when:
- ✅ **Accurate complexity detection** and appropriate tool selection
- ✅ **Vietnamese query support** with proper translation and parameter extraction
- ✅ **Clear descriptions** provided for every tool call
- ✅ **Intelligent parameter extraction** from natural language
- ✅ **Effective multi-dimensional filtering** for complex requests
- ✅ **Structured data presentation** with descriptions and transaction lists
- ✅ **Fast response times** through single-pass processing
- ✅ **Service integration** capability for other agents

## 📈 Future Enhancements

- **Expanded Vietnamese vocabulary** for more financial terms
- **Additional language support** (Thai, Chinese, etc.)
- **Advanced pattern recognition** for complex queries
- **Real-time data integration** with live banking APIs
- **Enhanced behavioral analysis** with time-based insights

---

This agent provides the **data foundation** that powers informed financial decision-making across the entire personal finance ecosystem with comprehensive Vietnamese language support! 🇻🇳🔍💰📊
