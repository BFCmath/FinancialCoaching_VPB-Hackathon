# Budget Advisor Agent - Detailed Specifications

## 🎯 Agent Purpose

The **Budget Advisor Agent** is a **financial planning consultant and advisory expert** that provides comprehensive financial guidance using an intelligent ReAct (Reason-Act-Observe) framework. It acts as a **financial advisor** that analyzes user spending patterns, manages budget plans, and creates detailed jar adjustment proposals while coordinating with specialized agents (transaction fetcher, jar manager) for data gathering.

## 🧠 Advisory Intelligence System

### Core Capabilities:
- **Financial Situation Analysis**: LLM analyzes spending patterns, jar allocations, and existing plans
- **ReAct Advisory Framework**: Continuous reasoning cycles for comprehensive financial guidance
- **Multi-Agent Coordination**: Integrates with transaction fetcher and jar manager for data
- **Integrated Plan Management**: Creates/adjusts budget plans with detailed jar proposals in single operations
- **Interactive Memory System**: Remembers conversation history for natural follow-up discussions
- **Advisory Expertise**: Provides personalized recommendations based on real financial data
- **Vietnamese Language Support**: Handles financial planning queries in Vietnamese with cultural context

### ReAct Architecture:
```
User Query → Analyze Request → Gather Data → Analyze Situation → Create/Adjust Plans → Provide Advice
```

## 🗂️ Budget Planning Data Model

### Budget Plan Structure:
```python
BUDGET_PLAN = {
    "name": str,                        # Unique plan name
    "detail_description": str,          # Comprehensive plan description
    "day_created": str,                 # Creation date (ISO format)
    "status": str,                      # "active", "paused", "completed"
    
    # Jar Recommendations (when included)
    "jar_recommendations": str          # Detailed jar adjustment proposals
}
```

### Memory System Structure:
```python
CONVERSATION_HISTORY = [
    (user_input: str, agent_response: str),  # Tuple of user query and agent response
    ...  # Up to max_memory_turns entries
]

MEMORY_CONFIG = {
    "enable_memory": bool,              # Memory system toggle
    "max_memory_turns": int,            # Maximum conversation pairs to remember
    "conversation_history": list        # Stored conversation pairs
}
```

### Tool Result Structures:
```python
TRANSACTION_RESULT = {
    "data": [
        {
            "amount": float,
            "jar": str,
            "description": str,
            "date": str,
            "time": str,
            "source": str
        }
    ],
    "description": str                 # Context summary
}

JAR_RESULT = {
    "data": [
        {
            "name": str,
            "budget": float,
            "current": float,
            "percent": float,
            "status": str,             # "under", "over", "on_track"
            "description": str
        }
    ],
    "description": str
}

PLAN_RESULT = {
    "data": [
        {
            "name": str,
            "detail_description": str,
            "day_created": str,
            "status": str
        }
    ],
    "description": str
}

CREATE_PLAN_RESULT = {
    "data": {
        "name": str,
        "detail_description": str,
        "day_created": str,
        "status": str,
        "jar_recommendations": str      # When jar_propose_adjust_details provided
    },
    "description": str                  # Includes jar recommendation summary
}

ADJUST_PLAN_RESULT = {
    "data": {
        "name": str,
        "detail_description": str,
        "day_created": str,
        "status": str,
        "jar_recommendations": str      # When jar_propose_adjust_details provided
    },
    "description": str                  # Includes changes and jar recommendations
}

ADVISORY_RESPONSE = {
    "data": {
        "summary": str,                 # Financial situation analysis
        "advice": str,                  # Personalized recommendations (optional)
        "question_ask_user": str        # Follow-up question when clarification needed (optional)
    },
    "description": str
}
```

## 🛠️ Budget Advisory Tools (6 Specialized Tools)

### **Data Gathering Tools:**

### 1. **`transaction_fetcher(user_query: str, description: str = "")`**

**Purpose:** Retrieve spending transaction data for financial analysis

**Parameters:**
- `user_query`: Natural language transaction query (e.g., "groceries spending", "lunch transactions 11am-2pm under $20", "ăn trưa dưới 20 đô")
- `description`: Context for what data is needed (optional)

**Returns:** `{"data": [...], "description": str}` - Transaction data with analysis context

**Use Cases:**
- General spending analysis: "spending patterns last 3 months"
- Category analysis: "meals transactions last month"
- Vietnamese queries: "ăn trưa dưới 20 đô"
- Time-specific queries: "coffee purchases this week"

**Implementation Details:**
```python
@tool
def transaction_fetcher(user_query: str, description: str = "") -> Dict[str, Any]:
    # Direct import from the data agent's tools
    from tool_agent.data.tools import get_jar_transactions
    
    result = get_jar_transactions.invoke({
        "description": description or f"transaction query: {user_query}"
    })
    
    return result
```

