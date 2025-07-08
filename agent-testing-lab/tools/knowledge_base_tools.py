"""
Tools for the KnowledgeBase Agent.
Provides general financial education through mocked RAG pipeline.
"""

from langchain_core.tools import tool


# Mock knowledge base documents
MOCK_KNOWLEDGE_BASE = {
    "compound interest": """
    Compound interest is the interest you earn on both your original money (principal) 
    and the interest you've already earned. It's often called "interest on interest" 
    and can significantly boost your savings over time. The key is to start early 
    and be consistent with your savings habits.
    """,
    
    "50/30/20 rule": """
    The 50/30/20 rule is a simple budgeting guideline that suggests allocating:
    - 50% of after-tax income to needs (housing, food, utilities)
    - 30% to wants (entertainment, dining out, hobbies) 
    - 20% to savings and debt repayment
    This provides a balanced approach to managing your finances.
    """,
    
    "emergency fund": """
    An emergency fund is money set aside to cover unexpected expenses like medical bills,
    car repairs, or job loss. Financial experts recommend saving 3-6 months of living 
    expenses in an easily accessible account. This provides financial security and peace of mind.
    """,
    
    "investing basics": """
    Investing involves putting money into assets like stocks, bonds, or real estate with 
    the expectation of earning returns over time. Key principles include diversification,
    starting early to benefit from compound growth, and investing regularly regardless 
    of market conditions (dollar-cost averaging).
    """
}


@tool
def query_knowledge_base(query: str) -> str:
    """
    Retrieves information from a curated set of financial documents.
    
    Args:
        query: Search query for financial information
    
    Returns:
        Relevant financial information or guidance to ask specific questions
    """
    query_lower = query.lower()
    
    # Search for relevant content
    for topic, content in MOCK_KNOWLEDGE_BASE.items():
        if any(word in query_lower for word in topic.split()):
            return f"**{topic.title()}**\n\n{content.strip()}"
    
    # If no direct match, provide helpful guidance
    available_topics = list(MOCK_KNOWLEDGE_BASE.keys())
    return f"""
I don't have specific information about '{query}', but I can help with these financial topics:
- {', '.join(available_topics)}

Please ask about one of these topics, or rephrase your question to be more specific.
""".strip() 