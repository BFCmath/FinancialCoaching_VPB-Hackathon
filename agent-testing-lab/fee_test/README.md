# Fee Manager Test Lab

LLM-powered recurring fee pattern recognition and management system using Gemini 2.5 Flash Lite with LangChain tool calling.

## 🎯 Overview

This is a **development testing lab** for an LLM-powered fee manager agent that:
- Analyzes natural language fee descriptions (English + Vietnamese)
- Creates structured recurring patterns (daily, weekly, monthly, biweekly) 
- Calculates next occurrence dates with edge case handling
- Provides confidence-based responses with detailed debug output
- Uses LangChain tool calling for fee management operations

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Copy environment template
cp env.example .env

# Add your Gemini API key to .env
GOOGLE_API_KEY=your_api_key_here
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Test the System
```bash
# Interactive testing with full interface
python test.py

# Direct testing with pattern examples
python main.py
```

## 🧪 Testing Capabilities

### Pattern Recognition Examples:

#### English Patterns:
```bash
"5 dollar daily for coffee"                        # Daily pattern
"10 dollar every Monday and Friday for commute"    # Weekly pattern with specific days
"50 dollar every 15th for insurance"              # Monthly pattern with date
"30 dollar every other Monday for cleaning"        # Bi-weekly pattern
```

#### Vietnamese Patterns:
```bash
"phí đi lại hằng tuần 25k từ thứ 2 đến thứ 6"     # Weekly Monday-Friday transport
"30k mỗi thứ hai cho xe buýt"                     # Weekly Monday bus fare
```

#### Complex Patterns:
```bash
"20 dollar weekdays for lunch"                     # Weekly Monday-Friday
"subscription for stuff"                           # Ambiguous - triggers clarification
```

## 🛠️ Current Features

### LLM Tool Calling:
- **create_recurring_fee()** - Create new fees with schedule patterns
- **adjust_recurring_fee()** - Modify existing fees (amount, pattern, jar, disable)
- **delete_recurring_fee()** - Deactivate fees with reason tracking
- **list_recurring_fees()** - List active/inactive fees with filters
- **request_clarification()** - Ask for clarification on ambiguous input

### Schedule Calculation:
- **Daily patterns** - Next day occurrence
- **Weekly patterns** - Multiple days support (e.g., Mon+Fri, weekdays)
- **Monthly patterns** - Specific dates with month-end edge case handling
- **Bi-weekly patterns** - Every other week on specified day

### Development Features:
- **Enhanced debug output** - Track all data transformations
- **No fallback error handling** - All errors exposed for debugging
- **Type safety validation** - Handle LangChain parameter serialization
- **Confidence-based responses** - Different formats based on LLM confidence

## 📊 Current Budget Jars

The system uses a database-driven jar selection approach:

```python
JARS_DATABASE = [
    {"name": "meals", "budget": 500, "current": 212, "description": "Dining out, food delivery, and coffee shop purchases"},
    {"name": "transport", "budget": 300, "current": 89, "description": "Public transportation, ride-sharing, gas, and parking fees"},
    {"name": "utilities", "budget": 200, "current": 156, "description": "Internet, phone, streaming subscriptions, and insurance"}
]
```

## 🔧 Configuration

### Environment Variables:
```bash
GOOGLE_API_KEY=your_gemini_api_key
MODEL_NAME=gemini-2.5-flash-lite-preview-06-17  # Optional, defaults to this
LLM_TEMPERATURE=0.1                              # Optional, defaults to 0.1
DEBUG_MODE=true                                  # Optional, defaults to false
```

### Confidence Thresholds:
- **High confidence (≥90%)**: ✅ Direct confirmation
- **Medium confidence (70-89%)**: ⚠️ Moderate certainty note
- **Low confidence (<70%)**: ❓ "Please verify" note

## 🧪 Testing Modes

### Interactive Mode:
```bash
python test.py
```
- Full testing interface with system commands
- Fee creation, listing, adjustment, deletion
- Enhanced debug output with fee summary
- Mock data initialization

### Quick Test Mode:
```bash
python test.py quick
```
- Rapid pattern recognition testing
- Pre-defined test cases
- Confidence score validation

### Direct Testing:
```bash
python main.py
```
- Run built-in test scenarios
- Automated pattern recognition validation
- Vietnamese language support testing

## 📅 Sample Test Cases

### Test Vietnamese Input:
```bash
> phí đi lại hằng tuần 25k từ thứ 2 đến thứ 6
✅ Created recurring fee: Phí đi lại hàng tuần - $25.0 weekly → transport jar. Next: 2025-07-09 (95% confident)
```

### Test Complex Weekly Pattern:
```bash
> 10 dollar every Monday and Friday for commute  
✅ Created recurring fee: Weekly commute - $10.0 weekly → transport jar. Next: 2025-07-11 (90% confident)
```

### Test Debug Output:
```bash
> summary
🔍 DEBUG: Total fees in storage: 3
🔍 DEBUG: Active fees: 3
🔍 DEBUG Fee 1: Daily coffee
   Type: <class 'dict'> = {}
   Pattern: daily
   Amount: $5.0
   Jar: meals
   Monthly calc (daily): $5.0 * 30 = $150.0
```

## 🐛 Development Focus

This is a **testing lab** with development-oriented features:

### Error Transparency:
- No fallback error handling - all errors exposed
- Full exception stack traces printed
- Type validation without silent failures

### Debug Information:
- Complete data type inspection
- Pattern details validation logging
- Schedule calculation step-by-step tracking
- Tool execution parameter logging

### Pattern Edge Cases:
- Month-end date handling (Feb 31st → Feb 28th/29th)
- Vietnamese language number parsing ("25k" = 25.0)
- Complex weekly patterns ("weekdays" = Mon-Fri)
- Bi-weekly synchronization with start dates

## 🎯 Success Criteria

The system is working correctly when:
- ✅ **LLM correctly parses** natural language into structured patterns
- ✅ **Tools execute properly** with correct parameter types
- ✅ **Schedule calculation accurate** for all pattern types
- ✅ **Vietnamese language support** works correctly
- ✅ **Debug output helpful** for tracking system behavior
- ✅ **No hidden errors** - all issues exposed for development

## 🚫 What This Is NOT

This is **NOT**:
- A production recurring payment system
- A persistent database solution
- A complex calendar management system
- A notification or reminder system

This **IS**:
- A testing lab for LLM pattern recognition
- A schedule calculation validation tool
- A development debugging environment
- A tool calling integration test platform

---

**Remember**: Focus on testing LLM pattern recognition accuracy and schedule calculation correctness!
