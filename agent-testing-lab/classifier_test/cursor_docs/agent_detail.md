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

#### `add_money_to_jar_with_confidence(amount: float, jar_name: str, confidence: int)`
- **Purpose**: Add money to the specified jar when LLM is confident about classification
- **Parameters**: 
  - `amount`: Amount to add (extracted from user input)
  - `jar_name`: Name of the jar to add money to
  - `confidence`: Confidence score (0-100)
- **Returns**: Confirmation message with confidence indicator
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
def add_money_to_jar_with_confidence(amount: float, jar_name: str, confidence: int) -> str:
    """Add money to the specified jar with confidence score."""
    if confidence >= 90:
        return f"✅ Added ${amount} to {jar_name} jar ({confidence}% confident)"
    elif confidence >= 70:
        return f"⚠️ Added ${amount} to {jar_name} jar ({confidence}% confident - moderate certainty)"
    else:
        return f"❓ Added ${amount} to {jar_name} jar ({confidence}% confident - please verify)"

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
LLM Action: Calls add_money_to_jar_with_confidence(20.0, "meals", 95)
System Output: "✅ Added $20.0 to meals jar (95% confident)"
```

### Medium Confidence Cases (50-80%) - Ask Confirmation:
```python
Input: "50k"
Data: Past transactions show 50k typically for Food
LLM Action: Calls add_money_to_jar_with_confidence(50.0, "meals", 75)
System Output: "⚠️ Added $50.0 to meals jar (75% confident - moderate certainty)"
```

### Low Confidence Cases (<50%) - No Jar Found:
```python
Input: "crypto investment 100 dollar"
Data: No matching keywords in any jar
LLM Action: Calls report_no_suitable_jar("crypto investment 100 dollar", "Consider creating an investment jar")
System Output: "❌ Cannot classify 'crypto investment 100 dollar'. Consider creating an investment jar"
```

### Vietnamese Cases - Direct Addition:
```python
Input: "cơm gà 25k"
Data: Food jar with Vietnamese keywords ["cơm", "phở"]
LLM Action: Calls add_money_to_jar_with_confidence(25.0, "meals", 95)
System Output: "✅ Added $25.0 to meals jar (95% confident)"
```

### Ambiguous Cases - Ask Confirmation:
```python
Input: "shopping"
Data: Multiple possible jars (Food for groceries, Entertainment for items)
LLM Action: Calls ask_for_confirmation(0, "meals", "Could be groceries or entertainment items")
System Output: "❓ Add $0 to meals jar? Could be groceries or entertainment items. Confirm (y/n):"
```

## 🎯 Expected Behaviors

### High Confidence Classification (>80%):
```
Input: "meal 20 dollar"
LLM: Calls add_money_to_jar_with_confidence(20.0, "meals", 95)
System: "✅ Added $20.0 to meals jar (95% confident)"
```

### Medium Confidence - With Transparency (50-80%):
```
Input: "50k"
LLM: Calls add_money_to_jar_with_confidence(50.0, "meals", 70)
System: "⚠️ Added $50.0 to meals jar (70% confident - moderate certainty)"
```

### Ambiguous Cases - Need Confirmation:
```
Input: "shopping"
LLM: Calls ask_for_confirmation(0, "meals", "Could be groceries or entertainment items")
System: "❓ Add $0 to meals jar? Could be groceries or entertainment items. Confirm (y/n):"
```

### Low Confidence - No Suitable Jar (<50%):
```
Input: "crypto investment 100 dollar"
LLM: Calls report_no_suitable_jar("crypto investment", "Consider creating an investment jar")
System: "❌ Cannot classify 'crypto investment'. Consider creating an investment jar"
```

### Pattern Recognition with Confidence:
```
Input: "25k lunch"
LLM: Calls add_money_to_jar_with_confidence(25.0, "meals", 90)
System: "✅ Added $25.0 to meals jar (90% confident)"
```

## 🔧 Implementation Notes

### Simple Architecture:
- **No complex patterns** - just fetch data and send to Gemini
- **Direct prompt approach** - all context provided upfront
- **Single LLM call** - Gemini makes decision with complete information
- **Confidence-based responses** - transparent scoring for user understanding

### Prompt Design Focus:
- **Clear data presentation**: How to format jars and transactions
- **Task instructions**: Clear classification guidelines for Gemini
- **Response format**: How Gemini should structure its answers
- **Vietnamese support**: Include Vietnamese examples and context
- **Confidence scoring**: Guidelines for when to be certain vs uncertain

### Testing Strategy:
- **Prompt iterations**: Test different ways to present data to Gemini
- **Data formatting**: Find optimal structure for jar/transaction info
- **Response consistency**: Ensure reliable classification decisions
- **Multi-transaction support**: Handle multiple items in single input

This is a **simple, direct LLM classification system** with confidence transparency - fetch data, build prompt, get Gemini decision with clear confidence indicators!
