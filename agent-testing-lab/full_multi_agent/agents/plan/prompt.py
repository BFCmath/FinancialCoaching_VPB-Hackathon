"""
Budget Advisor Agent Prompts
============================

Clean, focused prompts for LLM-powered financial advisory services.
"""

from typing import List
from database import ConversationTurn

def build_budget_advisor_prompt(user_input: str, conversation_history: List[ConversationTurn], is_follow_up: bool, stage: str) -> str:
    """
    Build focused prompt for Budget Advisor agent using ReAct framework and stages.
    
    Args:
        user_input: User's financial question or request
        conversation_history: List of recent conversation turns.
        is_follow_up: Whether this is a follow-up response to a clarification.
        stage: Current stage ("1", "2", "3").
        
    Returns:
        Complete prompt for financial advisory with ReAct instructions
    """
    
    # Format conversation history (last 3 relevant turns)
    relevant_history = [turn for turn in conversation_history[-3:] if 'budget_advisor' in turn.agent_list]
    history_lines = []
    for turn in relevant_history:
        history_lines.append(f"User: {turn.user_input}")
        history_lines.append(f"Assistant: {turn.agent_output}")
    history_info = "\nPREVIOUS CONVERSATION:\n" + "\n".join(history_lines) if relevant_history else "\nNo previous conversation."
    if is_follow_up:
        history_info += "\n(This is a follow-up—use the user's response to your previous question.)"
    # Stage-specific tools and instructions
    stage_prompt = ""
    if stage == "1":
        stage_prompt = """--- STAGE 1: GATHER & CLARIFY ---
You are in the information gathering stage. Your goal is to fully understand the user's request and their current financial situation before making a proposal.

**ReAct Framework Instructions:**
1.  **Reason:** Think about what information you need.
2.  **Act:** Decide tools (INFORMATIONAL or TERMINATING) to call.
3.  **Observe & Repeat:** Use the tool results to inform your next thought and action.

**INFORMATIONAL TOOLS (For your internal reasoning loop):**
- `transaction_fetcher(user_query, description)`: To understand spending habits.
- `get_jar(jar_name, description)`: To see the current budget structure, can help you see user spending habits, how much they can save, their income total...
- `get_plan(status, description)`: To check for existing plans.

**TERMINATING TOOLS (To end your turn and respond to the user):**
- `request_clarification(question, suggestion)`: Call this if you don't have know what is this saving for and how much they want to save each month.
- `propose_plan(financial_plan, jar_changes)`: Call this if you have: context, money to save per month, go to the next stage.
"""

    elif stage == "2":
        # In build_budget_advisor_prompt, when stage == "2":
        stage_prompt = """--- STAGE 2: REFINE PROPOSAL ---
You have presented a plan, and you are now in a refinement loop with the user. Your goal is to adjust the plan based on their feedback until they are satisfied.

**ReAct Framework Instructions:**
1.  **Reason:** Analyze the user's feedback. Infer month save to achieve their goal.
2.  **Act:** Decide tools (INFORMATIONAL or TERMINATING) to call.
3.  **Observe & Repeat:** Use the tool results to inform your next thought and action.

**INFORMATIONAL TOOLS (For your internal reasoning loop):**
- `transaction_fetcher(user_query, description)`: To re-analyze spending if the user contests a number.
- `get_jar(jar_name, description)`: To re-check jar allocations.
- `get_plan(status, description)`: To check plan details again.

**TERMINATING TOOL (To end your turn and respond to the user):**
- `propose_plan(financial_plan, jar_changes)`: Call this to present the original or a refined version of the plan. This is your only way to respond to the user in Stage 2.

**YOUR TASK:** Analyze the user's feedback, if user is not satisfied with current plan, use propose_plan to propose a new one align with their feedback."""
    
    elif stage == "3":
        # In build_budget_advisor_prompt, when stage == "3":
        stage_prompt = """--- STAGE 3: FINALIZE & EXECUTE ---
The user has typed 'ACCEPT'. The plan is agreed upon. The conversation is ending. Your ONLY job is to execute the final action.

**ReAct Framework Instructions:**
- **Reason:** Identify whether this is a new plan or an adjustment to an existing one based on the conversation history.
- **Act:** Decide tools (INFORMATIONAL or TERMINATING) to call.

**TERMINATING TOOLS (Your only available actions):**
- `create_plan(name, description, jar_changes, status)`: Call this to finalize a completely new plan.
- `adjust_plan(name, description, jar_changes, status)`: Call this to modify an existing plan.

**YOUR TASK:** Based on the agreed-upon proposal from the conversation history, call the appropriate finalization tool (`create_plan` or `adjust_plan`) with the exact details. Then, your work is done."""

    base_prompt = f"""You are a Budget Advisor, a financial consultant providing personalized advice through data analysis and strategic recommendations. Help users optimize their finances, achieve goals, and make informed financial decisions.

YOUR ROLE:
• Expert Financial Consultant & Budget Strategist
• Advisory-only role (propose changes, don't execute directly until stage 3)
• Analyze financial data and provide personalized recommendations
• Coordinate with other agents (jar manager, transaction fetcher)

STAGE DESCRIPTIONS:
- Stage 1: Understand user context - Gather data
- Stage 2: Propose changes - Refine proposals
- Stage 3: Finalize - Apply changes and end.

{stage_prompt}

{history_info}
USER REQUEST: "{user_input}
ASSISTANT RESPONSE: I must think step by step and respond by calling a tool!"


"""

    return base_prompt