# Implementation Plan: Active Agent Context (Conversation Lock)

## 1. The Problem: Stateless Orchestrator vs. Stateful Conversations

The current system uses a stateless orchestrator to route user requests to specialist agents. This works for simple, one-shot commands but fails during complex, multi-turn conversations.

When a specialist agent (like the `Budget Advisor`) asks the user a clarifying question, the user's response is sent back to the orchestrator. The orchestrator lacks the specific context of the ongoing dialogue and may fail to route the response back to the correct agent, leading to a "panic" or incorrect behavior.

## 2. The Solution: Active Agent Context (Conversation Lock)

As detailed in `propose_solution.md`, we will implement a "Conversation Lock" pattern. This pattern temporarily delegates routing control from the orchestrator to the specialist agent that is in the middle of a conversation.

- **Engaging the Lock:** When an agent asks a clarifying question, it will signal that it requires a follow-up. The system will "lock" the conversation on this agent.
- **Maintaining the Lock:** The user's next response will bypass the orchestrator and be sent directly to the locked agent. The agent can continue its task and maintain the lock if more questions are needed.
- **Releasing the Lock:** Once the agent's task is complete, it will signal that no follow-up is required, and the lock will be released. The system returns to being managed by the orchestrator.

---

## 3. Implementation Details

### Part A: Conversation History Management

To support this new model, we will refine how conversation history is handled:

1.  **Orchestrator Access:** The orchestrator will continue to receive the full, recent conversation history to make the best initial routing decision for new tasks.
2.  **Specialist Agent Access:** When routed a task, a specialist agent will receive a filtered history containing only previous turns where it was involved. This will be accomplished with a new utility function: `get_agent_specific_history(agent_name: str)`.
3.  **Locked Agent Access:** An agent with a conversation lock will have the relevant history passed to it directly by the main control loop.

### Part B: Agent Modification for Follow-up Signaling

Agents need a mechanism to signal their intent to continue a conversation. This will be handled by modifying the tools they use to ask users questions. When one of these tools is called, it will be responsible for engaging the conversation lock.

1.  **Unified Return Structure:** The main processing loop for each agent will be standardized to return a dictionary: `{"response": "...", "requires_follow_up": True/False}`. The `requires_follow_up` flag will be set by the tool that is called.

2.  **`plan` Agent (`budget_advisor`):**
    *   **Tool to Modify:** `respond` in `agents/plan/tools.py`.
    *   **Logic:** When the `respond` tool is called with the `question_ask_user` argument, it will set `requires_follow_up` to `True` and engage the conversation lock. If called without a question, it will set the flag to `False` and release any existing lock.

3.  **`jar` Agent (`jar_manager`):**
    *   **Tool to Modify:** `request_clarification` in `agents/jar/tools.py`.
    *   **Logic:** This tool will be updated to always set `requires_follow_up` to `True` and engage the conversation lock, as its sole purpose is to ask a question.

4.  **`fee` Agent (`fee_manager`):**
    *   **Tool to Modify:** `request_clarification` in `agents/fee/tools.py`.
    *   **Logic:** Similar to the jar agent, this tool will be updated to always set `requires_follow_up` to `True` and engage the lock.

5.  **`classifier` Agent (`transaction_classifier`):**
    *   **Tool to Modify:** `request_more_info` in `agents/classifier/tools.py`.
    *   **Logic:** The docstring for this tool will be updated. Instead of being a final action, it will now engage the conversation lock and set `requires_follow_up` to `True`.

### Part C: Refactoring the Orchestrator into the Main Controller

The `agents/orchestator/main.py` will be transformed from a test script into the primary, interactive control loop for the entire system.

1.  **State Variable:** A global `active_agent_context: Optional[str]` variable will be introduced in `database.py` to track the locked agent.
2.  **New Control Flow:** The main loop in the new orchestrator will implement the core logic:
    *   **Check for Lock:** Before calling the orchestrator, it will check if `active_agent_context` is set.
    *   **Bypass if Locked:** If an agent has the lock, the user's input is sent directly to that agent.
    *   **Route if Unlocked:** If there is no lock, the input is sent to the orchestrator for normal routing.
3.  **Manage Lock State:** The control loop will be responsible for setting or clearing `active_agent_context` based on the `requires_follow_up` flag returned by the specialist agents.

---

## 4. Summary of Changes

- **`database.py`:**
    - Add `active_agent_context` state variable and getter/setter functions.
- **`utils.py`:**
    - Add `get_agent_specific_history(agent_name)` function.
- **`agents/plan/tools.py`:**
    - Update the `respond` tool to handle the conversation lock.
- **`agents/jar/tools.py`:**
    - Update the `request_clarification` tool to handle the conversation lock.
- **`agents/fee/tools.py`:**
    - Update the `request_clarification` tool to handle the conversation lock.
- **`agents/classifier/tools.py`:**
    - Update the `request_more_info` tool to handle the conversation lock.
- **Agent Interfaces (`interface.py` for all modified agents):**
    - Update `process_task` return types to be a dictionary `{"response": str, "requires_follow_up": bool}`.
- **`agents/orchestator/main.py`:**
    - Rework into the main interactive application loop, implementing the stateful control flow.
- **`agents/orchestator/test.py`:**
    - A new `test.py` will be created to run the full interactive system. 