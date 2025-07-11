"""
Knowledge Base Agent - ReAct Framework
=====================================

Main agent that handles financial knowledge and app documentation questions
using a ReAct (Reason-Act) framework with proper LangChain tool calling.
"""

from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from tools import get_all_knowledge_tools
from prompt import build_react_prompt
import config


class KnowledgeBaseAgent:
    """Knowledge Base Agent using ReAct framework with proper LangChain tool calling"""
    
    def __init__(self):
        """Initialize the agent with LLM and tools"""
        self.llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=config.google_api_key,
            temperature=config.llm_temperature
        )
        
        # Bind all tools to LLM for intelligent selection
        self.tools = get_all_knowledge_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Track conversation for ReAct
        self.conversation_history = []
    
    def get_knowledge(self, user_query: str) -> str:
        """
        Main method to get knowledge using proper ReAct framework.
        Continues conversation until respond() tool is called.
        
        Args:
            user_query: User's question about financial concepts or app features
            
        Returns:
            Final formatted answer from respond() tool
        """
        
        try:
            # Build ReAct system prompt  
            system_prompt = build_react_prompt()
            
            # Initialize conversation
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ]
            
            if config.debug_mode:
                print(f"🔍 Processing query: {user_query}")
                print(f"🧠 System prompt length: {len(system_prompt)} chars")
            
            # ReAct Loop: Continue until respond() is called
            max_iterations = config.max_react_iterations
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                if config.debug_mode:
                    print(f"\n🔄 ReAct Iteration {iteration}/{max_iterations}")
                    print("=" * 40)
                
                # Get LLM response with tools
                response = self.llm_with_tools.invoke(messages)
                
                if config.debug_mode:
                    print(f"🤖 LLM Response Type: {type(response)}")
                    if hasattr(response, 'content') and response.content:
                        print(f"💭 LLM Thinking: {response.content[:100]}...")
                    if hasattr(response, 'tool_calls') and response.tool_calls:
                        print(f"🔧 Tool Calls: {len(response.tool_calls)}")
                
                # Add AI message to conversation
                messages.append(AIMessage(content=response.content, tool_calls=response.tool_calls if hasattr(response, 'tool_calls') else []))
                
                # Process tool calls if any
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    
                    if config.debug_mode:
                        print(f"\n🔧 Processing {len(response.tool_calls)} tool call(s):")
                    
                    for i, tool_call in enumerate(response.tool_calls, 1):
                        tool_name = tool_call['name']
                        tool_args = tool_call.get('args', {})
                        tool_call_id = tool_call.get('id', f'call_{i}')
                        
                        if config.debug_mode:
                            print(f"\n📞 Call {i}: {tool_name}()")
                            print(f"📋 Parameters: {tool_args}")
                        
                        # Find and execute tool
                        tool_func = None
                        for tool in self.tools:
                            if tool.name == tool_name:
                                tool_func = tool
                                break
                        
                        if tool_func:
                            try:
                                result = tool_func.invoke(tool_args)
                                
                                # Special handling for respond() tool - THIS IS THE KEY FIX
                                if tool_name == "respond" and isinstance(result, dict):
                                    final_answer = result.get("data", {}).get("final_answer", "")
                                    if config.debug_mode:
                                        print(f"✅ Final answer received: {final_answer[:100]}...")
                                        print(f"🏁 ReAct completed in {iteration} iterations")
                                    return final_answer
                                
                                # Add tool result to conversation
                                messages.append(ToolMessage(
                                    content=str(result),
                                    tool_call_id=tool_call_id
                                ))
                                
                                if config.debug_mode:
                                    print(f"✅ Tool result: {str(result)[:150]}...")
                                    
                            except Exception as e:
                                error_msg = f"❌ Tool {tool_name} failed: {str(e)}"
                                messages.append(ToolMessage(
                                    content=error_msg,
                                    tool_call_id=tool_call_id
                                ))
                                if config.debug_mode:
                                    print(f"❌ Error: {error_msg}")
                        else:
                            error_msg = f"❌ Tool {tool_name} not found"
                            messages.append(ToolMessage(
                                content=error_msg,
                                tool_call_id=tool_call_id
                            ))
                            if config.debug_mode:
                                print(f"❌ Error: {error_msg}")
                    
                    # Continue the loop to let LLM process tool results and potentially call respond()
                    continue
                
                else:
                    # No tool calls - LLM provided direct response without tools
                    if config.debug_mode:
                        print("🤖 No tool calls - direct response")
                    return response.content if hasattr(response, 'content') else str(response)
            
            # If we reach here, max iterations exceeded without respond() being called
            if config.debug_mode:
                print(f"⚠️ Max iterations ({max_iterations}) reached without respond() call")
            
            return f"❌ Could not provide a complete answer within {max_iterations} reasoning steps. Please try a simpler question."
                
        except Exception as e:
            error_msg = f"❌ Error processing request: {str(e)}"
            if config.debug_mode:
                import traceback
                print(f"🐛 Full error traceback:\n{traceback.format_exc()}")
            return error_msg
    
    def quick_test(self, test_queries: List[str] = None) -> Dict[str, str]:
        """
        Quick test of the agent with common queries.
        
        Args:
            test_queries: List of test questions (optional)
            
        Returns:
            Dict mapping queries to responses
        """
        
        if test_queries is None:
            test_queries = [
                "What is compound interest?",
                "How does the jar system work?", 
                "What is budgeting and how does this app help?",
                "Tell me about the app features"
            ]
        
        results = {}
        
        for query in test_queries:
            print(f"\n🔍 Testing: {query}")
            try:
                result = self.get_knowledge(query)
                results[query] = result
                print(f"✅ Response: {result[:150]}...")
            except Exception as e:
                results[query] = f"Error: {str(e)}"
                print(f"❌ Error: {str(e)}")
        
        return results


# Convenience functions for direct usage
def get_knowledge_response(user_query: str) -> str:
    """
    Simple function to get a knowledge response.
    
    Args:
        user_query: User's question
        
    Returns:
        Knowledge response
    """
    agent = KnowledgeBaseAgent()
    return agent.get_knowledge(user_query)


def quick_knowledge_test():
    """Run a quick test of the knowledge base agent"""
    agent = KnowledgeBaseAgent()
    return agent.quick_test()


if __name__ == "__main__":
    # Example usage
    agent = KnowledgeBaseAgent()
    
    # Interactive mode
    print("🧠 Knowledge Base Agent - ReAct Framework")
    print("Ask me about financial concepts or app features!")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            user_input = input("❓ Your question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("\n🤔 Thinking...")
            response = agent.get_knowledge(user_input)
            print(f"\n💡 Answer: {response}\n")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
