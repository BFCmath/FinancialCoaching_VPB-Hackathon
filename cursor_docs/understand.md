# VPBank Hackathon - AI Financial Coach Chatbot Project Understanding

## Project Overview
- **Purpose**: AI Financial Coach system implementing 6-jar budgeting methodology for Vietnamese users
- **Focus**: Testing orchestrator prompt quality, NOT building full backend
- **Goal**: Test if orchestrator can correctly analyze user requests, decompose them, and route to specific workers

## 6-Jar Budgeting System
The core financial methodology:
- **Necessities (55%)** - Essential expenses
- **Long-Term Savings (10%)** - Future financial security  
- **Financial Freedom (10%)** - Investment/passive income
- **Education (10%)** - Learning and skill development
- **Play (10%)** - Entertainment and enjoyment
- **Give (5%)** - Charity and helping others

## System Architecture

### Core Workflow
```
User Input → Gemini Analysis → Routing Decision → Worker Assignment(s)
```

### Orchestrator Component (orchestrator_test/)
**Purpose**: Central routing system that analyzes user requests and routes to appropriate workers

**Key Features**:
- Single worker routing for simple requests
- Multi-worker routing for complex requests  
- Request decomposition for unclear requests
- Interactive CLI testing interface
- Mock mode for API-free testing

**Available Workers**:
1. **jar_manager** - Budget jar operations (create, update, delete, view jars)
2. **transaction_classifier** - Logging and classifying transactions
3. **budget_advisor** - Financial planning, savings goals, spending analysis
4. **knowledge_base** - Financial education and answering questions
5. **direct_response** - Greetings, clarifications, simple responses

**Routing Types**:
- **Single Worker**: "Add vacation jar 10%" → route_to_jar_manager()
- **Multi-Worker**: "I spent $100 on groceries and want to add vacation jar" → route_to_multiple_workers()
- **Decomposition**: "Help me with finances" → decompose_complex_request()

**Tech Stack**: Gemini 2.5-flash-lite-preview, LangChain, Python

**Philosophy**: Extreme simplicity, no over-engineering, interactive testing only

---

### Transaction Classifier Component (classifier_test/)
**Purpose**: LLM-powered agent that analyzes user spending descriptions and classifies them into appropriate budget jars

**Key Features**:
- **Gemini LLM** analyzes transaction inputs using classification prompts
- **Confidence-based decision making** (0-100% confidence scores)
- **Tool-driven architecture** - LLM calls tools to gather data and respond
- **Pattern recognition** from past transaction history
- **Multi-language support** (English and Vietnamese)

**Process Flow**:
1. **Fetch data**: Get jar information + past transaction history
2. **Build prompt**: Combine user input + context data + available tools
3. **LLM analysis**: Gemini analyzes and decides which tool to call
4. **Execute action**: Run chosen tool and return result

**Tools Available to LLM**:
- `add_money_to_jar_with_confidence(amount, jar_name, confidence)` - High confidence (>80%)
- `ask_for_confirmation(amount, jar_name, reason)` - Medium confidence (50-80%)
- `report_no_suitable_jar(description, suggestion)` - Low confidence (<50%)
- `request_more_info(question)` - Ambiguous input

**Example Classifications**:
- "meal 20 dollar" → Add $20 to meals jar (95% confident)
- "50k" → Ask confirmation for meals jar (70% confident - usual pattern)
- "crypto investment" → No suitable jar (suggest creating investment jar)

**Mock Data**: Sample jars (rent, groceries, utilities, gas, meals, transport) with keywords and transaction history

---

### Fee Manager Component (fee_test/)
**Purpose**: LLM-powered agent that analyzes natural language descriptions of recurring fees and creates structured schedule patterns

**Key Features**:
- **Gemini 2.5 Flash Lite** analyzes natural language fee descriptions
- **LangChain tool calling** for fee management operations
- **Pattern recognition** for daily, weekly, monthly, bi-weekly schedules
- **Confidence-based responses** (0-100% confidence scores)
- **Multi-language support** (English and Vietnamese)
- **Schedule calculation** with next occurrence dates

