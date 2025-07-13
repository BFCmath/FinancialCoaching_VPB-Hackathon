# Multi-Worker Orchestrator Test Lab - Detailed Context

## 🏗️ Project Overview

This is a **VPBank Hackathon project** for an **AI Financial Coach** system that implements a **6-jar budgeting methodology** for Vietnamese users. The focus is specifically on **testing orchestrator prompt quality**, not building a full backend system.

### Core Purpose
**Test if orchestrator prompts can correctly:**
- Analyze complex user requests
- Decompose them into sub-tasks  
- Route to multiple specific workers with appropriate task descriptions

### Key Philosophy
- **Focus ONLY on prompt testing** - no over-engineering
- **Interactive testing preferred** over hardcoded scenarios
- **Real-time prompt validation** from CLI interface
- **Simplicity over complexity** - minimal viable testing system

## 📊 6-Jar Budgeting System Context

The AI Financial Coach implements the 6-jar money management system:
- **Necessities (55%)** - Essential expenses
- **Long-Term Savings (10%)** - Future financial security
- **Financial Freedom (10%)** - Investment/passive income
- **Education (10%)** - Learning and skill development  
- **Play (10%)** - Entertainment and enjoyment
- **Give (5%)** - Charity and helping others

## 🔄 Project Evolution History

### Phase 1: Over-Engineered System (Initial State)
**Problems identified:**
- Complex conversation state management (INITIAL, ROUTING, GATHERING_INFO, PENDING_CONFIRMATION, EXECUTING, COMPLETED)
- Multi-step conversation workflows
- Business function implementations (mock jar operations, transactions)
- Confirmation logic with thresholds
- Complex configuration classes (LLMConfig, TestingConfig, OrchestatorConfig, AppConfig)
- Multi-provider LLM support (OpenAI, Anthropic, Local, Gemini)
- Advanced features like session management, auto-save, performance monitoring
- 659-line main.py with excessive complexity

### Phase 2: First Simplification 
**Changes made:**
- Focused on Gemini only (removed multi-provider support)
- Simplified configuration to single provider
- Removed unused environment variables
- Maintained tool system but simplified implementation

### Phase 3: Radical Simplification (User Request)
**Key realization:** "This is for test orchestrator, not for backend"
**Major simplifications:**
- Removed all business logic implementations
- Eliminated conversation stages and state management
- Focused purely on routing decision testing
- Reduced line counts by 60-85% across all files

### Phase 4: Multi-Worker Focus (Final State)
**User's refined requirement:**
- **Input:** Single prompt from user
- **Logic:** Analyze, decompose and send correct prompts using Gemini  
- **Output:** Many prompts to specific workers

**Final architecture implemented:**
- Single worker routing for simple requests
- Multi-worker routing for complex requests
- Request decomposition for unclear requests
- Interactive CLI testing interface
- Mock mode for API-free testing

## 🎯 Current System Architecture

### Core Workflow
```
User Input → Gemini Analysis → Routing Decision → Worker Assignment(s)
```

### Routing Types

#### 1. Single Worker Routing
```
Input: "Add vacation jar 10%"
Output: route_to_jar_manager(task_description="add vacation jar with 10% allocation")
```

#### 2. Multi-Worker Routing  
```
Input: "I spent $100 on groceries and want to add a vacation jar with 15%"
Output: route_to_multiple_workers(tasks=[
    {"worker": "transaction_classifier", "task_description": "log $100 grocery transaction"},
    {"worker": "jar", "task_description": "add vacation jar with 15% allocation"}
])
```

#### 3. Request Decomposition
```
Input: "Help me with my finances - I spent money on dining and need a savings plan"
Output: decompose_complex_request(
    user_request="...",
    identified_tasks=[
        {"task": "log dining expense", "worker": "transaction_classifier", "details": "..."},
        {"task": "create savings plan", "worker": "budget", "details": "..."}
    ]
)
```

### Available Workers
1. **jar_manager** - Budget jar operations (create, update, delete, view jars)
2. **transaction_classifier** - Logging and classifying transactions  
3. **budget_advisor** - Financial planning, savings goals, spending analysis
4. **knowledge_base** - Financial education and answering questions
5. **direct_response** - Greetings, clarifications, simple responses

## 📁 File Structure & Line Counts

