# Knowledge Base Agent - Implementation Context

## 🎯 Project Overview

This is a **Knowledge Base Agent** that provides comprehensive answers about financial concepts and personal finance app features using a **ReAct (Reason-Act-Observe) framework** with LangChain tool binding. The agent intelligently combines online search capabilities with hardcoded app documentation to deliver formatted, educational responses that help users understand both fundamental financial concepts and application functionality.

## 🏗️ System Architecture

### Core Components:
```
📁 knowledge_test/
├── 🧠 main.py              # ReAct framework implementation with conversational loop
├── 🛠️ tools.py             # 3 knowledge tools (search, app info, respond)
├── 📝 prompt.py            # ReAct prompts with explicit respond() requirements
├── ⚙️ config.py            # Configuration management (API keys, iterations, settings)
├── 🧪 test.py             # Comprehensive testing framework with validation
├── 📋 env.example         # Environment template
└── 📁 cursor_docs/        # Documentation for AI assistants
```

### ReAct Processing Flow:
```
User Query ("What is compound interest?")
         ↓
Question Analysis (financial concept)
         ↓
System Prompt Building (ReAct instructions + tool descriptions)
         ↓
ReAct Loop Start
         ↓
LLM Reasoning → Tool Selection (search_online)
         ↓
Tool Execution (DuckDuckGo search for compound interest)
         ↓
Tool Result Processing → Continue Conversation
         ↓
LLM Reasoning → Final Tool Selection (respond)
         ↓
Formatted Response Generation
         ↓
ReAct Loop End → Return Final Answer
```

### LangChain Implementation:
```python
class KnowledgeBaseAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=config.google_api_key,
            temperature=config.llm_temperature
        )
        
        # Bind all 3 knowledge tools to LLM
        self.tools = get_all_knowledge_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
    
    def get_knowledge(self, user_query: str) -> str:
        # Build ReAct system prompt with mandatory respond() requirement
        system_prompt = build_react_prompt()
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query)
        ]
        
        # ReAct Loop: Continue until respond() is called
        max_iterations = config.max_react_iterations
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Get LLM response with tools
        response = self.llm_with_tools.invoke(messages)
        
            # Add AI message to conversation
            messages.append(AIMessage(content=response.content, tool_calls=response.tool_calls))
            
            # Process tool calls
        if response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call.get('args', {})
                    
                    # Execute tool
                    result = execute_tool(tool_name, tool_args)
                    
                    # Check for respond() tool - END CONDITION
                    if tool_name == "respond":
                        return result.get("data", {}).get("final_answer", "")
                    
                    # Add tool result to conversation
                    messages.append(ToolMessage(content=str(result), tool_call_id=tool_call.get('id')))
                
                # Continue ReAct loop
                continue
        else:
                # No tool calls - direct response
                return response.content
        
        # Max iterations reached
        return "Could not provide complete answer within iteration limit"
```

## 🗂️ Knowledge Data Model

### Tool Result Structure:
```python
SEARCH_RESULT = {
    "data": {
        "query": "compound interest definition",           # Original search query
        "results": "Compound interest is...",            # DuckDuckGo search results
        "source": "online_search"                        # Tool identifier
    },
    "description": "online search for compound interest" # LLM-provided description
}

APP_INFO_RESULT = {
    "data": {
        "complete_app_info": {                          # Structured app documentation
            "app_overview": {...},
            "jar_system": {...},
            "budget_suggestions": {...},
            # ... all app features
        },
        "source": "app_documentation"
    },
    "description": "complete app information and features"
}

FINAL_RESPONSE = {
    "data": {
        "final_answer": "Compound interest is...",      # Complete formatted answer
        "response_type": "complete",                    # Completion indicator
        "source": "knowledge_assistant"                # Final source
    },
    "description": "explaining compound interest"       # Response description
}
```

