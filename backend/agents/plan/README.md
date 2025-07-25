# Budget Advisor Agent

**Status**: ✅ ASYNC MIGRATION COMPLETED

## Overview

The Budget Advisor Agent is a sophisticated ReAct-based agent that serves as a financial consultant for users. It analyzes financial data, understands user goals, and creates or adjusts budget plans with detailed jar allocation recommendations. The agent operates in a 3-stage process to ensure thorough understanding, proposal refinement, and finalization. It integrates with other agents like the Transaction Fetcher and Jar Manager for data gathering and changes application.

The agent uses the ReAct (Reason-Act-Observe) framework for multi-step reasoning, conversation locking for follow-ups, and stage management to structure the advisory process.

## Async Migration Status:
- ✅ All 8 async tools use direct service calls
- ✅ 2 sync tools appropriately remain sync (return dictionaries only)
- ✅ inspect.iscoroutinefunction() check added to main.py
- ✅ Direct PlanManagementService and JarManagementService integration
- ✅ AgentCommunicationService for cross-agent communication
- ✅ Proper async/await patterns throughout

## Core Features

- **ReAct Framework**: Reasons step-by-step, acts by calling tools, and observes results in a loop until a terminating tool is called.
- **3-Stage Process**:
  - **Stage 1 (Understand Context)**: Gathers data from transactions, jars, and existing plans; clarifies ambiguities.
  - **Stage 2 (Propose Changes)**: Presents and refines financial plans and jar adjustments based on feedback until user accepts (by typing 'ACCEPT').
  - **Stage 3 (Finalize)**: Creates or adjusts the plan with jar change commands sent to the Jar Manager.
- **Conversation Lock & Follow-Up**: Locks the conversation for clarification or refinement, releasing only after finalization.
- **Cross-Agent Integration**: Calls Transaction Fetcher for spending data and Jar Manager (via service) for budget updates.
- **Data-Driven Recommendations**: Uses total income, jar balances, and transaction history for personalized advice.
- **Bilingual Support**: Handles English and Vietnamese queries naturally.

## How it Works: The ReAct Flow with Stages

The agent's process is divided into stages, with ReAct looping within each stage until a terminating tool is called:

1. **Stage Detection**: Determined from conversation history (JSON in last output).
2. **Tool Binding**: Stage-specific tools are bound to the LLM.
3. **ReAct Loop**:
   - **Reason**: LLM thinks based on prompt and history.
   - **Act**: Calls tools (informational for data, terminating to end turn).
   - **Observe**: Adds tool results to messages.
   - Loop stops on terminating tool call or max iterations.
4. **Stage Transitions**:
   - Stage 1 → 2: Via `propose_plan`.
   - Stage 2 loop: Refines with `propose_plan` until user inputs 'ACCEPT'.
   - Stage 2 → 3: On 'ACCEPT', transitions and runs ReAct in stage 3.
   - Stage 3 ends after plan tool call.
5. **Terminating Tools**:
   - Stage 1: `request_clarification`, `propose_plan`.
   - Stage 2: `propose_plan`.
   - Stage 3: `create_plan`, `adjust_plan`.

## Agent Components

- `main.py`: Implements the ReAct loop, stage management, tool execution, and orchestrator interface.
- `prompt.py`: Builds stage-specific prompts with tool lists and instructions.
- `tools.py`: Defines tools, including data gathering, plan management, clarification, proposal, and stage-specific getters.
- `interface.py`: Provides a clean interface for the orchestrator.
- `config.py`: Handles configuration (e.g., API key, max iterations) from `.env`.
- `test.py`: Interactive script for testing the agent and multi-stage flows.
- `.env.example`: Template for environment variables.

## Configuration

Create a `.env` file in `agents/plan/` with:
