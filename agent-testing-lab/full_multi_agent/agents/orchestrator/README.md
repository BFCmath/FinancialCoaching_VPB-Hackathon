# Orchestrator

## Overview

The Orchestrator is the central router for the multi-agent system. It is stateful (uses last 10 conversation turns), classifies intents to route to agents via tool calls, handles direct answers for greetings/irrelevant queries, manages follow-up locking with agent-specific history, and supports multi-intent queries by calling multiple tools (agents) in parallel. The LLM decides whether to respond directly or call tools.

## Core Features

- **Stateful**: Uses last 10 turns from conversation_history for context in the prompt.
- **Intent Classification via LLM**: LLM analyzes query and history to decide direct response or tool calls.
- **Direct Answers**: For greetings/irrelevant, responds without tools.
- **Follow-up Locking**: If locked, routes to locked agent with filtered history (turns involving that agent).
- **Tool Calling for Routing**: Tools map to agents; LLM can call multiple for multi-intent.
- **Single Flow**: LLM invoked once; if tools called, execute and synthesize (join responses).
- **Bilingual Support**: Can respond in Vietnamese.

## Execution Flow

1. Check lock: If active, route to locked agent with filtered history, release if no follow-up.
2. Limit history to 10 turns.
3. Build prompt with history, query, tools.
4. Invoke LLM with tools bound.
5. If no tool calls: Direct response from LLM content, log turn.
6. If tool calls: Execute each (agent route), collect responses, synthesize (join), log with tool calls.
7. Handle follow-up: If any requires it, keep lock.

## Domains (from Agent READMEs)

- **Classifier**: Transaction categorization into jars.
- **Fee**: Manage recurring fees/subscriptions (create, update, delete, list).
- **Jar**: CRUD for budget jars, rebalancing.
- **Knowledge**: Financial concepts, app features, general advice.
- **Plan**: Financial planning, goals, savings plans, jar adjustments.
- **Fetcher**: Retrieve transaction history with filters.

## Components

- `main.py`: Core logic for lock handling, LLM invoke, tool execution, synthesis.
- `prompt.py`: Prompt for LLM with tools and rules.
- `tool.py`: Tools that call agents.
- `config.py`: Env config.
- `test.py`: Interactive testing.

## Configuration

`.env` in `agents/orchestrator/`:
