reading: [text](for_ai.md)
reading: [text](detail_context.md)

> reading all files I sent
> Always reading to confirm instead of asssuming wrong context
> avoid hallucination efffectively by reading lines by lines and take note as you go

# Transaction Classifier Agent - Detailed Specifications

## 🎯 Agent Purpose

The **transaction_classifier** is an **LLM-powered agent** (using Gemini) that analyzes user spending descriptions and classifies them into appropriate budget jars. The LLM uses available tools to gather information and make intelligent classification decisions.

## 🧠 LLM-Powered Intelligence

### How It Works:
- **Fetch data first**: Get jar information and transaction history using utils
- **Build complete prompt**: Combine user input + jar data + classification task
- **Send to Gemini**: LLM receives all context and makes decision
- **Get jar classification**: Gemini decides which jar the transaction belongs to

### Simple Process:
1. **Data Gathering**: Fetch available jars and past transactions
2. **Prompt Building**: Create complete prompt with all necessary context
3. **Gemini Analysis**: LLM analyzes input and decides jar classification
4. **Result Return**: Get classification decision from Gemini

## 🔍 LLM Decision Process

### Input Processing:
```python
# User provides transaction descriptions like:
"meal 20 dollar"          # Clear description + amount
"cơm gà 25k"             # Vietnamese description + amount  
"50k"                    # Amount only (ambiguous)
"netflix subscription"    # Description only
"shopping"               # Vague description
```

### Implementation Flow:
```python
def classify_transaction(user_input: str):
    # 1. Fetch all necessary data
    jars = fetch_jar_information()
    past_transactions = fetch_past_transactions()
    
    # 2. Build complete prompt with confidence requirements
    prompt = f"""
    You are a transaction classifier. Classify the user's transaction into the appropriate jar.
    
    AVAILABLE JARS:
    {format_jars(jars)}
    
    PAST TRANSACTION PATTERNS:
    {format_transactions(past_transactions)}
    
    USER TRANSACTION: {user_input}
    
    REQUIRED FORMAT:
    JAR: [jar_name]
    CONFIDENCE: [0-100]%
    REASON: [explanation]
    
    CONFIDENCE GUIDELINES:
    - High (80-100%): Clear keyword match or strong pattern
    - Medium (50-79%): Possible match but needs confirmation
    - Low (0-49%): No suitable jar found
    """
    
    # 3. Send to Gemini
    response = llm.invoke(prompt)
    
    # 4. Parse and handle based on confidence
    jar, confidence, reason = parse_response(response)
    
    if confidence > 80:
        return f"✅ {jar} jar ({confidence}%) - {reason}"
    elif confidence >= 50:
        return f"❓ {jar} jar ({confidence}%) - {reason}. Is this correct?"
    else:
        return f"❌ No suitable jar ({confidence}%) - {reason}"
```

## 🛠️ Implementation Components

### 1. **Data Fetching Utils (Feed to LLM)**

#### `fetch_jar_information()`
- **Purpose**: Get all available budget jars with details
- **Returns**: List of jars with names, descriptions, keywords
- **Usage**: Provide context to LLM about available jars

#### `fetch_past_transactions(limit: int = 10)`
- **Purpose**: Get recent transaction history for pattern recognition
- **Returns**: List of recent transactions with classifications
- **Usage**: Help LLM understand user's spending patterns

### 2. **Classification Tools (LLM calls these)**

#### `add_money_to_jar(amount: float, jar_name: str)`
- **Purpose**: Add money to the specified jar when LLM is confident about classification
- **Parameters**: 
  - `amount`: Amount to add (extracted from user input)
  - `jar_name`: Name of the jar to add money to
- **Returns**: Confirmation message
- **Usage**: LLM calls when classification is clear and confident

#### `ask_for_confirmation(amount: float, jar_name: str, reason: str)`
- **Purpose**: Ask user for confirmation when LLM is uncertain about classification
- **Parameters**:
  - `amount`: Amount to potentially add
  - `jar_name`: Suggested jar name
  - `reason`: Why this jar was suggested
- **Returns**: Confirmation question for user
- **Usage**: LLM calls when unsure or when multiple jars could match

#### `report_no_suitable_jar(description: str, suggestion: str)`
- **Purpose**: Report that no existing jar matches the transaction
- **Parameters**:
  - `description`: The original transaction description
  - `suggestion`: Suggestion for what user could do (e.g., create new jar)
- **Returns**: "No suitable jar" message with helpful suggestion
- **Usage**: LLM calls when transaction doesn't fit any existing jar

#### `request_more_info(question: str)`
- **Purpose**: Ask user for more information when input is too ambiguous
- **Parameters**:
  - `question`: Specific question to ask user for clarification
- **Returns**: Question for user to provide more details
- **Usage**: LLM calls when user input lacks essential information (amount, description, etc.)