### App Documentation Structure:
```python
APP_INFO = {
    "app_overview": {
        "name": "VPBank Personal Finance Assistant",
        "description": "Smart personal finance app for budgeting, tracking spending, and achieving financial goals automatically.",
        "main_features": [
            "🏺 Smart Budget Jars",
            "🤖 Automatic Transaction Sorting", 
            "💡 Smart Budget Suggestions",
            "📊 Advanced Search",
            "💳 Subscription Tracker"
        ]
    },
    
    "jar_system": {
        "overview": "Virtual budget jars for spending categories",
        "how_it_works": "Create jars for categories (groceries, dining, etc.), set budgets, transactions auto-sort into jars",
        "example": "Set $400 for groceries, see remaining balance after each shopping trip"
    },
    
    "budget_suggestions": {
        "overview": "Personalized budget recommendations based on spending patterns",
        "what_it_does": "Analyzes spending and suggests realistic budgets for each category",
        "example": "If you spend $350 on groceries, suggests $380 budget with saving tips"
    },
    
    "auto_categorization": {
        "overview": "Automatically sorts transactions into budget categories",
        "how_it_works": "Looks at transaction descriptions and amounts to assign to correct jar",
        "examples": [
            "Starbucks → Dining jar",
            "Shell Gas → Transportation jar",
            "Netflix → Entertainment jar"
        ]
    },
    
    "transaction_search": {
        "overview": "Find transactions using natural language",
        "features": "Search by amount, date, category, description, supports Vietnamese",
        "examples": [
            "Show coffee purchases last month",
            "Grocery shopping over $100",
            "Vietnamese: 'ăn trưa dưới 20 đô'"
        ]
    },
    
    "subscription_tracking": {
        "overview": "Track recurring payments and subscriptions",
        "features": "List subscriptions, renewal alerts, total monthly cost",
        "examples": "Netflix, Spotify, gym memberships, phone bills"
    }
}
```

## 🛠️ Knowledge Retrieval Tools (3 Specialized Tools)

### 1. **`search_online(query: str, description: str = "")`**

**Implementation:**
```python
@tool
def search_online(query: str, description: str = "") -> Dict[str, Any]:
    """
    Search online for financial knowledge and information using DuckDuckGo.
    
    Args:
        query: The search query for financial information
        description: What you're searching for
    
    Returns:
        Dict with search results
    """
    
    search_tool = DuckDuckGoSearchRun()
    
    # Enhance query with financial context for better results
    enhanced_query = f"{query} financial definition guide explanation"
    
    try:
        search_results = search_tool.run(enhanced_query)
        
        return {
            "data": {
                "query": query,
                "results": search_results,
                "source": "online_search"
            },
            "description": description or f"online search for: {query}"
        }
        
    except Exception as e:
    return {
            "data": {
                "query": query,
                "results": f"Search error: {str(e)}. Please try a different search term.",
                "source": "online_search"
            },
            "description": f"search error for: {query}"
    }
```

**Use Cases:**
- Financial concepts: "compound interest", "budgeting basics", "investment strategies"
- Economic terms: "inflation definition", "recession explanation"
- Banking topics: "credit score importance", "savings account types"
- Investment education: "diversification strategy", "risk management"

### 2. **`get_application_information(description: str = "")`**

**Implementation:**
```python
@tool
def get_application_information(description: str = "") -> Dict[str, Any]:
    """
    Get complete information about the personal finance app and all its features.
    Returns all app documentation in one call.
    
    Args:
        description: What app information you need
    
    Returns:
        Dict with all app information
    """
    
    # Comprehensive app documentation (see APP_INFO structure above)
    return {
        "data": {
            "complete_app_info": APP_INFO,
            "source": "app_documentation"
        },
        "description": description or "complete app information and features"
    }
```

**Features Covered:**
- **Jar System**: Virtual budgeting with category-based jars
- **Budget Suggestions**: AI-powered budget recommendations
- **Auto Categorization**: Smart transaction sorting
- **Transaction Search**: Advanced search capabilities
- **Subscription Tracking**: Recurring payment management
- **App Overview**: Core features and functionality

### 3. **`respond(answer: str, description: str = "")`**

**Implementation:**
```python
@tool
def respond(answer: str, description: str = "") -> Dict[str, Any]:
    """
    Provide the final response to the user's question.
    Call this tool when you have gathered enough information to answer the user's question.
    This stops the ReAct execution.
    
    Args:
        answer: The complete answer to the user's question
        description: Brief description of what you're responding about
        
    Returns:
        Dict with the final response
    """
    
    return {
        "data": {
            "final_answer": answer,
            "response_type": "complete",
            "source": "knowledge_assistant"
        },
        "description": description or "final response to user question"
    }
```

