from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

# Define the allowed agent types
AGENT_LIST = Literal["classifier", "jar", "fee", "plan", "fetcher", "knowledge", "orchestrator"]

class ConversationTurnBase(BaseModel):
    """
    Base model for a single turn in a conversation.
    """
    user_input: str = Field(..., description="The user's message to the agent.")
    agent_output: str = Field(..., description="The agent's response to the user.")
    agent_list: List[AGENT_LIST] = Field(default_factory=list, example=["orchestrator", "jar"], description="A list of agents that were involved in generating the response.")
    tool_call_list: List[str] = Field(default_factory=list, example=["jar.list_jars()"], description="A list of tools that were called by the agents.")

class ConversationTurnCreate(ConversationTurnBase):
    """
    Model used when creating a new conversation turn.
    This is what the application logic will use to log a new turn.
    """
    pass

class ConversationTurnInDB(ConversationTurnBase):
    """
    Model representing a conversation turn as it is stored in the database.
    """
    id: str = Field(alias="_id", description="The unique identifier for the conversation turn.", example="60d5ecf3e7b3c2a4c8f3b3a7")
    user_id: str = Field(description="The ID of the user who had this conversation.", example="60d5ecf3e7b3c2a4c8f3b3a2")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="The timestamp of the conversation turn.")
    agent_lock: Optional[AGENT_LIST] = Field(None, description="The agent that currently has the conversation lock, if any.")
    plan_stage: Optional[str] = Field(None, description="The current stage of the plan agent, if applicable.", example="1")
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
