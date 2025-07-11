# Transaction Classifier Agent Test Lab - Detailed Context

## 🎯 Project Overview

This is a minimal testing environment for a **transaction classifier agent powered by Gemini LLM** that analyzes user spending descriptions and classifies them into appropriate budget jars. The LLM uses tools to gather information and make intelligent classification decisions with confidence scoring. The primary goal is to test and improve the classifier's prompt quality.

## 🏗️ System Architecture

### Core Components:
```
📁 classifier_test/
├── 🧠 main.py           # Core classifier logic and LLM tool processing
├── 🛠️ tools.py          # Tool definitions for LLM to use  
├── 📝 prompt.py         # Classification prompt (THE THING WE'RE TESTING)
├── ⚙️ config.py         # Simple configuration (Gemini API key)
├── 🧪 test.py          # Interactive testing interface
├── 📋 env.example      # Environment template
└── 📁 cursor_docs/     # Documentation for AI assistants
```

### LLM-Powered Data Flow:
```
User Transaction Input ("meal 20 dollar")
         ↓
Fetch jar data + transaction history (utils functions)
         ↓
Prepare prompt with: [user input] + [jar data] + [available tools]
         ↓
Send complete prompt to Gemini LLM
         ↓
LLM analyzes and decides which tool to call:
- Clear match → LLM calls add_money_to_jar_with_confidence(amount, jar_name, confidence)
- Uncertain → LLM calls ask_for_confirmation(amount, jar_name, reason)
- No match → LLM calls report_no_suitable_jar(description, suggestion)
- Need info → LLM calls request_more_info(question)
         ↓
Execute the tool call and return result with confidence indicators
```

### Implementation with Confidence-Based Decision Making:
```python
def classify_and_add_transaction(user_input: str):
    # 1. Fetch data (utils functions)
    jars = fetch_jar_information()
    past_transactions = fetch_past_transactions()
    
    # 2. Prepare prompt with tools available
    full_prompt = f"""
    You are a transaction classifier. Analyze this transaction and take appropriate action.
    
    AVAILABLE JARS: {jars}
    PAST TRANSACTIONS: {past_transactions}
    USER INPUT: {user_input}
    
    AVAILABLE TOOLS:
    - add_money_to_jar_with_confidence(amount, jar_name, confidence) - Add with confidence score (0-100)
    - ask_for_confirmation(amount, jar_name, reason) - Ask when uncertain
    - report_no_suitable_jar(description, suggestion) - When no jar matches
    - request_more_info(question) - When you need more information
    
    CONFIDENCE GUIDELINES:
    - 90-100%: Very certain (exact keyword match, clear transaction)
    - 70-89%: Moderately certain (good match but some ambiguity)  
    - 50-69%: Uncertain (multiple possible jars, should use ask_for_confirmation)
    
    Analyze the transaction and call the most appropriate tool.
    """
    
    # 3. Send to Gemini with tools bound
    response = llm_with_tools.invoke(full_prompt)
    
    # 4. Execute the tool call Gemini made
    return execute_tool_call(response.tool_calls[0])
```

### Tool Definitions:
```python
@tool
def add_money_to_jar_with_confidence(amount: float, jar_name: str, confidence: int) -> str:
    """Add money to the specified jar with confidence score (0-100)."""
    if confidence >= 90:
        return f"✅ Added ${amount} to {jar_name} jar ({confidence}% confident)"
    elif confidence >= 70:
        return f"⚠️ Added ${amount} to {jar_name} jar ({confidence}% confident - moderate certainty)"
    else:
        return f"❓ Added ${amount} to {jar_name} jar ({confidence}% confident - please verify)"

@tool  
def ask_for_confirmation(amount: float, jar_name: str, reason: str) -> str:
    """Ask user for confirmation when uncertain about classification."""
    return f"❓ Add ${amount} to {jar_name} jar? {reason}. Confirm (y/n):"

@tool
def report_no_suitable_jar(description: str, suggestion: str) -> str:
    """Report when no existing jar matches the transaction."""
    return f"❌ Cannot classify '{description}'. {suggestion}"

@tool
def request_more_info(question: str) -> str:
    """Ask user for more information when input is ambiguous."""
    return f"❓ {question}"
```

## 🧠 LLM Architecture (Similar to Orchestrator)

### How It Works:
- **Gemini LLM** receives transaction input and classification prompt
- **LLM analyzes** the input using the prompt instructions
- **LLM calls tools** to gather jar data and transaction history
- **LLM processes** tool results to make classification decision
- **LLM calls response tools** to generate final output with confidence scores

### Tool Binding:
```python
# Similar to orchestrator_test/main.py
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite-preview-06-17")
llm_with_tools = llm.bind_tools(ALL_CLASSIFIER_TOOLS)
```

## 🛠️ Tool Categories for LLM

### Information Fetching Tools (LLM calls these):
```python
fetch_jar_information() -> List[Jar]
# LLM: "Let me see what jars are available"

get_jar_by_name(name: str) -> Optional[Jar] 
# LLM: "User mentioned Food jar, let me get details"

fetch_past_transactions(limit: int = 10) -> List[Transaction]
# LLM: "Let me check spending patterns for this amount"
```

