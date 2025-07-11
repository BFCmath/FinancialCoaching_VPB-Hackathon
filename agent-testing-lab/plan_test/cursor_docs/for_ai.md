# AI Assistant Guide - Budget Advisor Agent

## 🤖 Quick Start for AI Assistants

This is a **Budget Advisor Agent** that provides **financial planning analysis and advice** using intelligent ReAct framework with LangChain tool binding. The agent acts as a **financial consultant** that analyzes user situations, provides personalized advice, and creates/adjusts budget plans with integrated jar proposals for comprehensive financial guidance.

### Core Understanding
- **Financial planning consultant** - Analyzes spending, creates budget plans, provides personalized advice
- **Integrated jar proposals** - Plan creation/adjustment includes detailed jar recommendations
- **Interactive memory** - Remembers conversation history for natural follow-up
- **Multi-agent integration** - Coordinates with transaction fetcher and jar manager for data
- **ReAct framework** - Uses Reason-Act-Observe cycle for comprehensive analysis and advice
- **6 specialized tools** - Data gathering, plan management, and advisory response tools
- **LangChain integration** - Uses tool binding for intelligent analysis and advisory workflow
- **Vietnamese support** - Handles financial planning queries in Vietnamese language

## 🎯 Primary Use Cases

### 1. Financial Advisory & Analysis
Provide comprehensive financial guidance based on spending analysis:
- "I'm overspending on meals, help me fix my budget"
- "How can I save $2000 for vacation in 6 months?"
- "Analyze my spending patterns and give me advice"
- "Can I afford a $800 laptop next month?"
- "Help me optimize my budget to save more"

### 2. Budget Plan Management with Jar Integration
Create and adjust comprehensive budget plans with detailed jar proposals:
- "Create a budget plan for emergency fund savings"
- "I want to save $15,000 for Japan trip in 3 months"
- "Update my vacation plan - extend deadline by 2 months"
- "Show me my current budget plans and progress"

### 3. Interactive Conversation with Memory
Natural follow-up conversations remembering previous context:
- "What about my vacation plan?" (references previous discussion)
- "Can you explain that jar proposal more?" (remembers recommendation)
- "How much should I save monthly?" (continues planning conversation)

### 4. Vietnamese Financial Planning
Support localized financial planning queries:
- "tôi muốn tiết kiệm tiền cho kỳ nghỉ" (I want to save money for vacation)
- "tạo kế hoạch ngân sách cho chuyến đi" (create budget plan for trip)
- "phân tích chi tiêu và đưa ra lời khuyên" (analyze spending and give advice)
- "tôi muốn đi nhật, 15000 đô, trong 3 tháng tới"

## 🏗️ Agent Architecture

### **ReAct Framework Pattern:**
```
User Query → Analyze Request → Gather Data → Analyze Situation → Create/Adjust Plans → Provide Advice
```

### **Integrated Workflow (No Separate Proposals):**
```
Financial Question → transaction_fetcher() + get_jar() + get_plan() → create_plan(with jar_propose_adjust_details) → respond()
Plan Request → get_plan() → create_plan(with detailed jar proposals) → respond()
Plan Update → get_plan() → adjust_plan(with jar adjustments) → respond()
```

### **LangChain Tool Binding Implementation:**
```python
# All 6 tools bound to LLM for intelligent advisory workflow
BUDGET_ADVISOR_TOOLS = [
    transaction_fetcher,
    get_jar,
    get_plan,
    create_plan,
    adjust_plan,
    respond
]

llm_with_tools = llm.bind_tools(BUDGET_ADVISOR_TOOLS)

# ReAct loop continues until respond() is called
while iteration < max_iterations:
    response = llm_with_tools.invoke(messages)
    if "respond" tool called:
        return final_advice_with_questions
    else:
        continue_analysis()
```

### Memory System Integration:
```python
# Interactive mode with conversation history
def process_with_agent(user_input, conversation_history):
    if config.enable_memory and conversation_history:
        history_to_pass = conversation_history[-config.max_memory_turns:]
    
    response = provide_budget_advice(user_input, llm_with_tools, history_to_pass)
    
    # Store for next interaction
    conversation_history.append((user_input, response))
    return response
```

## 🛠️ Budget Advisory Tools (6 Core Tools)

### **Data Gathering Tools:**

### 1. **`transaction_fetcher(user_query: str, description: str = "")`**
**Purpose:** Get spending transaction data for analysis

**Parameters:**
- `user_query`: Natural language transaction query
- `description`: Context for what data is needed

**Returns:** Dict with transaction data and spending patterns

**Use Cases:**
- "Last 3 months spending analysis" → `transaction_fetcher("spending patterns last 3 months")`
- "Meals overspending data" → `transaction_fetcher("meals transactions last month")`
- "Vietnamese query support" → `transaction_fetcher("ăn trưa dưới 20 đô")`

