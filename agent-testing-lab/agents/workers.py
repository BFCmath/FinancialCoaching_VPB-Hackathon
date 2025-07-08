"""
Worker Agents - Specialized agents that execute specific tasks.
Generic worker node creation function that can be customized for each agent type.
"""

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from state import GraphState
from typing import List
from langchain_core.tools import BaseTool


def create_worker_node(agent_name: str, system_prompt: str, tools: List[BaseTool], model_name: str = "gemini-pro"):
    """
    Creates a worker node function for the graph.
    
    Args:
        agent_name: Name of the agent (for logging/debugging)
        system_prompt: System prompt defining the agent's role and behavior
        tools: List of tools available to this agent
        model_name: Name of the Google AI model to use
    
    Returns:
        Function suitable for use as a LangGraph node
    """
    
    # Initialize the LLM with tool calling capability
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.1,
        convert_system_message_to_human=True
    )
    llm_with_tools = llm.bind_tools(tools)
    
    def worker_node(state: GraphState) -> GraphState:
        """
        Worker node function that executes tasks using available tools.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with task results
        """
        
        # Get the user's original request
        messages = state["messages"]
        
        # Find the original human message
        human_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                human_message = msg
                break
        
        if not human_message:
            return {
                "messages": [AIMessage(content=f"{agent_name} error: No user request found")],
                "task_complete": True,
                "next_agent": "orchestrator"
            }
        
        # Prepare conversation for the worker agent
        conversation = [
            SystemMessage(content=system_prompt),
            human_message
        ]
        
        # Get initial response from the agent
        response = llm_with_tools.invoke(conversation)
        
        # Execute tools if called
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Process tool calls
            tool_results = []
            for tool_call in response.tool_calls:
                try:
                    # Find the tool by name
                    tool = None
                    for t in tools:
                        if t.name == tool_call["name"]:
                            tool = t
                            break
                    
                    if tool:
                        # Execute the tool
                        result = tool.invoke(tool_call["args"])
                        tool_results.append(f"Tool '{tool_call['name']}' result: {result}")
                    else:
                        tool_results.append(f"Tool '{tool_call['name']}' not found")
                        
                except Exception as e:
                    tool_results.append(f"Error executing tool '{tool_call['name']}': {str(e)}")
            
            # Generate final response based on tool results
            final_prompt = f"""
Based on the tool execution results below, provide a clear, user-friendly response about what was accomplished:

Tool Results:
{chr(10).join(tool_results)}

Respond as if you are speaking directly to the user about what you've done for them.
"""
            
            final_response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=final_prompt)
            ])
            
            return {
                "messages": [final_response],
                "task_complete": True,
                "next_agent": "orchestrator"
            }
        else:
            # No tools called - return the agent's direct response
            return {
                "messages": [response],
                "task_complete": True, 
                "next_agent": "orchestrator"
            }
    
    return worker_node


# Agent-specific system prompts
AGENT_PROMPTS = {
    "jar_manager": """
You are the JarManager Agent, specializing in budget jar operations. Your role is to:

1. Create new budget jars when users want to add categories
2. Update existing jars (name changes, percentage adjustments)  
3. Delete jars when requested
4. Handle budget rebalancing when percentages change

Use your available tools to fulfill the user's jar-related requests. Always ensure percentage totals don't exceed 100%.
When you complete a task, provide a clear summary of what was changed.
""",

    "transaction_classifier": """
You are the TransactionClassifier Agent, specializing in transaction logging. Your role is to:

1. Parse user descriptions of spending into structured transactions
2. Use historical patterns to categorize transactions intelligently
3. Log transactions to the appropriate budget jars
4. Ask for clarification when categorization is ambiguous

Use your tools to analyze the transaction description and historical patterns. If you're confident about the categorization, log it directly. If ambiguous, ask the user for clarification.
""",

    "fee_manager": """
You are the FeeManager Agent, specializing in recurring fees and subscriptions. Your role is to:

1. Set up new recurring fees with proper scheduling
2. Modify existing recurring fees
3. Cancel/delete recurring fees when requested
4. Handle complex recurrence patterns (daily, weekly, monthly)

Use your tools to manage the user's recurring financial commitments. Always confirm the schedule and jar assignment.
""",

    "budget_advisor": """
You are the BudgetAdvisor Agent, specializing in financial planning and advice. Your role is to:

1. Analyze user financial goals and create actionable plans
2. Review spending patterns and suggest improvements
3. Help users save for specific goals
4. Provide personalized financial guidance

Use your read-only tools to gather financial data, then formulate concrete proposals. Present clear recommendations with specific steps the user can take.
""",

    "knowledge_base": """
You are the KnowledgeBase Agent, specializing in financial education. Your role is to:

1. Answer general financial questions using your knowledge base
2. Provide educational content about financial concepts
3. Decline to answer personal financial questions (redirect to BudgetAdvisor)
4. Offer guidance on financial best practices

Use your knowledge base tool to provide accurate, educational responses. Stick to general financial concepts and avoid giving personal financial advice.
"""
} 