**Pattern Types Supported**:
- **Daily**: "5 dollar daily for coffee" → Empty pattern_details {}
- **Weekly**: "25k từ thứ 2 đến thứ 6" → {"days": [1,2,3,4,5]} (Mon-Fri)
- **Monthly**: "50 dollar every 15th" → {"date": 15}
- **Bi-weekly**: "every other Monday" → {"day": 1, "start_date": "2024-02-19"}

**LLM Tools Available**:
- `create_recurring_fee()` - Create new recurring fees with pattern validation
- `adjust_recurring_fee()` - Modify existing fees (amount, schedule, jar)
- `delete_recurring_fee()` - Deactivate fees with reason tracking
- `list_recurring_fees()` - Show active fees with filtering
- `request_clarification()` - Ask for clarification when input unclear

**Data Structure**: RecurringFee class with name, amount, pattern_type, pattern_details, target_jar, next_occurrence

**Example**: "phí đi lại hằng tuần 25k từ thứ 2 đến thứ 6" → Weekly transport fee $25, Mon-Fri pattern

---

### Jar Manager Component (jar_test/)
**Purpose**: Comprehensive multi-jar manager that implements T. Harv Eker's official 6-jar money management system with advanced CRUD operations

**Key Features**:
- **T. Harv Eker's 6-jar system**: Official percentages - necessities (55%), long_term_savings (10%), play (10%), education (10%), financial_freedom (10%), give (5%)
- **Multi-jar operations**: Create, update, delete multiple jars simultaneously
- **Automatic rebalancing**: Maintains 100% allocation across all jars
- **Decimal percentage system**: 0.0-1.0 format (0.15 = 15%)
- **Sample income**: $5,000 for realistic budget calculations
- **Atomic operations**: All succeed or all fail with rollback capability

**LLM Tools Available**:
- `create_jar()` - Create one or multiple jars with automatic rebalancing
- `update_jar()` - Update jar properties with percentage adjustments  
- `delete_jar()` - Delete jars with automatic redistribution
- `list_jars()` - Display all jars with status
- `request_clarification()` - Ask for clarification when needed

**Multi-Jar Examples**:
- Single: "Create vacation jar with 15%" → Create one jar, rebalance others
- Multi: "Create vacation and emergency jars with 10% each" → Create two jars, rebalance
- Batch update: "Update vacation to 8% and emergency to 12%" → Update both, rebalance

**Rebalancing Logic**: When jars added/removed/updated, system automatically scales other jars proportionally to maintain 100% total allocation

**Data Structure**: Simple dict with name, description, percent (0.0-1.0), current_percent

---

### Knowledge Base Component (knowledge_test/)
**Purpose**: Financial education and app documentation assistant using ReAct (Reason-Act-Observe) framework

**Key Features**:
- **ReAct framework**: Continuous reasoning cycles until complete formatted answer
- **Dual knowledge sources**: Online search (DuckDuckGo) + hardcoded app documentation
- **Smart question analysis**: Automatically categorizes questions as financial, app-related, or mixed
- **Tool coordination**: Intelligently uses multiple tools for comprehensive answers
- **Educational focus**: Prioritizes teaching concepts over providing financial advice
- **LangChain tool binding**: 3 specialized knowledge tools bound to LLM

**Tools Available**:
- `search_online(query, description)` - DuckDuckGo search for financial concepts
- `get_application_information(description)` - Complete app feature documentation  
- `respond(answer, description)` - Mandatory final formatted response (ends ReAct loop)

**App Documentation Coverage**:
- **Jar System**: Virtual budget jars for spending categories
- **Budget Suggestions**: AI-powered budget recommendations
- **Auto Categorization**: Smart transaction sorting (Starbucks → Dining)
- **Transaction Search**: Natural language search with Vietnamese support
- **Subscription Tracking**: Recurring payment management