### Analysis Tools (LLM calls these):
```python
analyze_transaction_patterns(description: str) -> List[PossibleMatch]
# LLM: "This description is similar to past transactions"

match_keywords_to_jars(description: str) -> List[JarMatch]
# LLM: "These keywords suggest these jars"

calculate_confidence_score(description: str, jar_name: str) -> float
# LLM: "How confident am I about this match?"
```

### Response Tools (LLM calls these):
```python
add_money_to_jar_with_confidence(amount, jar_name, confidence)
# LLM: "I'm classifying this as meals jar with 90% confidence"

ask_for_confirmation(amount, jar_name, reason)
# LLM: "I need to ask which jar they meant"

report_no_suitable_jar(description, suggestion)
# LLM: "No matching jar found, suggest creating new one"

request_more_info(question)
# LLM: "Need more details about the transaction"
```

## 🧪 LLM Testing Scenarios

### High Confidence LLM Behavior (90-100%):
```python
Input: "meal 20 dollar"
LLM Process:
1. Analyzes input with classification prompt
2. Calls fetch_jar_information()
3. Sees meals jar with keywords ["meal", "food", "lunch"]
4. High confidence match
5. Calls add_money_to_jar_with_confidence(20.0, "meals", 95)
Output: "✅ Added $20.0 to meals jar (95% confident)"
```

### Medium Confidence LLM Behavior (70-89%):
```python
Input: "coffee 5 dollar"
LLM Process:
1. Analyzes input with some ambiguity
2. Calls fetch_jar_information()
3. Could be meals or entertainment
4. Moderate confidence for meals
5. Calls add_money_to_jar_with_confidence(5.0, "meals", 75)
Output: "⚠️ Added $5.0 to meals jar (75% confident - moderate certainty)"
```

### Uncertain LLM Behavior (<70%):
```python
Input: "shopping"
LLM Process:
1. Analyzes ambiguous input
2. Calls fetch_jar_information()
3. Multiple possible matches (groceries vs entertainment)
4. Too uncertain to decide automatically
5. Calls ask_for_confirmation(0, "meals", "Could be groceries or entertainment items")
Output: "❓ Add $0 to meals jar? Could be groceries or entertainment items. Confirm (y/n):"
```

### No Match LLM Behavior:
```python
Input: "crypto investment 100 dollar"
LLM Process:
1. Analyzes unusual input
2. Calls fetch_jar_information()
3. No matching keywords in any jar
4. No historical patterns
5. Calls report_no_suitable_jar("crypto investment", "Consider creating an investment jar")
Output: "❌ Cannot classify 'crypto investment'. Consider creating an investment jar"
```

## 📊 Mock Data Examples (Tool Returns)

### Sample Jars (returned by fetch_jar_information):
```python
MOCK_JARS = [
    Jar("rent", "Monthly rent or mortgage payment", ["rent", "mortgage"], 1250.0, 1250.0),
    Jar("groceries", "Food and household essentials", ["grocery", "supermarket", "food"], 270.0, 400.0),
    Jar("utilities", "Essential services", ["electric", "water", "internet", "bill"], 65.0, 200.0),
    Jar("gas", "Fuel and vehicle expenses", ["gas", "fuel", "petrol", "xăng"], 103.0, 200.0),
    Jar("meals", "Dining out and food delivery", ["meal", "lunch", "dinner", "restaurant", "cơm", "phở"], 212.0, 500.0),
    Jar("transport", "Public transportation", ["bus", "taxi", "uber", "train"], 18.0, 100.0)
]
```

### Sample Transaction History (returned by fetch_past_transactions):
```python
MOCK_TRANSACTIONS = [
    Transaction("lunch pho restaurant", 25.0, "meals", "2024-01-15", 95),
    Transaction("cơm gà 50k", 50.0, "meals", "2024-01-14", 90),  # Pattern for "50k"
    Transaction("gas station fill up", 30.0, "gas", "2024-01-14", 90),
    Transaction("netflix subscription", 10.0, "entertainment", "2024-01-13", 88),
    Transaction("grocery shopping weekly", 80.0, "groceries", "2024-01-12", 92),
    Transaction("coffee morning", 5.0, "meals", "2024-01-12", 85),
    Transaction("bus fare work", 10.0, "transport", "2024-01-11", 95)
]
```

## 🎯 LLM Prompt Testing Focus

### Classification Prompt (prompt.py):
- **Tool usage instructions**: When and how to call each tool
- **Confidence guidelines**: Clear criteria for different confidence levels
- **Decision criteria**: How to evaluate matches and make decisions
- **Response patterns**: How to generate helpful responses with transparency
- **Vietnamese support**: Understanding mixed language inputs
- **Multi-transaction handling**: Process multiple items in single input
- **Always use tools**: Never respond directly without calling tools

### Success Metrics for LLM:
- **Accurate tool selection**: Calls right tools in right sequence
- **Appropriate confidence scoring**: Realistic confidence levels that match human intuition
- **Good decision making**: Makes sensible classifications based on tool data
- **Clear responses**: Generates helpful, understandable outputs with confidence indicators
- **Vietnamese handling**: Properly processes Vietnamese inputs
- **Multi-transaction support**: Handles complex inputs with multiple transactions

This system tests **LLM classification intelligence** with confidence transparency using tools, just like the orchestrator system!
