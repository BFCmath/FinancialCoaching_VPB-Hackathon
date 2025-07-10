"""
Transaction History Fetcher
===========================

LangChain tool binding system for transaction data retrieval.
Simple single-pass processing with intelligent multi-tool selection.
"""

import json
from typing import Dict, List, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import BaseTool

from config import config
from tools import get_all_transaction_tools, fetch_available_jars
from prompt import build_history_fetcher_prompt

class TransactionHistoryFetcher:
    """Transaction history fetcher using LangChain tool binding."""
    
    def __init__(self):
        """Initialize the history fetcher with LLM and bound tools."""
        self.llm = self._create_llm()
        self.tools = get_all_transaction_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        if config.debug_mode:
            print(f"✅ Transaction History Fetcher initialized")
            print(f"   • Model: {config.model_name}")
            print(f"   • Tools bound: {len(self.tools)}")
    
    def _create_llm(self) -> ChatGoogleGenerativeAI:
        """Create and configure the LLM instance."""
        if not config.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required")
        
        return ChatGoogleGenerativeAI(
            model=config.model_name,
            temperature=config.temperature,
            google_api_key=config.google_api_key
        )
    
    def fetch_transaction_history(self, user_query: str, context: Dict = None) -> List[Dict]:
        """
        Fetch transaction history and return transaction data with descriptions.
        
        Args:
            user_query: User's natural language query
            context: Optional context (unused but kept for compatibility)
            
        Returns:
            List of dictionaries, each containing:
            - tool_name: Name of the tool used
            - args: Arguments passed to the tool
            - data: List of transaction dictionaries
            - description: Human-readable description of what the data represents
        """
        try:
            if config.debug_mode:
                print(f"🔍 Processing query: {user_query}")
            
            # Build prompt with jar information
            available_jars = fetch_available_jars()
            system_prompt = build_history_fetcher_prompt(user_query, available_jars)
            
            # Create messages for LLM
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ]
            
            # Get LLM response with tool calls
            if config.debug_mode:
                print(f"🤖 Invoking LLM with {len(self.tools)} tools available")
            
            response = self.llm_with_tools.invoke(messages)
            
            # Extract tool calls
            tool_calls = getattr(response, 'tool_calls', [])
            
            if not tool_calls:
                if config.debug_mode:
                    print("⚠️ No tool calls detected in LLM response")
                return []
            
            # Process tool calls and return data with descriptions
            return self._process_tool_calls(tool_calls, user_query)
            
        except Exception as e:
            if config.debug_mode:
                print(f"❌ Error in fetch_transaction_history: {str(e)}")
            return []

    def _process_tool_calls(self, tool_calls: List, user_query: str) -> List[Dict]:
        """
        Process tool calls and return raw transaction data with descriptions.
        
        Args:
            tool_calls: List of tool calls from LLM
            user_query: Original user query (for debugging)
            
        Returns:
            List of dictionaries containing transaction data and descriptions
        """
        if config.debug_mode:
            print(f"🔧 Processing {len(tool_calls)} tool call(s)")
        
        results = []
        
        # Execute each tool call
        for tool_call in tool_calls:
            try:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                if config.debug_mode:
                    print(f"   • {tool_name}({tool_args})")
                
                # Find and execute the tool
                tool_result = self._execute_tool(tool_name, tool_args)
                
                # Handle new format with data and description
                if isinstance(tool_result, dict) and "data" in tool_result and "description" in tool_result:
                    results.append({
                        "tool_name": tool_name,
                        "args": tool_args,
                        "data": tool_result["data"],
                        "description": tool_result["description"]
                    })
                    
                    if config.debug_mode:
                        print(f"     → {len(tool_result['data'])} transactions: {tool_result['description']}")
                        
                elif config.debug_mode and isinstance(tool_result, str) and tool_result.startswith("Error"):
                    print(f"   ❌ {tool_result}")
                
            except Exception as e:
                if config.debug_mode:
                    print(f"   ❌ Error in tool call: {str(e)}")
        
        if config.debug_mode:
            total_transactions = sum(len(result["data"]) for result in results)
            print(f"✅ Returning {len(results)} result sets with {total_transactions} total transactions")
        
        return results
    
    def _execute_tool(self, tool_name: str, tool_args: Dict) -> Any:
        """Execute a specific tool with given arguments."""
        # Find the tool by name
        tool = None
        for t in self.tools:
            if t.name == tool_name:
                tool = t
                break
        
        if not tool:
            return f"Error: Tool '{tool_name}' not found"
        
        try:
            # Execute the tool
            result = tool.func(**tool_args)
            
            if config.debug_mode:
                result_count = len(result) if isinstance(result, list) else "data"
                print(f"     → {result_count} transactions returned")
            
            return result
            
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

def fetch_transaction_history(user_query: str, context: Dict = None) -> List[Dict]:
    """
    Standalone function to fetch transaction history.
    
    Args:
        user_query: User's natural language query
        context: Optional context (unused)
        
    Returns:
        List of dictionaries, each containing:
        - tool_name: Name of the tool used
        - args: Arguments passed to the tool
        - data: List of transaction dictionaries
        - description: Human-readable description of what the data represents
    """
    fetcher = TransactionHistoryFetcher()
    return fetcher.fetch_transaction_history(user_query, context)

def quick_transaction_lookup(jar_name: str = None, time_period: str = None, limit: int = 10) -> Dict[str, Any]:
    """
    Quick lookup function for simple transaction queries.
    
    Args:
        jar_name: Optional jar name filter
        time_period: Optional time period (e.g., "last_month")
        limit: Maximum number of transactions
        
    Returns:
        Dictionary containing:
        - data: List of transaction dictionaries
        - description: Human-readable description of what the data represents
    """
    # Import here to avoid circular imports
    from tools import get_jar_transactions, get_time_period_transactions
    
    if time_period:
        return get_time_period_transactions.func(jar_name=jar_name, start_date=time_period, limit=limit)
    else:
        return get_jar_transactions.func(jar_name=jar_name, limit=limit)

# Command line testing
if __name__ == "__main__":
    print("🔍 Transaction History Fetcher - Testing Mode")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        # Simple data requests
        "Show me my groceries spending",
        "All transactions from last month", 
        "List my entertainment expenses",
        
        # Amount-based queries
        "Show me all purchases over $50",
        "Small transactions under $20",
        
        # Time-based queries
        "What did I spend yesterday?",
        "Morning spending patterns",
        
        # Comparison queries
        "Compare groceries vs meals spending",
        "Morning vs evening transactions",
        
        # Multi-filter queries
        "Large grocery purchases from last month",
        "Manual entertainment entries over $30"
    ]
    
    fetcher = TransactionHistoryFetcher()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: '{test_case}'")
        try:
            result = fetch_transaction_history(test_case)
            print(f"✅ Result:\n{result}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print("-" * 60)
