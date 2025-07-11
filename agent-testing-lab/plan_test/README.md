# Budget Advisor Agent

A sophisticated financial planning consultant powered by LLM with ReAct framework, providing personalized budget advice and jar allocation recommendations.

## 🎯 Overview

The Budget Advisor Agent is a **financial consultant** that analyzes spending patterns, creates budget plans, and proposes jar adjustments through intelligent conversation. It uses a ReAct (Reason-Act-Observe) framework with LangChain tool binding to provide comprehensive financial guidance.

### Key Features

- **💡 Financial Advisory**: Personalized budget advice based on spending analysis
- **📋 Plan Management**: Create and adjust comprehensive budget plans  
- **🏺 Jar Integration**: T. Harv Eker 6-jar system integration with detailed proposals
- **🤖 ReAct Framework**: Intelligent reasoning with 6 specialized tools
- **💭 Memory System**: Conversational memory for interactive sessions
- **🌍 Vietnamese Support**: Native Vietnamese language financial planning
- **🔗 Multi-Agent Integration**: Coordinates with transaction fetcher and jar manager

## 🛠️ Architecture

### Core Tools (6 Total)

1. **`transaction_fetcher`** - Get spending transaction data
2. **`get_jar`** - Retrieve budget jar status and allocations 
3. **`get_plan`** - Get existing budget plans by status
4. **`create_plan`** - Create new budget plans with jar proposals
5. **`adjust_plan`** - Modify existing plans with jar adjustments  
6. **`respond`** - Provide final advisory response with optional follow-up questions

### Workflow Pattern
```
User Request → Gather Data → Analyze → Create/Adjust Plans → Provide Advice
```

### ReAct Framework
- **Max 6 iterations** for comprehensive analysis
- **LangChain tool binding** with Gemini LLM
- **Conversation memory** for interactive sessions
- **Vietnamese language** support throughout

## 🚀 Quick Start

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Add your GOOGLE_API_KEY to .env

# Run interactive testing
python test.py
```

### Basic Usage
```python
from main import get_budget_advice

# Get financial advice
advice = get_budget_advice("I want to save $15,000 for a Japan trip in 3 months")
print(advice)
```

### Interactive Mode
```bash
# Direct interactive mode
python test.py interactive

# Or use menu system
python test.py
# Select option 1: Interactive Testing
```

## 📊 Example Interactions

### Plan Creation with Jar Proposals
```
User: "tôi muốn đi nhật, 15000 đô, trong 3 tháng tới"

Agent Process:
1. get_jar() → Check current allocations
2. create_plan() with detailed jar_propose_adjust_details
3. respond() with summary and recommendations

Response:
- Plan: "Japan Trip" created
- Jar Proposal: "Create Japan Trip jar with $5,000/month..."
- Advice: Specific saving strategy and jar rebalancing
```

### Spending Analysis
```
User: "Analyze my spending and give advice"

Agent Process:  
1. transaction_fetcher() → Get spending data
2. get_jar() → Current jar status
3. respond() with analysis and recommendations
```

### Follow-up Questions
```
Agent: "What's your monthly income so I can calculate precise jar allocations?"
User: "$8,000 per month"
Agent: [Continues with specific percentage calculations]
```

## 🔧 Configuration

### Environment Variables
```env
GOOGLE_API_KEY=your_gemini_api_key
MODEL_NAME=gemini-2.5-flash-lite-preview-06-17
LLM_TEMPERATURE=0.1
MAX_REACT_ITERATIONS=6
ENABLE_MEMORY=true
MAX_MEMORY_TURNS=10
DEBUG_MODE=false
```

### Key Settings
- **ReAct Iterations**: Max 6 loops for comprehensive analysis
- **Memory**: Conversational history for interactive sessions
- **Temperature**: 0.1 for consistent financial advice
- **Debug Mode**: Disabled fallbacks for error visibility

## 📁 Project Structure

```
plan_test/
├── main.py              # ReAct framework implementation
├── tools.py             # 6 advisory tools
├── prompt.py            # Agent prompts and instructions  
├── config.py            # Configuration management
├── test.py              # Comprehensive testing framework
├── env.example          # Environment template
├── cursor_docs/         # AI assistant documentation
└── tool_agent/          # Integration with other agents
    ├── data/            # Transaction fetcher integration
    └── jar/             # Jar manager integration
```

## 🧪 Testing

### Test Categories
- **Interactive Testing**: Real-time conversation with memory
- **Predefined Scenarios**: Budget planning test cases
- **Tool Validation**: Individual tool functionality
- **ReAct Simulation**: Framework workflow testing

### Run Tests
```bash
# Full test suite
python test.py

# Individual test modes
python test.py
# 1. Interactive Testing (with memory)
# 2. Predefined Test Scenarios  
# 3. Tool Validation
# 4. ReAct Framework Simulation
```

## 💡 Advanced Features

### Memory System
- **Conversation History**: Remembers previous interactions
- **Context Awareness**: References past plans and advice
- **Follow-up Support**: Natural conversation flow
- **Interactive Only**: Memory disabled for non-interactive modes

### Jar Proposal Integration
- **Detailed Recommendations**: Comprehensive jar adjustment proposals
- **Impact Analysis**: How changes affect overall budget
- **Percentage Calculations**: Precise allocation recommendations
- **Rebalancing Strategy**: Complete jar system optimization

### Multi-Agent Coordination
- **Transaction Fetcher**: Real spending data analysis
- **Jar Manager**: Current allocation status and management
- **Plan Storage**: Persistent budget plan management

## 🌍 Vietnamese Language Support

Native Vietnamese financial planning queries supported:
- "tôi muốn tiết kiệm tiền cho kỳ nghỉ"
- "phân tích chi tiêu và đưa ra lời khuyên"  
- "tạo kế hoạch ngân sách cho chuyến đi"
- "điều chỉnh kế hoạch tiết kiệm"

## 🔍 Debugging

- **No Error Fallbacks**: All try/catch removed for visibility
- **Direct Error Messages**: Full Python tracebacks displayed
- **Tool Execution Logging**: Detailed tool call information
- **ReAct Iteration Tracking**: Debug mode shows reasoning steps

## 📚 Documentation

- **`cursor_docs/for_ai.md`**: AI assistant quick reference
- **`cursor_docs/agent_detail.md`**: Detailed specifications
- **`cursor_docs/detail_context.md`**: Implementation context

## 🔗 Integration

Compatible with VPB Hackathon agent ecosystem:
- Transaction Fetcher Agent
- Jar Manager Agent (T. Harv Eker 6-jar system)
- Fee Manager Agent
- Orchestrator Agent

---

**Built for VPB Hackathon** - Intelligent financial advisory through conversational AI