| File | Lines | Purpose | Key Features |
|------|-------|---------|--------------|
| `config.py` | 58 | Minimal configuration | API key, model settings, debug/mock modes |
| `tools.py` | 95 | Routing tools | 7 tools: 5 single-worker + 2 multi-worker |
| `prompt.py` | 142 | Routing prompts | Multi-worker routing logic + examples |
| `main.py` | 146 | Core orchestrator | Analysis, routing, display logic |
| `test.py` | 172 | Interactive testing | CLI interface with commands |
| `requirements.txt` | 9 | Dependencies | LangChain, Gemini, dotenv, colorama |
| `env.example` | 9 | Environment template | Essential variables only |

## ⚙️ Configuration Details

### Environment Variables
```bash
# Required (unless mock mode)
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional
MODEL_NAME=gemini-2.5-flash-lite-preview-06-17
LLM_TEMPERATURE=0.1
DEBUG_MODE=false
MOCK_RESPONSES=false
```

### Model Configuration
- **Model:** `gemini-2.5-flash-lite-preview-06-17` (fixed, do not change)
- **Temperature:** 0.1 (low for consistent routing)
- **Provider:** Google Gemini only
- **Tools:** LangChain tool calling integration

## 🧪 Testing Approach

### Interactive Testing Philosophy
- **Real-time prompt testing** via CLI
- **No hardcoded test scenarios** (user explicitly removed them)
- **Developer-driven testing** through interactive commands
- **Mock mode support** for API-free testing

### Testing Commands
```bash
# Interactive testing
python test.py

# Quick demo (mock mode)
MOCK_RESPONSES=true python main.py

# API testing 
python test.py  # (with GOOGLE_API_KEY set)
```

### Mock Response System
- Pattern-based routing for testing without API calls
- Simulates multi-worker, single-worker, and decomposition responses
- Keyword matching for different request types

## 🔧 Technical Implementation

### Tool System
**Single Worker Tools:**
- `route_to_jar_manager(task_description)`
- `route_to_transaction_classifier(task_description)`  
- `route_to_budget_advisor(task_description)`
- `route_to_knowledge_base(query)`
- `provide_direct_response(response_text)`

**Multi-Worker Tools:**
- `route_to_multiple_workers(tasks)` - Routes to multiple workers
- `decompose_complex_request(user_request, identified_tasks)` - Breaks down unclear requests

### Prompt Engineering
- **Analysis process:** Count tasks → Identify workers → Check complexity
- **Routing rules:** 1 task = single worker, 2+ tasks = multi-worker, unclear = decomposition
- **Examples provided:** Simple, complex, and decomposition scenarios
- **Clear instructions:** Always call exactly ONE tool per response

### Error Handling
- Graceful API failures with fallback to mock responses
- Missing API key detection with helpful instructions
- Debug mode for development troubleshooting

## 📋 User Requirements & Constraints

### Explicit User Preferences
1. **"This is for test orchestrator, not for backend"** - Focus only on prompt testing
2. **"Remove redundant over-engineering"** - Radical simplification required
3. **"Only focus to test orchestrator prompt only"** - No business logic needed
4. **"Test if prompt is good enough for agent to route"** - Core validation goal
5. **"Interactive testing preferred"** - CLI over hardcoded scenarios
6. **"Use real prompt from interactive mode"** - No hardcoded test cases

### Technical Constraints
- **Gemini only** - No multi-provider support needed
- **LangChain integration** - Tool calling system required
- **Mock mode essential** - Must work without API for testing
- **Simple configuration** - Minimal environment variables
- **Windows PowerShell** - User's development environment

## 🎯 Success Criteria

### Prompt Quality Validation
The system successfully tests if prompts can:
1. **Route simple requests** to appropriate single workers
2. **Decompose complex requests** into multiple worker tasks  
3. **Identify unclear requests** that need decomposition
4. **Generate appropriate task descriptions** for each worker
5. **Make logical routing decisions** based on user intent

### Developer Experience
- **Easy setup** with minimal configuration
- **Interactive testing** with immediate feedback
- **Clear output format** showing routing decisions
- **Debug capabilities** for prompt improvement
- **Mock mode** for API-free development

## 🚨 Important Notes

### Critical Design Decisions
- **No conversation state** - Each request is independent
- **No confirmation workflows** - Pure routing testing only
- **No business function execution** - Mock responses only
- **No persistent storage** - Stateless operation
- **No authentication** - Development tool only

### Future Considerations
- This is a **testing lab**, not production code
- **Prompt iteration** is the primary use case
- **Quick validation cycles** are prioritized over features
- **Simplicity maintenance** is crucial for effectiveness

### User's Vision
The goal is to create a **minimal, focused tool** that answers one question: 
**"Can my orchestrator prompts correctly analyze and route user requests to multiple workers?"**

Everything else is considered over-engineering and should be avoided. 