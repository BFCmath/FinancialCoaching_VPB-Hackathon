# Knowledge Base Agent

## Overview

The Knowledge Agent serves as the AI-powered information backbone of our financial coaching system. Using an advanced implementation of the **ReAct (Reason + Act)** framework, it provides comprehensive answers about financial concepts, application features, and personalized financial advice. 

The agent's sophisticated reasoning process allows it to:
1. Break down complex queries into sub-components
2. Gather information from multiple sources
3. Synthesize complete, accurate responses
4. Handle follow-up questions and clarifications

## Core Features

### 1. Advanced ReAct Framework
- **Multi-step Reasoning**: Breaks down complex queries into logical steps
- **Dynamic Tool Selection**: Intelligently chooses appropriate information sources
- **Result Analysis**: Evaluates information quality and completeness
- **Answer Synthesis**: Combines multiple sources into coherent responses

### 2. Information Sources
- **Live Financial Data**: Real-time market and financial information
- **Internal Documentation**: App features and capabilities
- **Knowledge Base**: Core financial concepts and principles
- **User Context**: History-aware responses when relevant

### 3. Response Quality
- **Comprehensive Answers**: Complete explanations with examples
- **Source Integration**: Combines multiple reliable sources
- **Clarity Control**: User-friendly language and formatting
- **Vietnamese Support**: Bilingual capability for all features

### 4. System Integration
- **Conversation Management**: Tracks context and history
- **Service Layer Integration**: Direct access to app features
- **Tool Result Caching**: Optimizes response times
- **Error Recovery**: Graceful handling of missing information

## ReAct Framework Implementation

The agent implements a sophisticated ReAct cycle:

## Implementation Details

### ReAct Loop Components

The agent's core ReAct cycle is implemented in `main.py`:

1. **Query Analysis**
   - Parses user input
   - Identifies key concepts
   - Determines required information

2. **Tool Selection**
   - Chooses appropriate information sources
   - Plans multi-step information gathering
   - Optimizes tool call sequence

3. **Result Processing**
   - Validates tool outputs
   - Combines multiple results
   - Ensures information completeness

4. **Answer Generation**
   - Synthesizes final response
   - Formats for readability
   - Adds relevant examples

### Code Organization

The agent's functionality is spread across several key files:

- `main.py`: Core ReAct implementation with the conversation loop
- `tools.py`: Information gathering and processing tools
- `prompt.py`: LLM guidance for ReAct reasoning
- `interface.py`: Clean orchestrator integration interface
- `config.py`: Environmental configuration management
- `test.py`: Interactive testing interface
- `env.example`: Configuration template

## Configuration

Configure the agent through environment variables in `/agents/knowledge/.env`:

```env
# Gemini API Key (required)
GOOGLE_API_KEY=your_gemini_api_key_here

# Model Configuration
MODEL_NAME=gemini-2.5-flash-lite-preview-06-17
LLM_TEMPERATURE=0.1

# ReAct Framework Settings
DEBUG_MODE=false
MAX_REACT_ITERATIONS=5
```

## Usage Guide

### Direct Integration

Import and use the agent in your code:

```python
from agents.knowledge.interface import KnowledgeAgent

# Create agent instance
knowledge_agent = KnowledgeAgent()

# Get financial knowledge
result = knowledge_agent.process(
    task="What's the best way to start investing?"
)
print(result)

# Get app feature information
result = knowledge_agent.process(
    task="How does the jar system work?"
)
print(result)
```

### Interactive Testing

Test the agent through the command line interface:

1. Set up the environment:

```bash
cd agent-testing-lab/full_multi_agent
cp agents/knowledge/env.example agents/knowledge/.env
# Edit .env with your API key
```

1. Run the test interface:

```bash
python -m agents.knowledge.test
```

1. Try example queries:

```text
> What is compound interest?
> How do I set up the 6-jar system?
> What's a good savings strategy?
> How do I track my recurring fees?
```

## Error Recovery

The agent includes sophisticated error handling:

1. **Missing Information**
   - Attempts alternative sources
   - Requests clarification if needed
   - Provides partial information with disclaimers

2. **Tool Failures**
   - Graceful degradation
   - Alternative tool selection
   - Clear error reporting

3. **Reasoning Limits**
   - Maximum iteration protection
   - Clear incomplete status
   - Suggestion for query simplification

## Performance Optimization

The agent implements several optimizations:

1. **Response Time**
   - Tool result caching
   - Optimized tool selection
   - Early exit on complete answers

2. **Memory Usage**
   - Efficient conversation history
   - Selective context retention
   - Resource cleanup

3. **Quality Control**
   - Multi-source validation
   - Confidence scoring
   - Answer completeness checks

---
This README details the Knowledge Agent's advanced ReAct framework implementation and capabilities.
