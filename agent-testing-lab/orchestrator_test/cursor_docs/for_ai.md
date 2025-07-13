# AI Assistant Guide - Multi-Worker Orchestrator Test Lab

## 🤖 Quick Start for AI Assistants

This is a **prompt testing lab** for a multi-worker orchestrator system. Your job is to help users test and improve orchestrator prompts that route requests to multiple workers.

### Core Understanding
- **NOT a backend system** - it's a testing tool
- **Focus:** Test if prompts can decompose complex requests and route to multiple workers
- **User philosophy:** Extreme simplicity, no over-engineering, interactive testing only

## 🎯 Primary Use Cases

### 1. Prompt Testing
Help users test orchestrator prompts by:
- Running interactive tests via `python test.py`
- Analyzing routing decisions for different inputs
- Identifying prompt improvement opportunities

### 2. Prompt Improvement  
Help users improve prompts by:
- Editing `prompt.py` ROUTING_PROMPT section
- Adding/modifying routing examples
- Adjusting analysis process instructions

### 3. Tool Modification
Help users modify routing tools by:
- Editing tools in `tools.py`
- Adding new worker types if needed
- Modifying tool descriptions for better LLM understanding

## 📁 File Guide for AI Assistants

### `config.py` (58 lines) - MINIMAL CONFIGURATION
```python
# Only touch for:
# - API key issues
# - Model parameter adjustments
# - Debug/mock mode changes
# NEVER add complex configuration classes!
```

### `tools.py` (95 lines) - ROUTING TOOLS
```python
# 7 tools total:
# - 5 single-worker routing tools
# - 2 multi-worker tools (route_to_multiple_workers, decompose_complex_request)
# Modify tool descriptions to improve LLM understanding
```

### `prompt.py` (142 lines) - CORE PROMPTS
```python
# MOST IMPORTANT FILE for prompt testing
# Contains ROUTING_PROMPT with:
# - Routing rules and analysis process
# - Examples for simple/complex/decomposition scenarios
# - Clear instructions for tool calling
# NOTE: TEST_SCENARIOS are commented out (user preference)
```

### `main.py` (146 lines) - ORCHESTRATOR LOGIC
```python
# Core orchestrator implementation
# Handles: analysis, routing, display
# Mock response system for API-free testing
# AVOID adding complex logic here!
```

### `test.py` (172 lines) - INTERACTIVE TESTING
```python
# CLI interface for testing
# Commands: help, examples, multi, simple, scenarios
# Interactive prompt testing (user's preferred method)
```

## 🔧 How to Help Users

### When User Wants to Test Prompts
1. **Run interactive testing:** `python test.py`
2. **Use mock mode if no API:** `MOCK_RESPONSES=true python test.py`
3. **Focus on routing quality** - are the right workers selected?
4. **Check task descriptions** - are they clear and actionable?

### When User Wants to Improve Prompts
1. **Edit `prompt.py`** - Focus on ROUTING_PROMPT section
2. **Add more examples** in the prompt for edge cases
3. **Clarify routing rules** if LLM makes wrong decisions
4. **Test immediately** after changes using CLI

### When User Reports Issues
1. **Check configuration** - API key, mock mode settings
2. **Verify model** - Should be `gemini-2.5-flash-lite-preview-06-17`
3. **Test in mock mode** first to isolate API issues
4. **Use debug mode** - Set `DEBUG_MODE=true`

## 🚨 Critical Do's and Don'ts

### ✅ DO
- **Keep everything simple** - this is the user's top priority
- **Focus on prompt testing** - the core purpose
- **Use interactive testing** - user's preferred method
- **Maintain minimal configuration** - only essential settings
- **Test in mock mode** when possible
- **Edit prompts to improve routing** quality