### 2. **`get_jar(jar_name: str = None, description: str = "")`**

**Purpose:** Get current jar allocations and balances (MUST call to see user's jar status)

**Parameters:**
- `jar_name`: Specific jar to analyze (optional - gets all jars if None)
- `description`: Context for what jar information is needed

**Returns:** `{"data": [...], "description": str}` - Jar allocation data and status

**Use Cases:**
- Overview: "all jar status and allocations"
- Specific jar: jar_name="meals" for meals jar analysis
- System check: "6-jar system overview"
- Budget status: "current jar utilization rates"

**Implementation Details:**
```python
@tool  
def get_jar(jar_name: str = None, description: str = "") -> Dict[str, Any]:
    # Direct import using importlib to avoid conflicts
    import importlib.util
    import os
    
    jar_tools_path = os.path.join(os.path.dirname(__file__), 'tool_agent', 'jar', 'tools.py')
    spec = importlib.util.spec_from_file_location("jar_tools", jar_tools_path)
    jar_tools = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(jar_tools)
    
    fetch_existing_jars = jar_tools.fetch_existing_jars
    
    # Filter by jar_name if specified
    if jar_name:
        all_jars = fetch_existing_jars()
        jars = [jar for jar in all_jars if jar.get("name", "").lower() == jar_name.lower()]
    else:
        jars = fetch_existing_jars()
    
    return {
        "data": jars,
        "description": description or f"retrieved {len(jars)} jars"
    }
```

### 3. **`get_plan(status: str = "active", description: str = "")`**

**Purpose:** Retrieve existing budget plans by status for analysis

**Parameters:**
- `status`: Plan status filter - "active" (default), "completed", "paused", "all"
- `description`: Context for what plan information is needed

**Returns:** `{"data": [...], "description": str}` - Budget plans matching criteria

**Use Cases:**
- Current plans: status="active" for active plans overview
- Historical analysis: status="completed" for completed plans
- Comprehensive review: status="all" for all plans
- Specific search: description="vacation plan details"

**Implementation Details:**
```python
@tool
def get_plan(status: str = "active", description: str = "") -> Dict[str, Any]:
    if status == "all":
        plans = list(BUDGET_PLANS_STORAGE.values())
    else:
        plans = [p for p in BUDGET_PLANS_STORAGE.values() if p.get("status") == status]
    
    return {
        "data": plans,
        "description": description or f"retrieved {len(plans)} {status} plans"
    }
```

### **Plan Management Tools with Integrated Jar Proposals:**

### 4. **`create_plan(name: str, description: str, status: str = "active", jar_propose_adjust_details: str = None)`**

**Purpose:** Create new budget plans with comprehensive jar adjustment proposals

**Parameters:**
- `name`: Plan name (must be unique)
- `description`: Plan description
- `status`: Plan status - "active" (default), "completed", "paused"
- `jar_propose_adjust_details`: **DETAILED jar adjustments needed for this plan (should have a reason to change)**

**Returns:** `{"data": {...}, "description": str}` - Created plan with jar recommendations

**Key Features:**
- **Integrated jar proposals** - No separate proposal step needed
- **Comprehensive recommendations** - Detailed jar allocation adjustments
- **Reasoning required** - Must justify jar changes
- **Impact analysis** - Consider effect on existing jars

**Jar Proposal Requirements:**
The `jar_propose_adjust_details` should be comprehensive and include:
- Specific jar names and exact allocation amounts/percentages
- Reasoning for each jar modification
- Timeline and target amounts
- Impact on existing jars and rebalancing details
- Monthly savings calculations

**Use Cases:**
- Vacation planning with jar setup
- Emergency fund creation with allocation changes
- Debt payoff plan with spending adjustments
- Investment goal with systematic savings

**Implementation Details:**
```python
@tool
def create_plan(name: str, description: str, status: str = "active", jar_propose_adjust_details: str = None) -> Dict[str, Any]:
    if name in BUDGET_PLANS_STORAGE:
        return {"data": {}, "description": f"plan {name} already exists"}
    
    plan = BudgetPlan(
        name=name,
        detail_description=description,
        day_created=datetime.now().isoformat(),
        status=status
    )
    
    BUDGET_PLANS_STORAGE[name] = plan.to_dict()
    
    # Build response with jar recommendations
    response_data = plan.to_dict()
    description_parts = [f"created plan {name} with status {status}"]
    
    if jar_propose_adjust_details:
        response_data["jar_recommendations"] = jar_propose_adjust_details
        description_parts.append(f"jar recommendations: {jar_propose_adjust_details}")
    
    return {
        "data": response_data,
        "description": " | ".join(description_parts)
    }
```

### 5. **`adjust_plan(name: str, description: str = None, status: str = None, jar_propose_adjust_details: str = None)`**

**Purpose:** Modify existing budget plans with comprehensive jar adjustment proposals

**Parameters:**
- `name`: Plan name to modify
- `description`: New description (optional)
- `status`: New status - "active", "completed", "paused" (optional)
- `jar_propose_adjust_details`: **DETAILED and COMPREHENSIVE jar adjustments needed for this plan update (should have a reason to change)**

**Returns:** `{"data": {...}, "description": str}` - Updated plan with jar recommendations

**Key Features:**
- **Plan modification tracking** - Records changes made
- **Integrated jar adjustments** - Updates jar proposals with plan changes
- **Comprehensive rebalancing** - Considers impact of plan updates on jar system

**Jar Adjustment Requirements:**
The `jar_propose_adjust_details` should be comprehensive for plan updates and include:
- Specific jar names and exact allocation amounts/percentages
- Reasoning for each jar modification based on plan changes
- Updated timeline and target amounts
- Impact on existing jars and complete rebalancing strategy
- Revised monthly savings calculations

**Use Cases:**
- Timeline extension with adjusted monthly targets
- Goal amount increase with allocation changes
- Status change with jar rebalancing
- Plan refinement with optimized allocations

**Implementation Details:**
```python
@tool
def adjust_plan(name: str, description: str = None, status: str = None, jar_propose_adjust_details: str = None) -> Dict[str, Any]:
    if name not in BUDGET_PLANS_STORAGE:
        return {"data": {}, "description": f"plan {name} not found"}
    
    plan = BUDGET_PLANS_STORAGE[name].copy()
    changes = []
    
    # Update description if provided
    if description is not None:
        old_desc = plan["detail_description"]
        plan["detail_description"] = description
        changes.append(f"description: {old_desc} → {description}")
    
    # Update status if provided
    if status is not None:
        old_status = plan["status"]
        plan["status"] = status
        changes.append(f"status: {old_status} → {status}")
    
    # Save updated plan
    BUDGET_PLANS_STORAGE[name] = plan
    
    # Build response with jar recommendations
    response_data = plan.copy()
    description_parts = [f"updated plan {name}: {', '.join(changes) if changes else 'no changes made'}"]
    
    if jar_propose_adjust_details:
        response_data["jar_recommendations"] = jar_propose_adjust_details
        description_parts.append(f"jar recommendations: {jar_propose_adjust_details}")
    
    return {
        "data": response_data,
        "description": " | ".join(description_parts)
    }
```

### **Advisory Response Tool:**

### 6. **`respond(summary: str, advice: str = None, question_ask_user: str = None)`**

**Purpose:** Provide final advisory response with optional follow-up question (MANDATORY - ends ReAct execution)

**Parameters:**
- `summary`: Analysis summary of financial situation
- `advice`: Personalized recommendations (optional)
- `question_ask_user`: Follow-up question to ask the user for more information when the user's plan is not clear (optional)

**Returns:** `{"data": {...}, "description": str}` - Complete advisory response

**Key Features:**
- **Session completion** - Ends ReAct loop execution
- **Comprehensive advice** - Financial situation analysis and recommendations
- **Interactive capability** - Can ask follow-up questions for clarification
- **Memory integration** - Response becomes part of conversation history

**Use Cases:**
- Complete consultation: All information gathered, provide full advice
- Clarification needed: Ask for missing details (income, timeline, etc.)
- Follow-up questions: Continue previous conversation with memory context
- Multi-step planning: Break complex planning into manageable steps

**Implementation Details:**
```python
@tool
def respond(summary: str, advice: str = None, question_ask_user: str = None) -> Dict[str, Any]:
    if not summary.strip():
        return {"data": {}, "description": "missing summary"}
    
    response_data = {"summary": summary}
    if advice is not None:
        response_data["advice"] = advice
    if question_ask_user is not None:
        response_data["question_ask_user"] = question_ask_user
    
    description_parts = ["advisory response with summary"]
    if advice:
        description_parts.append("advice")
    if question_ask_user:
        description_parts.append("follow-up question")
    
    return {
        "data": response_data,
        "description": " and ".join(description_parts)
    }
```

## 🔄 Memory System Implementation

### Configuration:
```python
MEMORY_CONFIG = {
    "enable_memory": True,              # Toggle for memory system
    "max_memory_turns": 10              # Conversation history limit
}
```

### Memory Storage:
```python
# In BudgetAdvisorTester class
self.conversation_history = []  # [(user_input, agent_response), ...]
```

### Memory Usage in Prompts:
```python
def build_budget_advisor_prompt(user_input, context, conversation_history):
    history_info = ""
    if conversation_history and len(conversation_history) > 0:
        history_items = []
        for user_msg, agent_response in conversation_history[-10:]:  # Last 10 interactions
            history_items.append(f"User: {user_msg}")
            history_items.append(f"Assistant: {agent_response[:200]}...")  # Truncate responses
        history_info = f"\nCONVERSATION HISTORY:\n" + "\n".join(history_items) + "\n"
    
    # Include history_info in system prompt
    return system_prompt_with_history
```

### Memory Integration:
- **Interactive Mode Only**: Memory disabled for non-interactive usage
- **Automatic Storage**: Conversations stored after each interaction
- **Context Awareness**: Previous plans and advice referenced
- **Natural Flow**: Follow-up questions and continued planning

## 🎯 Workflow Patterns

### **Complete Financial Planning (New Goal):**
```
1. get_plan(status="active") → Check existing plans
2. get_jar() → Current jar allocations and status
3. transaction_fetcher("spending patterns") → Historical spending analysis
4. create_plan(name="Goal", description="...", jar_propose_adjust_details="Detailed jar proposals...") → Plan + jar recommendations
5. respond(summary="Analysis complete", advice="Specific recommendations") → Final advice
```

### **Plan Modification with Jar Updates:**
```
1. get_plan(description="specific plan details") → Current plan status
2. get_jar() → Current jar allocations
3. adjust_plan(name="Plan", jar_propose_adjust_details="Updated jar strategy...") → Modified plan + new jar proposals
4. respond(summary="Plan updated", advice="Implementation steps") → Updated recommendations
```

### **Interactive Consultation with Memory:**
```
1. User: "I want to save for vacation"
2. Agent: get_jar() → create_plan(..., jar_propose_adjust_details="...") → respond(..., question_ask_user="What's your monthly income?")
3. User: "$8,000 per month" [Memory: Previous conversation context available]
4. Agent: [References previous vacation plan] → respond(summary="Based on $8k income...", advice="Specific percentage allocations")
```

### **Spending Analysis with Recommendations:**
```
1. transaction_fetcher("comprehensive spending analysis") → Historical data
2. get_jar() → Current allocations vs. actual spending
3. respond(summary="Spending analysis complete", advice="Optimization recommendations")
```

## 🚨 Critical Implementation Requirements

### ✅ **MUST DO:**
- **Always call respond()** - Every session must end with advisory response
- **Use get_jar()** - Must check current jar status for any financial advice
- **Include jar proposals** - When creating/adjusting plans, provide detailed jar_propose_adjust_details
- **Comprehensive proposals** - Jar adjustments must include reasoning, amounts, and impact analysis
- **Leverage memory** - Reference previous conversation context in interactive mode
- **Vietnamese support** - Handle Vietnamese financial queries naturally

### ❌ **NEVER DO:**
- **Skip respond() call** - This is mandatory for session completion
- **Assume jar status** - Always get current jar data before recommendations
- **Generic jar proposals** - Must be specific with amounts, percentages, and reasoning
- **Ignore conversation history** - Use memory context for natural follow-up

## 🔧 Error Handling & Debugging

### No Fallback Strategy:
- **All try/catch blocks removed** for error visibility
- **Direct error propagation** shows exact failure points
- **Tool execution logging** for debugging tool calls
- **ReAct iteration tracking** shows reasoning steps

### Debug Information:
- **Tool call details** logged during execution
- **LLM response types** and content shown
- **Memory state** tracked in interactive mode
- **Jar integration status** visible during jar tool calls

## 🌍 Vietnamese Language Support

### Supported Query Types:
- Financial planning: "tôi muốn tiết kiệm tiền cho kỳ nghỉ"
- Budget creation: "tạo kế hoạch ngân sách cho chuyến đi"
- Spending analysis: "phân tích chi tiêu và đưa ra lời khuyên"
- Specific goals: "tôi muốn đi nhật, 15000 đô, trong 3 tháng tới"

### Response Capability:
- **Vietnamese responses** when appropriate
- **Cultural context** understanding for financial planning
- **Mixed language** support (Vietnamese query, English response, or vice versa)

## 🧪 Testing Framework Integration

### Test Categories:
- **Interactive Testing**: Real conversation with memory system
- **Tool Validation**: Individual tool functionality verification
- **ReAct Simulation**: Complete workflow testing
- **Vietnamese Support**: Localized query handling

### Memory Testing:
```python
# Test conversation continuity
conversation_history = []
response1 = agent.process("I want to save for Japan trip", conversation_history)
response2 = agent.process("How much monthly?", conversation_history)  # References previous context
```

---

This comprehensive specification reflects the current Budget Advisor implementation with integrated jar proposals, memory system, and streamlined workflow for efficient financial consultation.