### 2. **`get_jar(jar_name: str = None, description: str = "")`**
**Purpose:** Get current jar allocations and balances (MUST call to see user's jar status)

**Parameters:**
- `jar_name`: Specific jar to analyze (optional for all jars)
- `description`: Context for what jar information is needed

**Returns:** Dict with jar allocations, balances, and budget status

**Use Cases:**
- "Current jar allocations" → `get_jar(description="all jar status")`
- "Meals jar analysis" → `get_jar(jar_name="meals")`
- "T. Harv Eker system status" → `get_jar(description="6-jar system overview")`

### 3. **`get_plan(status: str = "active", description: str = "")`**
**Purpose:** Retrieve budget plans by status

**Parameters:**
- `status`: Plan status - "active" (default), "completed", "paused", "all"
- `description`: Context for what plan info is needed

**Returns:** Dict with budget plans matching status

**Use Cases:**
- "Show my current plans" → `get_plan(status="active")`
- "Get vacation plan" → `get_plan(description="vacation plan details")`

### **Plan Management Tools with Integrated Jar Proposals:**

### 4. **`create_plan(name: str, description: str, status: str = "active", jar_propose_adjust_details: str = None)`**
**Purpose:** Create new budget plans with comprehensive jar adjustment proposals

**Parameters:**
- `name`: Plan name (must be unique)
- `description`: Plan description 
- `status`: Plan status - "active" (default), "completed", "paused"
- `jar_propose_adjust_details`: **DETAILED jar adjustments needed for this plan (should have a reason to change)**

**Returns:** Dict with created plan and jar recommendations

**Key Feature:** **Integrated jar proposals** - no separate proposal tool needed

**Use Cases:**
- Vacation planning → `create_plan("Japan Trip", "Save $15k in 3 months", "active", "Create Japan Trip jar with $5,000/month allocation...")`
- Emergency fund → `create_plan("Emergency Fund", "Build 6-month expenses", "active", "Increase Long-term Savings jar from 10% to 15%...")`

### 5. **`adjust_plan(name: str, description: str = None, status: str = None, jar_propose_adjust_details: str = None)`**
**Purpose:** Modify existing budget plans with comprehensive jar adjustment proposals

**Parameters:**
- `name`: Plan name to modify
- `description`: New description (optional)
- `status`: New status (optional)
- `jar_propose_adjust_details`: **DETAILED and COMPREHENSIVE jar adjustments needed for this plan update (should have a reason to change)**

**Returns:** Dict with updated plan and jar recommendations

**Use Cases:**
- Timeline change → `adjust_plan("Japan Trip", status="active", jar_propose_adjust_details="Extend timeline to 6 months, reduce monthly from $5k to $2.5k...")`
- Goal increase → `adjust_plan("Emergency Fund", jar_propose_adjust_details="Increase target, boost Long-term Savings to 20%...")`

### **Response Tool:**

### 6. **`respond(summary: str, advice: str = None, question_ask_user: str = None)`**
**Purpose:** Provide final advisory response with optional follow-up question (MANDATORY - ends ReAct)

**Parameters:**
- `summary`: Analysis summary of financial situation
- `advice`: Personalized recommendations (optional)
- `question_ask_user`: Follow-up question for more information when user's plan is not clear (optional)

**Returns:** Dict with advisory response and optional question

**Use Cases:**
- Complete advice → `respond("Plan created successfully", "Start saving $5k monthly", None)`
- Need clarification → `respond("Initial analysis done", "Preliminary recommendations ready", "What's your monthly income for precise calculations?")`

## 📋 Tool Result Structures:

```python
TRANSACTION_RESULT = {
    "data": [{"amount": float, "jar": str, "description": str, "date": str}],
    "description": str
}

JAR_RESULT = {
    "data": [{"name": str, "budget": float, "current": float, "percent": float}],
    "description": str
}

PLAN_RESULT = {
    "data": [{"name": str, "detail_description": str, "status": str, "day_created": str}],
    "description": str
}

CREATE_PLAN_RESULT = {
    "data": {
        "name": str,
        "detail_description": str,
        "status": str,
        "day_created": str,
        "jar_recommendations": str  # When jar_propose_adjust_details provided
    },
    "description": str
}

ADVISORY_RESPONSE = {
    "data": {
        "summary": str,
        "advice": str,
        "question_ask_user": str  # When follow-up needed
    },
    "description": str
}
```

## 🎯 Key Workflow Patterns:

### **Goal Planning (Integrated Approach):**
```
1. get_plan() → Check existing plans
2. get_jar() → Current jar status  
3. transaction_fetcher() → Spending analysis
4. create_plan(with detailed jar_propose_adjust_details) → Plan + jar proposals
5. respond() → Final advice
```

### **Plan Updates:**
```
1. get_plan() → Current plan status
2. adjust_plan(with jar_propose_adjust_details) → Update + jar adjustments
3. respond() → Updated recommendations
```

### **Interactive Follow-up:**
```
1. Previous conversation remembered via memory
2. respond(question_ask_user="Need more details?") → Ask for clarification
3. User responds with details
4. Continue with specific recommendations
```

## 💡 Best Practices for AI Assistants:

### **Always Use Jar Proposals:**
- Include `jar_propose_adjust_details` when creating/adjusting plans
- Make proposals detailed and comprehensive
- Provide reasoning for each jar change

### **Leverage Memory System:**
- Reference previous conversation context
- Build on earlier recommendations
- Ask follow-up questions when needed

### **Vietnamese Language Support:**
- Process Vietnamese queries naturally
- Respond in Vietnamese when appropriate
- Understand Vietnamese financial terminology

### **Error Visibility:**
- No fallback error handling - errors show directly
- Debug information available for troubleshooting
- Tool execution details logged

## 🔄 Memory & Conversation Flow:

The agent remembers conversation history in interactive mode:
- **Previous questions** and responses stored
- **Context awareness** for follow-up questions  
- **Natural conversation** flow maintained
- **Plan references** carried forward

Example conversation flow:
```
User: "I want to save for Japan vacation"
Agent: [Creates plan with jar proposals] + "What's your monthly income?"
User: "$8,000"
Agent: [Continues with specific percentage calculations based on income]
```

This creates a natural, consultant-like experience where the agent builds on previous interactions to provide increasingly specific and personalized financial advice.