### ❌ DON'T  
- **Add complex business logic** - this is NOT a backend
- **Create conversation state management** - each request is independent  
- **Add confirmation workflows** - pure routing testing only
- **Over-engineer configuration** - user explicitly rejected this
- **Add hardcoded test scenarios** - user removed them for a reason
- **Add multi-provider LLM support** - Gemini only
- **Add persistent storage** - stateless operation preferred
- **Add authentication** - development tool only

## 🔄 Routing Types to Understand

### 1. Single Worker Routing (Simple)
```
Input: "Add vacation jar 10%"
Expected: route_to_jar_manager(task_description="...")
```

### 2. Multi-Worker Routing (Complex)
```
Input: "I spent $100 on groceries and want to add a vacation jar with 15%"
Expected: route_to_multiple_workers(tasks=[
    {"worker": "transaction_classifier", "task_description": "..."},
    {"worker": "jar", "task_description": "..."}
])
```

### 3. Request Decomposition (Unclear)
```
Input: "Help me with my finances - I spent money on dining and need a savings plan"
Expected: decompose_complex_request(user_request="...", identified_tasks=[...])
```

## 🧪 Testing Workflow

### Standard Testing Process
1. User runs `python test.py`
2. User types test input
3. System analyzes and routes
4. User evaluates routing quality
5. User iterates on prompts if needed

### Mock Mode Testing
```bash
# Set environment variable
MOCK_RESPONSES=true python test.py

# Or in PowerShell (user's environment)
$env:MOCK_RESPONSES="true"; python test.py
```

### API Testing
```bash
# Requires GOOGLE_API_KEY in .env
python test.py
```

## 🎯 Success Metrics

Help users evaluate if their prompts work well:

### Good Routing Signs
- **Simple requests** → Single worker routing
- **Complex requests** → Multi-worker routing with appropriate task distribution
- **Unclear requests** → Decomposition with clarification
- **Clear task descriptions** for each worker
- **Logical worker selection** based on request content

### Bad Routing Signs  
- Complex requests routed to single worker
- Simple requests over-complicated with multi-worker
- Unclear or generic task descriptions
- Wrong worker selection for request type
- No tool call generated

## 💡 Common User Requests

### "Test this prompt"
```bash
# Help them run interactive testing
python test.py
# Guide them to type their test inputs
```

### "Improve routing for X type of request"
```python
# Edit prompt.py ROUTING_PROMPT section
# Add specific examples for that request type
# Test immediately after changes
```

### "Add new worker type"
```python
# Add new tool in tools.py
# Update ROUTING_PROMPT in prompt.py
# Add to available workers list
# Test the new routing path
```

### "System not working"
```bash
# Check API key: config.google_api_key
# Try mock mode: MOCK_RESPONSES=true
# Check debug output: DEBUG_MODE=true
# Verify model name in config.py
```

## 🔮 User's Vision

Remember the user's core vision:
> "Test if the prompt is good enough for the agent to route to agent worker or not"

Everything should serve this goal. The user values:
- **Simplicity over features**
- **Interactive testing over automation**  
- **Real prompts over hardcoded scenarios**
- **Focus over scope creep**

## 📋 Quick Reference Commands

```bash
# Interactive testing
python test.py

# Mock mode testing  
MOCK_RESPONSES=true python test.py

# Debug mode
DEBUG_MODE=true python test.py

# Quick demo
MOCK_RESPONSES=true python main.py

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env with your GOOGLE_API_KEY
```

## 🎮 Test Commands in CLI

When users run `python test.py`, they have these commands:
- `help` or `h` - Show help
- `examples` or `e` - Show example inputs
- `multi` or `m` - Test multi-worker examples
- `simple` - Test simple routing examples  
- `quit` or `q` - Exit
- Or just type any prompt to test routing

## 🚀 Final Notes for AI Assistants

This project is a **testing lab**, not production software. The user prioritizes:
1. **Quick iteration cycles** on prompt improvement
2. **Simple, focused functionality** over features
3. **Interactive validation** of routing decisions
4. **Minimal maintenance overhead**

Always keep these priorities in mind when helping users with this project! 