**ReAct Flow**: User Query → Think → Act (gather info) → Observe → Think → Act (respond) → Final Answer

**Examples**:
- Financial: "What is compound interest?" → search_online → respond with explanation
- App: "How does jar system work?" → get_application_information → respond with details
- Mixed: "What is budgeting and how does app help?" → search + app info → combined response

---

### Budget Advisor Component (plan_test/)
**Purpose**: Financial planning consultant and advisory expert using ReAct framework with multi-agent coordination

**Key Features**:
- **ReAct advisory framework**: Continuous reasoning cycles for comprehensive financial guidance
- **Multi-agent coordination**: Integrates with transaction fetcher and jar manager for data
- **Integrated plan management**: Creates/adjusts budget plans with detailed jar proposals in single operations
- **Interactive memory system**: Remembers conversation history for natural follow-up discussions
- **Vietnamese language support**: Handles financial planning queries with cultural context
- **Advisory expertise**: Provides personalized recommendations based on real financial data

**Tools Available**:
- `transaction_fetcher(user_query, description)` - Get spending data for analysis
- `get_jar(jar_name, description)` - Current jar allocations and balances  
- `get_plan(status, description)` - Retrieve existing budget plans
- `create_plan(name, description, status, jar_propose_adjust_details)` - Create plans with jar proposals
- `adjust_plan(name, description, status, jar_propose_adjust_details)` - Modify plans with jar adjustments
- `respond(summary, advice, question_ask_user)` - Final advisory response (ends ReAct)

**Data Model**: Comprehensive budget plan structure with goals, recommended jars, monthly targets, milestones, progress tracking

**Workflow Examples**:
- Financial advice: "I'm overspending on meals" → get data → analyze → provide recommendations
- Goal planning: "Save $15k for Japan in 3 months" → create plan with detailed jar adjustments
- Plan updates: "Extend vacation timeline" → adjust plan with revised jar recommendations

**Memory System**: Stores conversation history for natural follow-up discussions

---

### Transaction Fetcher Component (transaction_fetcher/)
**Purpose**: Data-focused transaction retrieval agent using intelligent tool selection with Vietnamese language support

**Key Features**:
- **Smart tool selection**: LLM automatically chooses appropriate tools based on query analysis
- **Complexity detection**: Simple (1-2 filters) vs complex (3+ filters) queries
- **Vietnamese query support**: Handles Vietnamese financial queries with automatic translation
- **Multi-tool combination**: Complex queries requiring multiple data sources in single pass
- **LLM-provided descriptions**: Each tool call includes intent description for clarity
- **Structured data return**: Returns data with descriptions for user and agent understanding
- **Service integration**: Provides data to other agents (budget_advisor, jar_manager, etc.)

**Tools Available**:
- `get_jar_transactions(jar_name, limit, description)` - Transactions for specific jar/category
- `get_time_period_transactions(jar_name, start_date, end_date, limit, description)` - Time-based filtering
- `get_amount_range_transactions(jar_name, min_amount, max_amount, limit, description)` - Amount-based filtering
- `get_hour_range_transactions(jar_name, start_hour, end_hour, limit, description)` - Hour-based behavioral analysis
- `get_source_transactions(jar_name, source_type, limit, description)` - Source-based filtering (vpbank_api, manual_input, etc.)
- `get_complex_transaction(...)` - Multi-dimensional filtering for complex queries (3+ filters)

**Data Structure**: Transaction with amount, jar, description, date, time, source

**Vietnamese Support Examples**:
- "cho tôi xem thông tin ăn trưa (11h sáng →2h chiều) dưới 20 đô" → Complex tool with meals jar, 11-14 hours, max $20
- "ăn sáng từ 6 giờ đến 10 giờ sáng dưới 15 đô" → Breakfast 6-10am under $15

**Architecture**: Single-pass processing with LangChain tool binding for intelligent complexity detection

---