### Tool Implementation Example:
```python
from langchain_core.tools import tool

@tool
def add_money_to_jar(amount: float, jar_name: str) -> str:
    """Add money to the specified jar."""
    # Mock implementation - would update jar balance in real system
    return f"✅ Added ${amount} to {jar_name} jar"

@tool  
def ask_for_confirmation(amount: float, jar_name: str, reason: str) -> str:
    """Ask user for confirmation before adding money to jar."""
    return f"❓ Add ${amount} to {jar_name} jar? {reason}. Confirm (y/n):"

@tool
def report_no_suitable_jar(description: str, suggestion: str) -> str:
    """Report that no suitable jar was found for this transaction."""
    return f"❌ Cannot classify '{description}'. {suggestion}"

@tool
def request_more_info(question: str) -> str:
    """Ask user for more information about their transaction."""
    return f"❓ {question}"
```

## 🧪 LLM Testing Scenarios

### High Confidence Cases (>80%) - Direct Addition:
```python
Input: "meal 20 dollar"
Data: Food jar with keywords ["meal", "food", "lunch"]
LLM Action: Calls add_money_to_jar("Food", 20.0, "meal 20 dollar")
System Output: "✅ Added $20.0 to Food jar for 'meal 20 dollar'"
```

### Medium Confidence Cases (50-80%) - Ask Confirmation:
```python
Input: "50k"
Data: Past transactions show 50k typically for Food
LLM Action: Calls ask_confirmation("Food", 50.0, "Matches usual 50k lunch pattern")
System Output: "❓ Add $50.0 to Food jar? Matches usual 50k lunch pattern. Confirm (y/n):"
```

### Low Confidence Cases (<50%) - No Jar Found:
```python
Input: "crypto investment 100 dollar"
Data: No matching keywords in any jar
LLM Action: Calls report_no_jar_found("crypto investment 100 dollar", "No existing jar matches investment category")
System Output: "❌ Cannot classify 'crypto investment 100 dollar'. No existing jar matches investment category. Consider creating a new jar."
```

### Vietnamese Cases - Direct Addition:
```python
Input: "cơm gà 25k"
Data: Food jar with Vietnamese keywords ["cơm", "phở"]
LLM Action: Calls add_money_to_jar("Food", 25.0, "cơm gà 25k")
System Output: "✅ Added $25.0 to Food jar for 'cơm gà 25k'"
```

### Ambiguous Cases - Ask Confirmation:
```python
Input: "shopping"
Data: Multiple possible jars (Food for groceries, Entertainment for items)
LLM Action: Calls ask_confirmation("Food", 0, "Could be groceries or entertainment items")
System Output: "❓ Add $0 to Food jar? Could be groceries or entertainment items. Confirm (y/n):"
```

### Pattern Recognition - Direct Addition:
```python
Input: "25k lunch"
Data: Clear food keywords plus typical lunch amount
LLM Action: Calls add_money_to_jar("Food", 25.0, "25k lunch")
System Output: "✅ Added $25.0 to Food jar for '25k lunch'"
```

## 🎯 Expected Behaviors

### High Confidence Classification (>80%):
```
Input: "meal 20 dollar"
Gemini: "JAR: Food, CONFIDENCE: 95%, REASON: Direct keyword match with meal"
System: "✅ Food jar (95%) - Direct keyword match with meal"
```

### Medium Confidence - Ask for Confirmation (50-80%):
```
Input: "50k"
Gemini: "JAR: Food, CONFIDENCE: 70%, REASON: Matches your typical 50k lunch pattern"
System: "❓ Food jar (70%) - Matches your typical 50k lunch pattern. Is this correct?"
```

### Ambiguous Cases - Need Confirmation:
```
Input: "shopping"
Gemini: "JAR: Food, CONFIDENCE: 60%, REASON: Could be groceries or entertainment items"
System: "❓ Food jar (60%) - Could be groceries or entertainment items. Is this correct?"
```

### Low Confidence - No Suitable Jar (<50%):
```
Input: "crypto investment 100 dollar"
Gemini: "JAR: None, CONFIDENCE: 15%, REASON: No existing jar matches investment category"
System: "❌ No suitable jar (15%) - No existing jar matches investment category"
```

### Pattern Recognition with Confidence:
```
Input: "25k lunch"
Gemini: "JAR: Food, CONFIDENCE: 85%, REASON: Clear food keywords plus typical lunch amount"
System: "✅ Food jar (85%) - Clear food keywords plus typical lunch amount"
```

## 🔧 Implementation Notes

### Simple Architecture:
- **No tool calling complexity** - just fetch data and send to Gemini
- **Direct prompt approach** - all context provided upfront
- **Single LLM call** - Gemini makes decision with complete information

### Prompt Design Focus:
- **Clear data presentation**: How to format jars and transactions
- **Task instructions**: Clear classification guidelines for Gemini
- **Response format**: How Gemini should structure its answers
- **Vietnamese support**: Include Vietnamese examples and context

### Testing Strategy:
- **Prompt iterations**: Test different ways to present data to Gemini
- **Data formatting**: Find optimal structure for jar/transaction info
- **Response consistency**: Ensure reliable classification decisions

This is a **simple, direct LLM classification system** - fetch data, build prompt, get Gemini decision!
