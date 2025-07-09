# Multi-Jar Manager - T. Harv Eker's 6-Jar Budget System

A comprehensive LLM-powered jar management system implementing T. Harv Eker's proven 6-jar money management philosophy with multi-jar operations, automatic percentage rebalancing, and natural language processing.

## 🎯 Overview

This system combines **Gemini LLM** with **LangChain tool calling** to provide an intelligent jar manager that understands natural language commands and executes sophisticated multi-jar operations. The system maintains T. Harv Eker's official 6-jar allocation percentages while allowing users to create custom jars with automatic rebalancing.

### Key Features

- **🤖 Natural Language Processing** - Understands commands in English and Vietnamese
- **🏺 Multi-Jar Operations** - Create, update, delete multiple jars simultaneously  
- **⚖️ Automatic Rebalancing** - Maintains 100% allocation across all jars
- **💰 T. Harv Eker's System** - Implements the proven 6-jar money management method
- **🔧 Enhanced Debugging** - Detailed function call tracing and parameter logging
- **🌍 Multilingual Support** - Works with Vietnamese input for localized usage

## 🏗️ Architecture

### Core Components

```
📁 jar_test/
├── 🧠 main.py           # LLM setup + tool execution + debug logging
├── 🛠️ tools.py          # 4 core tools + rebalancing algorithms
├── 📝 prompt.py         # Enhanced prompts with multi-jar examples  
├── ⚙️ config.py         # Gemini API configuration
├── 🧪 test.py          # Interactive testing interface
├── 📋 requirements.txt  # Dependencies
├── 🔧 env.example      # Environment template
└── 📁 cursor_docs/     # Detailed documentation
```

### LLM Tool Flow

```
Natural Language Input
         ↓
Gemini 2.5 Flash Lite Analysis
         ↓
Tool Selection & Parameter Extraction
         ↓
Multi-Jar Tool Execution
         ↓
Automatic Rebalancing
         ↓
Results + Updated Status
```

## 🛠️ Core Tools (4 Tools)

### 1. `create_jar()` - Multi-Jar Creation
Create one or multiple jars with automatic percentage allocation:

```python
# Single jar
"Create vacation jar with 15%"
→ create_jar(name=["vacation"], description=["Summer trip"], percent=[0.15])

# Multiple jars
"Create vacation and emergency jars with 10% each"  
→ create_jar(name=["vacation", "emergency"], percent=[0.10, 0.10])

# Amount-based
"Create car repair jar with $1000 budget"
→ create_jar(name=["car_repair"], amount=[1000])  # Auto-converts to 20%
```

### 2. `update_jar()` - Multi-Jar Updates
Update jar properties and percentages with rebalancing:

```python
# Single update
"Update vacation jar to 12%"
→ update_jar(jar_name=["vacation"], new_percent=[0.12])

# Multiple updates  
"Update vacation to 8% and emergency to 15%"
→ update_jar(jar_name=["vacation", "emergency"], new_percent=[0.08, 0.15])
```

### 3. `delete_jar()` - Multi-Jar Deletion
Delete jars with automatic percentage redistribution:

```python
# Single deletion
"Delete vacation jar because trip cancelled"
→ delete_jar(jar_name=["vacation"], reason="Trip cancelled")

# Multiple deletions
"Delete vacation and car repair jars"
→ delete_jar(jar_name=["vacation", "car_repair"], reason="Plans changed")
```

### 4. `list_jars()` - Status Display
Show all jars with current balances and budget allocations:

```python
"Show my jars" / "List all jars"
→ list_jars()
```

**Note:** The `add_money_to_jar` tool has been removed for simplicity. Users should use `update_jar` to modify percentage allocations instead.

## 🏺 T. Harv Eker's 6-Jar System

### Default Allocation (Total: 100%)

| Jar | Percentage | Purpose |
|-----|------------|---------|
| **Necessities** | 55% | Essential living expenses (rent, utilities, food) |
| **Long-term Savings** | 10% | Major purchases and future goals |
| **Play** | 10% | Entertainment and fun activities |
| **Education** | 10% | Learning and skill development |
| **Financial Freedom** | 10% | Investments and passive income |
| **Give** | 5% | Charity and helping others |

### Sample Data (Based on $5,000 income)

```
📋 Budget Jars (6 jars) - Total Income: $5,000.00
• necessities: $1650.00/$2750.00 (33.0%/55.0%) - Essential living expenses
• long_term_savings: $200.00/$500.00 (4.0%/10.0%) - Major purchases  
• play: $300.00/$500.00 (6.0%/10.0%) - Entertainment and fun
• education: $150.00/$500.00 (3.0%/10.0%) - Learning and development
• financial_freedom: $75.00/$500.00 (1.5%/10.0%) - Investments
• give: $25.00/$250.00 (0.5%/5.0%) - Charity and helping others
💰 Totals: $2400.00/$5000.00 (48.0%/100.0%)
```

## ⚖️ Automatic Rebalancing System

### How It Works

1. **New Jar Creation** - Existing jars scale down proportionally to make room
2. **Jar Deletion** - Freed percentage redistributes to remaining jars  
3. **Percentage Updates** - Other jars adjust to maintain 100% total

### Example Rebalancing

```
Initial: necessities(55%), play(10%), education(10%), give(5%) = 80%
Add: vacation(20%)
Result: necessities(44%), play(8%), education(8%), give(4%), vacation(20%) = 100%
```

The system automatically calculates the scale factor and adjusts all jars proportionally while ensuring a minimum 1% allocation for each jar.

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone and enter directory
cd jar_test

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 2. Interactive Testing

```bash
# Start interactive mode
python test.py

# Or run specific test suites
python test.py --batch           # Comprehensive tests
python test.py --rebalancing     # Rebalancing tests  
python test.py --confidence      # Confidence scoring tests
```

### 3. Example Commands

```python
# T. Harv Eker system
"Set up the 6-jar system"
"Show my jars"

# Single operations
"Create vacation jar with 15%"
"Update vacation jar to 12%" 
"Delete vacation jar because trip cancelled"

# Multi-jar operations
"Create vacation and emergency jars with 10% each"
"Update vacation to 8% and emergency to 15%"
"Delete vacation and car repair jars"

# Vietnamese language
"Tạo hũ du lịch với 15%"
"Tạo hũ du lịch và hũ khẩn cấp với 10% mỗi cái"
```

## 🔧 Enhanced Debug Features

### Function Call Tracing

The system provides detailed logging of AI function calls:

```
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

### Error Handling

- **Validation errors** with specific parameter details
- **Rebalancing notifications** with before/after percentages  
- **Confidence scoring** with uncertainty warnings
- **UTF-8 support** for Vietnamese language inputs

## 📊 System Commands

### Interactive Mode Commands

| Command | Description |
|---------|-------------|
| `help` | Show command examples and usage |
| `summary` | Display current jar status |
| `reset` | Reset to T. Harv Eker's default 6-jar system |
| `debug` | Toggle debug mode on/off |
| `quit` | Exit the program |

### Test Modes

| Flag | Description |
|------|-------------|
| `--batch` | Run comprehensive batch tests |
| `--rebalancing` | Test automatic rebalancing functionality |
| `--confidence` | Test confidence scoring and edge cases |
| `--help` | Show detailed usage information |

## 🔄 Data Structure

### Jar Format (Decimal Percentages)

```python
jar_data = {
    "name": str,                # Unique identifier (e.g., "vacation")
    "description": str,         # Human-readable description  
    "percent": float,          # Budget allocation (0.0-1.0, e.g., 0.15 = 15%)
    "current_percent": float   # Current balance (0.0-1.0, can exceed percent)
}
```

### Key Conversions

```python
# Percentage to dollar amount (based on $5000 income)
calculate_budget_from_percent(0.15)      # Returns $750.00
calculate_current_amount_from_percent(0.08)  # Returns $400.00

# Dollar amount to percentage  
calculate_percent_from_amount(500.0)     # Returns 0.10 (10%)

# Display formatting
format_percent_display(0.15)            # Returns "15.0%"
```

## 🌍 Vietnamese Language Support

The system supports Vietnamese language inputs for localized usage:

```python
vietnamese_examples = [
    "Tạo hũ du lịch với 15%",                          # Create vacation jar with 15%
    "Tạo hũ du lịch và hũ khẩn cấp với 10% mỗi cái",  # Create vacation and emergency jars
    "Cập nhật hũ du lịch thành 12%",                   # Update vacation jar to 12%
    "Xóa hũ du lịch vì hủy chuyến đi",                 # Delete vacation jar (trip cancelled)
]
```

## 📋 Requirements

### Dependencies

```
langchain-google-genai>=2.0.0
google-generativeai>=0.8.0
python-dotenv>=1.0.0
```

### Environment Variables

```bash
GOOGLE_API_KEY=your_gemini_api_key_here
MODEL_NAME=gemini-2.5-flash-lite-preview-06-17  # Optional
TEMPERATURE=0.1                                  # Optional  
DEBUG_MODE=false                                 # Optional
```

## 🎯 Use Cases

### 1. Personal Budget Management
- Implement T. Harv Eker's proven 6-jar system
- Create custom jars for specific goals (vacation, car, emergency)
- Track spending against budget allocations
- Automatic rebalancing when priorities change

### 2. Testing Multi-Jar Operations  
- Validate multi-jar CRUD operations
- Test automatic percentage rebalancing
- Verify confidence scoring accuracy
- Debug natural language processing

### 3. Educational & Training
- Learn T. Harv Eker's money management principles
- Practice percentage-based budgeting
- Understand automatic rebalancing concepts
- Explore LLM tool calling architecture

## 🔐 Security & Privacy

- **No financial data storage** - Sample data only ($5,000 mock income)
- **Local processing** - All jar data stored in memory during session
- **API key protection** - Store Gemini API key in environment variables
- **No persistent storage** - Data resets between sessions (testing focus)

## 📚 Documentation

Detailed documentation available in `cursor_docs/`:

- **`for_ai.md`** - AI assistant guide with tool specifications
- **`detail_context.md`** - System architecture and implementation details  
- **`agent_detail.md`** - LLM agent specifications and examples

## 🤝 Contributing

This system serves as a testing lab for multi-jar budget management. To extend functionality:

1. **Add new tools** in `tools.py` with `@tool` decorator
2. **Update prompts** in `prompt.py` with new examples
3. **Add test scenarios** in `test.py` for validation
4. **Update documentation** in `cursor_docs/` folder

## 📄 License

This project implements T. Harv Eker's proven 6-jar money management system for educational and testing purposes. Please refer to official T. Harv Eker resources for the complete methodology.

---

**Built with ❤️ using Gemini LLM, LangChain, and T. Harv Eker's proven money management principles.**