## Complete System Overview

## Components Read So Far:
✅ **orchestrator_test** - Central routing system
✅ **classifier_test** - Transaction classification with confidence scoring
✅ **fee_test** - Recurring fee management with pattern recognition
✅ **jar_test** - Multi-jar budget management with auto-rebalancing
✅ **knowledge_test** - Financial education with ReAct framework
✅ **plan_test** - Budget advisory and financial planning with memory
✅ **transaction_fetcher** - Intelligent transaction data retrieval with Vietnamese support

## FULLY READ - ALL COMPONENTS COMPLETE! 🎉

---

## 💡 Final System Understanding

### What This Chatbot System Is:
This is a **VPBank Hackathon AI Financial Coach** implementing a **comprehensive 6-jar budgeting methodology** for Vietnamese users. It's not a complete backend system but rather a **testing lab for AI agent prompts** focusing on **orchestrator routing quality**.

### The Complete Architecture:

#### 🎯 **Central Orchestrator** (`orchestrator_test/`)
- **Brain of the system** - routes user requests to appropriate specialist agents
- **3 routing types**: Single worker, multi-worker, request decomposition
- **5 specialist workers**: jar_manager, transaction_classifier, budget_advisor, knowledge_base, direct_response
- **Testing focus**: "Can my orchestrator prompts correctly analyze and route user requests?"

#### 🔄 **Worker Agent Ecosystem**:

1. **Transaction Classifier** - Intelligently categorizes spending into jars with confidence scoring
2. **Fee Manager** - Handles recurring payments with complex schedule patterns
3. **Jar Manager** - Implements T. Harv Eker's 6-jar system with automatic rebalancing 
4. **Knowledge Base** - Financial education using ReAct framework + app documentation
5. **Budget Advisor** - Comprehensive financial planning with memory and jar proposals
6. **Transaction Fetcher** - Intelligent data retrieval with Vietnamese language support

#### 🏺 **6-Jar Budget Foundation**:
- **Necessities (55%)**: Essential expenses
- **Long-Term Savings (10%)**: Future financial security  
- **Financial Freedom (10%)**: Investment/passive income
- **Education (10%)**: Learning and skill development
- **Play (10%)**: Entertainment and enjoyment
- **Give (5%)**: Charity and helping others

### Key Technologies:
- **Gemini 2.5 Flash Lite** for all LLM processing
- **LangChain tool binding** for structured agent interactions
- **ReAct framework** for complex reasoning and decision making
- **Multi-language support** (English + Vietnamese)
- **Confidence-based scoring** throughout the system

### User Journey Examples:

#### Simple Request:
User: "Add vacation jar 10%" 
→ Orchestrator → Single worker routing → Jar Manager → Create jar with rebalancing

#### Complex Request:
User: "I spent $100 on groceries and want to add a vacation jar with 15%"
→ Orchestrator → Multi-worker routing → Transaction Classifier + Jar Manager → Execute both actions

#### Vietnamese Request:
User: "tôi muốn tiết kiệm tiền cho kỳ nghỉ" 
→ Orchestrator → Budget Advisor → Vietnamese query processing → Financial planning with jar proposals

#### Educational Request:
User: "What is compound interest and how does this app help?"
→ Orchestrator → Knowledge Base → ReAct cycle → Search online + app documentation → Combined educational response

### System Philosophy:
- **Extreme simplicity** over complex engineering
- **Interactive testing** preferred over hardcoded scenarios  
- **Prompt quality validation** as the primary goal
- **Mock data and responses** for development speed
- **No over-engineering** - this is a testing lab, not production code

### The Big Picture:
This system demonstrates how modern LLM-powered agents can work together to provide comprehensive financial coaching. Each component is designed to be **testable**, **simple**, and **focused** on its specific domain while the orchestrator ensures users get routed to the right expertise for their needs.

The ultimate goal: **Test if AI agents can understand, route, and respond to complex financial requests as effectively as a human financial coach would.**
