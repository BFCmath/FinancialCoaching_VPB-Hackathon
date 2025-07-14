from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ConversationTurnBase(BaseModel):
    """
    Base model for a single turn in a conversation.
    """
    user_input: str = Field(..., description="The user's message to the agent.")
    agent_output: str = Field(..., description="The agent's response to the user.")
    agent_list: List[str] = Field(default_factory=list, example=["orchestrator", "jar_agent"], description="A list of agents that were involved in generating the response.")
    tool_call_list: List[str] = Field(default_factory=list, example=["jar_agent.list_jars()"], description="A list of tools that were called by the agents.")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata for the conversation turn, including agent stage information and other context.")

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
    agent_lock: Optional[str] = Field(None, description="Agent that has conversation lock")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
