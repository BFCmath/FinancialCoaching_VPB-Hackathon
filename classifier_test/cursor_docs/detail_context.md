# Transaction Classifier Agent Test Lab - Detailed Context

## 🎯 Project Overview

This is a minimal testing environment for a **transaction classifier agent powered by Gemini LLM** that analyzes user spending descriptions and classifies them into appropriate budget jars. The LLM uses tools to gather information and make intelligent classification decisions. The primary goal is to test and improve the classifier's prompt quality.

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
- Clear match → LLM calls add_money_to_jar(amount, jar_name)
- Uncertain → LLM calls ask_for_confirmation(amount, jar_name, reason)
- No match → LLM calls report_no_suitable_jar(description, suggestion)
- Need info → LLM calls request_more_info(question)
         ↓
Execute the tool call and return result
```

### Implementation with Natural Decision Making:
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
    - add_money_to_jar(amount, jar_name) - Add money when you're confident
    - ask_for_confirmation(amount, jar_name, reason) - Ask when uncertain
    - report_no_suitable_jar(description, suggestion) - When no jar matches
    - request_more_info(question) - When you need more information
    
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
def add_money_to_jar(amount: float, jar_name: str) -> str:
    """Add money to the specified jar when confident about classification."""
    return f"✅ Added ${amount} to {jar_name} jar"

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
- **LLM calls response tools** to generate final output

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
classify_transaction(description, amount, jar_name, confidence, reason)
# LLM: "I'm classifying this as Food jar with 90% confidence"

request_clarification(description, suggested_jars, question)
# LLM: "I need to ask which jar they meant"

confirm_classification(jar_name, amount, confidence, reason)
# LLM: "Final confirmation of classification"

report_no_suitable_jar(description, reason)
# LLM: "No matching jar found"
```

## 🧪 LLM Testing Scenarios

### High Confidence LLM Behavior:
```python
Input: "meal 20 dollar"
LLM Process:
1. Analyzes input with classification prompt
2. Calls fetch_jar_information()
3. Sees Food jar with keywords ["meal", "food", "lunch"]
4. High confidence match
5. Calls confirm_classification("Food", 20.0, 0.95, "Direct keyword match")
```

### Medium Confidence LLM Behavior:
```python
Input: "50k"
LLM Process:
1. Analyzes ambiguous input
2. Calls fetch_jar_information()
3. Multiple possible matches
4. Calls fetch_past_transactions()
5. Sees pattern of 50k Food expenses
6. Calls request_clarification("50k", ["Food"], "Is this for Food like your usual lunch?")
```

### Low Confidence LLM Behavior:
```python
Input: "crypto investment 100 dollar"
LLM Process:
1. Analyzes unusual input
2. Calls fetch_jar_information()
3. No matching keywords in any jar
4. No historical patterns
5. Calls report_no_suitable_jar("crypto investment", "No existing jar matches investment category")
```

## 📊 Mock Data Examples (Tool Returns)

### Sample Jars (returned by fetch_jar_information):
```python
MOCK_JARS = [
    Jar("Food", "Daily meals and groceries", ["meal", "food", "lunch", "dinner", "grocery", "restaurant", "cơm", "phở"], 30.0, 150.0),
    Jar("Transportation", "Commute and travel expenses", ["gas", "fuel", "uber", "taxi", "bus", "commute", "xăng"], 20.0, 80.0),
    Jar("Entertainment", "Fun and leisure activities", ["movie", "game", "book", "music", "netflix"], 15.0, 45.0),
    Jar("Save", "Emergency and future savings", ["save", "emergency", "future"], 35.0, 200.0)
]
```

### Sample Transaction History (returned by fetch_past_transactions):
```python
MOCK_TRANSACTIONS = [
    Transaction("lunch pho restaurant", 25.0, "Food", "2024-01-15", 0.95),
    Transaction("cơm gà 50k", 50.0, "Food", "2024-01-14", 0.90),  # Pattern for "50k"
    Transaction("gas station", 30.0, "Transportation", "2024-01-14", 0.90),
    Transaction("netflix subscription", 10.0, "Entertainment", "2024-01-13", 0.88),
    Transaction("grocery shopping", 80.0, "Food", "2024-01-12", 0.92)
]
```

## 🎯 LLM Prompt Testing Focus

### Classification Prompt (prompt.py):
- **Tool usage instructions**: When and how to call each tool
- **Decision criteria**: How to evaluate confidence and make decisions
- **Response patterns**: How to generate helpful responses
- **Vietnamese support**: Understanding mixed language inputs
- **Always use tools**: Never respond directly without calling tools

### Success Metrics for LLM:
- **Accurate tool selection**: Calls right tools in right sequence
- **Good decision making**: Makes sensible classifications based on tool data
- **Appropriate confidence**: Knows when to ask for clarification
- **Clear responses**: Generates helpful, understandable outputs
- **Vietnamese handling**: Properly processes Vietnamese inputs

This system tests **LLM classification intelligence** using tools, just like the orchestrator system!
