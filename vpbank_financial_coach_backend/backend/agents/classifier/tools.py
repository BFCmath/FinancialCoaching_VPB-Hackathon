"""
Classification Tools for ReAct-based Transaction Classifier
===========================================================

Tools that the ReAct-based classifier LLM can call to handle transaction
classification. Includes tools for gathering information and for executing
the final classification action.

This implementation uses dependency injection with ServiceContainer for 
production-ready multi-user support.
"""

import sys
import os

# Add the parent directories to path to import from service layer
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from langchain_core.tools import tool
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import direct async services (no adapters)
from backend.services.transaction_service import TransactionService
from backend.services.communication_service import AgentCommunicationService


class ClassifierServiceContainer:
    """
    Request-scoped service container for classifier agent.
    Provides direct access to async services.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id


def get_all_classifier_tools(services: ClassifierServiceContainer) -> List[tool]:
    """
    Create classifier tools with injected service dependencies.
    
    Args:
        services: Service container with user context
        
    Returns:
        List of configured tools for the classifier agent
    """
    
    # =============================================================================
    # INFORMATION GATHERING TOOL
    # =============================================================================

    @tool
    async def transaction_fetcher(user_query: str, description: str) -> Dict[str, Any]:
        """
        Gathers historical data about transactions to handle ambiguous user inputs.

        Use this as your primary information-gathering tool when the user's request
        is incomplete. For example, if the amount is missing from a transaction
        (e.g., user says "coffee"), or the description is too vague.

        Args:
            user_query: A specific, targeted query for the type of transaction history
                        you need. For example: "past coffee transactions", "transactions
                        for 'rent' in the last 3 months", "what did I spend $50 on last week".
            description: A brief, clear explanation for why you are fetching this data.
                         This helps in debugging and understanding the agent's reasoning.
                         Example: "To find the average cost of coffee to infer the amount."

        Returns:
            A dictionary containing a list of past transactions that match the query.
            This data can then be used to infer missing details in your reasoning process.
        """
        return await AgentCommunicationService.call_transaction_fetcher(
            services.db, services.user_id, user_query, description
        )

    # =============================================================================
    # FINAL ACTION / TERMINAL TOOLS
    # =============================================================================

    @tool
    async def add_money_to_jar_with_confidence(amount: float, jar_name: str, confidence: int) -> str:
        """
        FINAL ACTION: Classifies a transaction by adding a specific amount to a budget jar.

        This is a terminal tool. Call it only when you have all the necessary information
        (a clear description, amount, and target jar) and are confident in your decision.
        This tool should be used to finalize a successful classification.

        Args:
            amount: The exact monetary value of the transaction (e.g., 15.50).
            jar_name: The precise name of the target jar the money should be added to.
                      This must match one of the available jars.
            confidence: Your confidence level (from 0 to 100) in this classification,
                        based on the clarity of the user's input and any data you fetched.

        Returns:
            A success message confirming the transaction has been logged.
        """
        return await TransactionService.add_money_to_jar_with_confidence(
            services.db, services.user_id, amount, jar_name, confidence, source="text_input"
        )

    @tool
    def report_no_suitable_jar(description: str, suggestion: str) -> str:
        """
        FINAL ACTION: Reports that a transaction cannot be classified into any existing jar.

        This is a terminal tool. Use it when the user's expense does not fit any of the
        current budget categories. This allows the agent to fail gracefully and provide
        helpful feedback to the user.

        Args:
            description: A clear description of the transaction that could not be classified.
                         Example: "The expense for a 'new bicycle helmet'".
            suggestion: A helpful suggestion for the user on how they could handle this
                        in the future. Example: "You might want to create a 'Sporting Goods' jar."

        Returns:
            A message explaining that no suitable jar was found, including the suggestion.
        """
        return TransactionService.report_no_suitable_jar(description, suggestion)

    @tool
    def respond(pattern_found: str, confirm_question: str) -> str:
        """
        FINAL ACTION: Presents findings from data analysis and asks a confirmation question.

        This is a terminal tool. Use it when you have a strong hypothesis based on
        fetched data, but you require the user's final confirmation to proceed.
        Calling this tool ends the agent's turn; the user's response will be processed
        as a new, separate turn.

        Args:
            pattern_found: A clear and concise statement describing the pattern or inference
                           you made from the data. This is a statement of fact, not a question.
                           Example: "Based on your history, your last 3 coffee purchases were all $5."
            confirm_question: The single, direct question you want to ask the user to confirm
                              your hypothesis. Example: "Should I classify this transaction as $5?"

        Returns:
            A formatted string containing both the finding and the question for the user.
        """
        # This is a final action, so it does not set a conversation lock.
        # The user's response will be handled by the orchestrator in the next turn.
        return f"Finding: {pattern_found}\nQuestion: {confirm_question}"

    # =============================================================================
    # TOOL REGISTRATION
    # =============================================================================

    return [
        transaction_fetcher,
        add_money_to_jar_with_confidence,
        report_no_suitable_jar,
        respond
    ]


# Backward compatibility function (deprecated)
def get_all_classifier_tools_legacy() -> List[tool]:
    """
    Legacy function for backward compatibility.
    Raises an error since global services are not production-ready.
    """
    raise RuntimeError(
        "Legacy global service approach is not production-ready. "
        "Use get_all_classifier_tools(services) with ServiceContainer instead."
    )