**Critical Requirements:**
- **Mandatory completion tool** - Must be called to end ReAct loop
- **Complete formatted answers** - Comprehensive explanations with examples
- **Clear language** - Accessible to users of all financial literacy levels
- **Structured information** - Well-organized responses with logical flow
- **Educational focus** - Teaching concepts rather than giving advice

## 🔄 ReAct Framework Implementation

### **Conversation Management:**
```python
def get_knowledge(self, user_query: str) -> str:
    # Initialize conversation with system prompt and user query
    messages = [
        SystemMessage(content=build_react_prompt()),
        HumanMessage(content=user_query)
    ]
    
    # ReAct Loop: Continue until respond() tool is called
    for iteration in range(config.max_react_iterations):
        # Get LLM response with tool selection
        response = self.llm_with_tools.invoke(messages)
        
        # Add AI response to conversation history
        messages.append(AIMessage(
            content=response.content, 
            tool_calls=response.tool_calls
        ))
        
        # Process tool calls if any
        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_result = execute_tool(tool_call)
                
                # Check for completion condition
                if tool_call['name'] == "respond":
                    return extract_final_answer(tool_result)
                
                # Add tool result to conversation
                messages.append(ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call.get('id')
                ))
            
            # Continue to next iteration
            continue
        else:
            # Direct response without tools
            return response.content
    
    # Max iterations reached
    return "Unable to provide complete answer within iteration limit"
```

### **Tool Selection Logic:**
The LLM automatically selects tools based on query analysis:

**Financial Questions** → `search_online()` → `respond()`
- "What is compound interest?" → Search for financial definition → Formatted explanation
- "How does budgeting work?" → Search for budgeting concepts → Comprehensive guide

**App Questions** → `get_application_information()` → `respond()`
- "How does the jar system work?" → Get app documentation → Feature explanation
- "What features does this app have?" → Get complete app info → Feature overview

**Mixed Questions** → `search_online()` + `get_application_information()` → `respond()`
- "What is budgeting and how does this app help?" → Search + App info → Combined response

## 🧪 Testing Framework

### **Test Categories:**
```python
TEST_CATEGORIES = {
    "financial_knowledge": [
        "What is compound interest?",
        "How does budgeting work?",
        "What are investment strategies?",
        "Explain emergency funds"
    ],
    "app_features": [
        "How does this app work?",
        "What is the jar system?",
        "Tell me about budget suggestions",
        "How does automatic categorization work?"
    ],
    "mixed_questions": [
        "What is budgeting and how does this app help?",
        "Explain savings and how to track them in the app"
    ]
}
```

### **Validation Criteria:**
```python
def validate_response(response: str, query: str) -> bool:
    # Check response length and quality
    if not response or len(response.strip()) < 10:
        return False
    
    # Check for error indicators
    error_indicators = ["error", "failed", "couldn't", "unable"]
    if any(indicator in response.lower() for indicator in error_indicators):
        return False
    
    # Check relevance to query
    query_words = query.lower().split()
    response_lower = response.lower()
    matching_words = sum(1 for word in query_words if word in response_lower)
    relevance_ratio = matching_words / len(query_words)
    
    return relevance_ratio > 0.2  # At least 20% relevance
```

## 🎯 Success Criteria

The Knowledge Base Agent is working effectively when:
- ✅ **Proper ReAct execution** with conversation loops ending in respond() calls
- ✅ **Accurate tool selection** based on question type analysis
- ✅ **High-quality responses** with clear explanations and practical examples
- ✅ **Complete information gathering** using appropriate knowledge sources
- ✅ **Educational value** helping users understand concepts and app features
- ✅ **Fast response times** through efficient ReAct iterations
- ✅ **Error handling** with graceful degradation and helpful error messages
- ✅ **Comprehensive coverage** of both financial concepts and app functionality

Remember: This agent serves as the **knowledge foundation** for financial education and app expertise, bridging the gap between complex financial concepts and practical application usage! 📚🎯
