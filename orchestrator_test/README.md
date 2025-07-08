# Multi-Worker Orchestrator Test Lab

A minimal, interactive testing environment for a multi-worker orchestrator system. Test and improve routing prompt quality for financial AI workers.

## 🎯 Purpose

This lab tests whether an orchestrator can:
- **Analyze** user requests accurately
- **Route** to appropriate financial workers
- **Handle** both simple and complex multi-worker scenarios
- **Maintain** consistent tool calling behavior

**Core Philosophy**: Extreme simplicity. Focus only on prompt testing, avoid over-engineering.

---

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Clone and navigate
cd orchestrator_test

# Install dependencies
pip install langchain-google-genai python-dotenv

# Create .env file
cp env.example .env
# Add your GOOGLE_API_KEY to .env
```

### 2. Run Tests
```bash
# Interactive testing (recommended)
python test.py

# Full test suite
python main.py
```

### 3. Example Usage
```
Input: "cơm gà 25k"
Output: 🤖 TRANSACTION_CLASSIFIER - Log chicken rice 25k expense

Input: "add vacation jar 15%"  
Output: 🤖 JAR_MANAGER - Create vacation jar with 15% allocation
```

---

## 🏗️ System Architecture

```
📁 orchestrator_test/
├── 🧠 main.py           # Core orchestrator logic
├── 🛠️ tools.py          # Worker tool definitions  
├── 📝 prompt.py         # Routing prompt (THE THING WE'RE TESTING)
├── ⚙️ config.py         # Simple configuration
├── 🧪 test.py          # Interactive testing interface
├── 📋 env.example      # Environment template
└── 📖 README.md        # This file
```

### Data Flow:
```
User Input → LLM Analysis → Tool Selection → Worker Routing
    ↓            ↓              ↓              ↓
"cơm gà 25k" → Analyze → transaction_classifier → Log expense
```

---

## 🤖 Available Workers

| Worker | Purpose | Example Input |
|--------|---------|---------------|
| **transaction_classifier** | One-time expenses → jars | "cơm gà 25k", "bought groceries $80" |
| **jar_manager** | CRUD jar operations | "add vacation jar", "reduce Save to 2%" |
| **budget_advisor** | Financial planning advice | "save money for parents", "budget plan" |
| **insight_generator** | Spending analysis | "my spending trend", "can I afford trip?" |
| **fee_manager** | Recurring expenses | "$10 monthly Netflix", "$2 daily coffee" |
| **knowledge_base** | Financial education | "what is compound interest?", "explain budgeting" |

### Special Tools:
- **`provide_direct_response`** - Greetings, general conversation
- **`route_to_multiple_workers`** - Complex requests needing multiple workers

---

## 🧪 Testing Scenarios

### Single Worker Tests:
```python
"I spent $25 on lunch"           → transaction_classifier
"create emergency fund"          → jar_manager  
"how to save for vacation?"      → budget_advisor
"my spending patterns"           → insight_generator
"Netflix subscription $10/month" → fee_manager
"what is budgeting?"            → knowledge_base
"hello"                         → provide_direct_response
```

### Multi-Worker Tests:
```python
"I spent $100 on groceries and want to add vacation jar 15%"
→ transaction_classifier + jar_manager

"Log my $50 dinner and help me create a savings plan"  
→ transaction_classifier + budget_advisor
```

---

## ⚙️ Configuration

### Environment Variables (`.env`):
```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional
MODEL_NAME=gemini-2.5-flash-lite-preview-06-17
LLM_TEMPERATURE=0.1
DEBUG_MODE=false
```

### Debug Mode:
```bash
DEBUG_MODE=true python test.py
```
Shows:
- Analysis process
- Tool call count
- Raw LLM responses

---

## 🎯 Key Features

### ✅ **Always Tool Calling**
- LLM never responds directly
- Every request triggers at least one tool
- Consistent routing behavior

### ✅ **Multi-Worker Support** 
- Handle complex requests with multiple tasks
- Parallel worker routing
- JSON-based task decomposition

### ✅ **Vietnamese Support**
- Test with Vietnamese inputs
- Proper Unicode handling
- Cultural context awareness

### ✅ **Error Handling**
- Graceful API failures
- Schema validation
- Fallback mechanisms

---

## 🔧 Development

### Testing New Prompts:
1. Edit `prompt.py` 
2. Run `python test.py`
3. Test various inputs
4. Iterate based on results

### Adding New Workers:
1. Add tool function in `tools.py`
2. Update `ALL_TOOLS` list
3. Add routing guidelines in `prompt.py`
4. Test routing accuracy

### Common Issues:

| Error | Cause | Fix |
|-------|-------|-----|
| "No tool call generated" | LLM responding directly | Strengthen prompt requirements |
| "Invalid argument provided" | Complex parameter types | Use simple `str` parameters |
| "KeyError: 'function'" | Wrong tool call format | Check LangChain integration |

---

## 📊 Expected Results

### Good Routing:
```
================================================================================
📝 USER INPUT: cơm gà 25k
================================================================================
🎯 SINGLE TOOL CALL
──────────────────────────────────────────────────
  1. 🤖 TRANSACTION_CLASSIFIER
     📋 Task: Log chicken rice 25k expense
```

### Multi-Worker Routing:
```
================================================================================
📝 USER INPUT: I spent $100 on groceries and want vacation jar 15%
================================================================================
🔄 PARALLEL TOOL CALLS (2 tools)
──────────────────────────────────────────────────
  1. 🤖 TRANSACTION_CLASSIFIER
     📋 Task: Log $100 grocery expense

  2. 🤖 JAR_MANAGER
     📋 Task: Add vacation jar with 15% allocation
```

---

## 🎨 Design Principles

### **Extreme Simplicity**
- Minimal dependencies
- Clear, focused code
- No unnecessary features

### **Interactive Testing**
- `test.py` for rapid iteration
- Real-time prompt testing
- Quick feedback loops

### **Prompt Quality Focus**
- Test routing accuracy
- Improve decision making
- Validate multi-worker scenarios

---

## 🚦 Getting Started Checklist

- [ ] Install dependencies (`langchain-google-genai`, `python-dotenv`)
- [ ] Set up `.env` with `GOOGLE_API_KEY`
- [ ] Run `python test.py` for interactive testing
- [ ] Try basic inputs: "hello", "cơm gà 25k", "add vacation jar"
- [ ] Test complex inputs with multiple workers
- [ ] Enable debug mode to see detailed analysis
- [ ] Iterate on `prompt.py` to improve routing

---

## 📈 Success Metrics

The orchestrator is working well when:
- ✅ **Consistent tool calling** (never direct responses)
- ✅ **Accurate worker routing** (right tool for the task)
- ✅ **Multi-worker handling** (complex requests decomposed correctly)
- ✅ **Vietnamese support** (proper handling of Vietnamese inputs)
- ✅ **Error resilience** (graceful handling of edge cases)

---

## 🤝 Contributing

This is a **testing lab**, not a production system. Focus on:
1. **Prompt improvements** in `prompt.py`
2. **Test case additions** for edge scenarios
3. **Routing accuracy** enhancements
4. **Documentation** clarity

**Remember**: Keep it simple, keep it focused on testing!

---

*Happy testing! 🧪✨* 