# AI Assistant Guide - Transaction Classifier Agent Test Lab

## 🤖 Quick Start for AI Assistants

This is a **prompt testing lab** for a transaction classifier agent. Your job is to help users test and improve classifier prompts that analyze transactions and route them to appropriate budget jars.

### Core Understanding
- **NOT a backend system** - it's a testing tool for the classifier agent
- **Focus:** Test if prompts can classify transactions into correct jars
- **User philosophy:** Extreme simplicity, no over-engineering, interactive testing only

## 🎯 Primary Use Cases

### 1. Classification Testing
Help users test classifier prompts by:
- Running interactive tests via `python test.py`
- Testing transaction classification accuracy
- Verifying jar matching logic

### 2. Prompt Improvement  
Help users improve classifier prompts by:
- Editing `prompt.py` CLASSIFICATION_PROMPT section
- Adding/modifying classification examples
- Adjusting jar matching criteria

### 3. Tool Interface Testing
Help users test classifier tools by:
- Testing jar information fetching
- Testing transaction pattern analysis
- Testing clarification mechanisms

## 🏗️ Classifier Agent Architecture

### LLM-Powered System:
- **Gemini LLM** analyzes transaction inputs using classification prompt
- **LLM calls tools** to gather jar information and transaction history  
- **LLM makes decisions** based on tool results and prompt instructions
- **LLM generates responses** using appropriate response tools
- **Similar to orchestrator** but focused on transaction classification

### Main Features:
1. **Jar Information Fetching** - LLM calls tools to get jar data
2. **Transaction History Analysis** - LLM calls tools to check patterns
3. **Smart Classification** - LLM analyzes and decides jar assignment
4. **Missing Jar Handling** - LLM responds when no suitable jar exists
5. **Clarification System** - LLM asks user for confirmation when uncertain

### LLM Flow:
```
User Input ("meal 20 dollar") → 
Fetch jar data & transaction history → 
Build prompt with data + task → 
Send to Gemini → 
Gemini decides jar classification → 
Return result
```

## 🧪 Testing Scenarios

### High Confidence (>80%):
- "meal 20 dollar" → Food jar (clear keyword match)
- "gas 30k" → Transportation jar (direct match)
- "netflix subscription" → Entertainment jar (subscription pattern)

### Medium Confidence (50-80% - Ask for confirmation):
- "50k" → "Food jar (70%) - matches your usual lunch pattern. Is this correct?"
- "shopping" → "Food jar (60%) - could be groceries or entertainment. Is this correct?"
- "coffee" → "Food jar (65%) - could be drink or cafe visit. Is this correct?"

### Low Confidence (<50% - No suitable jar):
- "crypto investment" → "No suitable jar (15%) - no existing jar matches investment"
- "charity donation" → "No suitable jar (20%) - no jar for charitable giving"

### Vietnamese Support with Confidence:
- "cơm gà 25k" → Food jar (90%) - Vietnamese meal description
- "xăng 30k" → Transportation jar (85%) - Vietnamese fuel term

## 🚨 Critical Do's and Don'ts

### ✅ DO
- **Keep everything simple** - this is the user's top priority
- **Focus on classification testing** - the core purpose
- **Use mock data** for jars and transactions
- **Test clarification flows** - key classifier feature
- **Test pattern recognition** - important for user experience
- **Maintain minimal configuration** - only essential settings

### ❌ DON'T  
- **Add real database connections** - use mock data only
- **Create complex jar management** - focus on classification only
- **Add persistent storage** - stateless operation preferred
- **Over-engineer data structures** - simple mock objects
- **Add authentication** - development tool only
- **Create conversation state** - each classification is independent

## 🔧 Key Implementation Components

### 1. **Data Fetching (Utils Functions)**
```python
fetch_jar_information() -> List[Jar]  # Get available jars (feed to LLM)
fetch_past_transactions() -> List[Transaction]  # Get transaction history (feed to LLM)
```

### 2. **Classification Tools (LLM calls these)**
```python
add_money_to_jar(jar_name, amount, description) -> str  # Add money to jar (high confidence)
ask_confirmation(jar_name, amount, reason) -> str  # Ask for confirmation (medium confidence)
report_no_jar_found(description, reason) -> str  # No suitable jar (low confidence)
```

## Core Function - classify_and_add_transaction()

### Purpose:
Process user transaction input and automatically classify it into the appropriate jar using LLM analysis and tool calling.

### Process:
1. **Fetch Context Data**: Get jar information and past transaction history using utility functions
2. **Build Complete Prompt**: Combine user input + context data + available tools for LLM
3. **LLM Analysis**: Gemini analyzes the transaction and naturally decides which tool to call
4. **Execute Action**: Run the tool call chosen by the LLM and return the result

### Tool Options for LLM:
- **`add_money_to_jar(amount, jar_name)`**: When classification is clear and confident
- **`ask_for_confirmation(amount, jar_name, reason)`**: When uncertain or multiple jars could match  
- **`report_no_suitable_jar(description, suggestion)`**: When no existing jar fits the transaction
- **`request_more_info(question)`**: When user input lacks essential information

### Implementation Flow:
```python
def classify_and_add_transaction(user_input: str):
    # Get context data
    jars = fetch_jar_information()
    past_transactions = fetch_past_transactions()
    
    # Build prompt with tools
    prompt = f"""
    Analyze this transaction: "{user_input}"
    
    Available jars: {jars}
    Past patterns: {past_transactions}
    
    Choose the most appropriate action by calling one of these tools:
    - add_money_to_jar(amount, jar_name) - when confident
    - ask_for_confirmation(amount, jar_name, reason) - when uncertain
    - report_no_suitable_jar(description, suggestion) - when no match
    - request_more_info(question) - when need more details
    """
    
    # LLM decides and calls tool
    response = llm_with_tools.invoke(prompt)
    
    # Execute the chosen tool
    return execute_tool_call(response.tool_calls[0])
```

### Key Features:
- **Natural Decision Making**: LLM uses its judgment instead of explicit confidence thresholds
- **Context-Aware**: Uses jar data and transaction history for pattern recognition
- **Flexible Actions**: Four different tools for different situations
- **Simple Testing**: Easy to test with `python test.py` using mock data

## 🎯 Success Criteria

The classifier agent is working well when:
- ✅ **Accurate jar matching** for clear transactions
- ✅ **Smart pattern recognition** from transaction history
- ✅ **Appropriate clarification** when uncertain
- ✅ **Proper "no jar" responses** when no match exists
- ✅ **Consistent tool usage** throughout the process

Remember: This is about testing the **classifier's decision-making ability**, not building a production system!
