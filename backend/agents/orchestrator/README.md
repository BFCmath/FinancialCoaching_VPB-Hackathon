# Orchestrator - Central Router 

**Status**: ✅ ASYNC MIGRATION COMPLETED

## Overview
Central routing agent that manages conversation flow, agent locks, and handles direct responses vs agent routing decisions.

## Async Migration Status
- ✅ inspect.iscoroutinefunction() check added to main.py
- ✅ All routing tools are appropriately sync (routing decisions)
- ✅ Proper async/await patterns for agent communication
- ✅ Agent lock management with database integration

## Core Features
- Intent classification and routing
- Conversation lock management
- Direct response capability
- Multi-agent orchestration
- Production-ready error handling
