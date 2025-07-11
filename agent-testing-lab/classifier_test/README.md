# Transaction Classifier Test Lab 🧪

**LLM-powered transaction classifier with confidence-based classification using Gemini API**

Automatically classify expenses into budget jars with intelligent confidence scoring - no confirmation prompts needed for high-confidence transactions!

## 🎯 What This Does

Test how well Gemini LLM can:
- **Classify multiple transactions** in a single input with multiple tool calls
- **Provide confidence scores** (0-100%) for classification certainty with visual indicators
- **Handle Vietnamese language** inputs and cultural context
- **Extract amounts** from various formats (dollars, k, Vietnamese currency)
- **Use transaction history** for pattern recognition and improved accuracy
- **Make smart decisions** about when to ask for confirmation vs. auto-classify

## 🛠️ LLM Tools Available

The LLM intelligently chooses from these tools based on transaction analysis:

### **1. `add_money_to_jar_with_confidence(amount, jar_name, confidence)`**
**Purpose:** Add money to jar with confidence score and visual feedback

**Confidence Levels:**
- **90-100%**: ✅ Very certain - auto-classify (exact keyword match, clear transaction)
- **70-89%**: ⚠️ Moderately certain - auto-classify with warning (good match but some ambiguity)  
- **50-69%**: ❓ Uncertain - should use ask_for_confirmation instead

### **2. `ask_for_confirmation(amount, jar_name, reason)`**
**Purpose:** Ask for user confirmation when classification is uncertain

### **3. `report_no_suitable_jar(description, suggestion)`**
**Purpose:** Report when no existing jar matches the transaction

### **4. `request_more_info(question)`**
**Purpose:** Ask for clarification when input lacks essential information

## 📊 Available Budget Jars

**Essential & High-Priority:**
- **`rent`**: $1,250/$1,250 - Monthly rent or mortgage payment
- **`groceries`**: $270/$400 - Food and household essentials from supermarkets
- **`utilities`**: $65/$200 - Essential services (electricity, water, internet)
- **`gas`**: $103/$200 - Fuel and vehicle-related expenses

**Daily & Variable:**
- **`meals`**: $212/$500 - Dining out, food delivery, coffee shop purchases
- **`transport`**: $18/$100 - Public transportation, taxis, rideshare services

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Copy environment template
cp env.example .env

# Add your Gemini API key to .env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Tests
```bash
# Interactive testing interface
python test.py

# Quick command line test
python main.py

# Simple testing mode  
python -c "from main import classify_simple; print(classify_simple('meal 20 dollar'))"
```

## 🧪 Example Scenarios

### **Single Transaction (High Confidence - Auto-classify)**
```
Input: "gas 50 dollar"
Output: 🔧 add_money_to_jar_with_confidence() → ✅ Added $50.0 to gas jar (95% confident)
```

### **Single Transaction (Medium Confidence - Auto-classify with Warning)**
```
Input: "coffee 5 dollar"
Output: 🔧 add_money_to_jar_with_confidence() → ⚠️ Added $5.0 to meals jar (75% confident - moderate certainty)
```

### **Uncertain Transaction (Ask for Confirmation)**
```
Input: "shopping 30 dollar"
Output: 🔧 ask_for_confirmation() → ❓ Add $30.0 to groceries jar? Could be groceries or entertainment items. Confirm (y/n):
```

### **Multiple Transactions (Mixed Confidence)**
```
Input: "chicken rice 10, coffee 5, utilities bill 65"
Output:
🔄 Multiple Transactions Processed:
1. 🔧 add_money_to_jar_with_confidence() → ✅ Added $10.0 to meals jar (90% confident)
2. 🔧 add_money_to_jar_with_confidence() → ⚠️ Added $5.0 to meals jar (75% confident - moderate certainty)
3. 🔧 add_money_to_jar_with_confidence() → ✅ Added $65.0 to utilities jar (95% confident)
```

### **Vietnamese Language Support**
```
Input: "tôi ăn cơm 25k, mua xăng 100k"
Output:
🔄 Multiple Transactions Processed:
1. 🔧 add_money_to_jar_with_confidence() → ✅ Added $25.0 to meals jar (95% confident)
2. 🔧 add_money_to_jar_with_confidence() → ✅ Added $100.0 to gas jar (95% confident)
```

### **No Suitable Jar**
```
Input: "gym membership 30 dollar"
Output: 🔧 report_no_suitable_jar() → ❌ Cannot classify 'gym membership'. Consider creating a fitness jar
```

### **Need More Information**
```
Input: "50k"
Output: 🔧 request_more_info() → ❓ What was this $50 spent on?
```

## 🎮 Interactive Testing Features

Run `python test.py` for comprehensive testing:

### **Testing Modes:**
1. **📊 Display Context** - See current jars and transaction history
2. **🎯 Predefined Scenarios** - Run 25+ test cases automatically  
3. **🎮 Interactive Mode** - Type custom inputs for live testing
4. **🔧 Simple Mode** - Test with minimal prompts
5. **🚪 Exit**

### **Interactive Commands:**
- `context` - Show available jars and recent transactions
- `debug` - Toggle debug mode (see LLM prompts and tool calls)
- `quit` - Exit testing

### **Test Categories:**
- **High Confidence (90-100%)**: Clear transactions (gas, meals, rent) → Auto-classify with ✅
- **Medium Confidence (70-89%)**: Somewhat ambiguous (coffee, snack) → Auto-classify with ⚠️
- **Low Confidence (<70%)**: Ambiguous items → Use ask_for_confirmation with ❓
- **Multi-Transaction**: Various separator formats (comma, semicolon, "and")
- **Vietnamese Inputs**: Cultural context and language support
- **Edge Cases**: No jar matches, insufficient information

## 🔧 Configuration

Edit `.env` file:
```bash
GOOGLE_API_KEY=your_key_here
MODEL_NAME=gemini-2.5-flash-lite-preview-06-17
LLM_TEMPERATURE=0.1
DEBUG_MODE=false
```

## 📁 Project Structure

```
classifier_test/
├── config.py              # Configuration management with env vars
├── main.py                 # Core classifier with multi-tool-call support
├── tools.py                # LLM tools, mock jars & transaction data
├── prompt.py               # Intelligent prompt building with context
├── test.py                 # Interactive testing interface
├── requirements.txt        # Dependencies (LangChain, Google GenAI)
├── env.example             # Environment template
├── README.md               # This documentation
└── cursor_docs/            # AI assistant documentation
    ├── for_ai.md           # Core function overview
    ├── detail_context.md   # Implementation details  
    └── agent_detail.md     # Tool specifications
```

## 🎯 Key Features

### **✅ Confidence-Based Processing**
- **Smart auto-classification** - high confidence (90-100%) processes automatically
- **Moderate confidence warning** - medium confidence (70-89%) processes with ⚠️ indicator  
- **Uncertainty handling** - low confidence (<70%) asks for confirmation
- **Visual indicators** - ✅ ⚠️ ❓ for quick confidence assessment

### **✅ Multi-Transaction Support**  
- **Single LLM call** handles multiple transactions
- **Multiple tool calls** in one response
- **Various input formats** - "meal 20, gas 50" or "coffee 5; lunch 15"

### **✅ Vietnamese Language Support**
- **Cultural context** - understands Vietnamese spending patterns
- **Currency formats** - handles "k", "đô la", mixed language
- **Natural inputs** - "tôi ăn cơm 50k" processes correctly

### **✅ Smart Pattern Recognition**
- **Rich transaction history** - 50+ past transactions for context
- **Spending patterns** - learns from historical data
- **Amount validation** - reasonable spending amounts per category

## 🐛 Troubleshooting

**"GOOGLE_API_KEY required" error:**
- Set your Gemini API key in `.env` file

**"LLM did not call any classification tool" error:**
- LLM responded directly instead of using tools
- Try rephrasing input or enable debug mode

**Unrealistic confidence scores:**
- Check if jar names match exactly
- Verify transaction history provides good patterns
- Consider adjusting prompt guidelines in `prompt.py`

**Tool call format errors:**
- Ensure LangChain and Google GenerativeAI versions are compatible
- Verify API key has proper permissions for function calling

## 🏆 Success Criteria

- ✅ **Accurate confidence scoring** - matches human intuition about certainty
- ✅ **Smart decision making** - knows when to auto-classify vs ask for confirmation
- ✅ **Multi-transaction processing** - handles complex inputs correctly  
- ✅ **Vietnamese language support** - processes cultural context appropriately
- ✅ **Format flexibility** - extracts amounts from various input styles
- ✅ **Pattern recognition** - uses transaction history effectively
- ✅ **Tool selection** - chooses appropriate tools based on context
- ✅ **Minimal workflow interruption** - auto-processes high confidence transactions with transparency 