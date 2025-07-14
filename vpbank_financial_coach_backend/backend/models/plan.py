from pydantic import BaseModel, Field
from typing import Optional, Literal

# Define the allowed statuses for a plan, matching the original database.py
PlanStatus = Literal["active", "completed", "paused"]

class BudgetPlanBase(BaseModel):
    """
    Base model for a budget plan, matching lab structure exactly.
    """
    name: str = Field(..., min_length=3, max_length=200, example="Save for Vacation", description="The unique name for the budget plan.")
    detail_description: str = Field(..., max_length=5000, example="A plan to save $2000 for a trip to Japan next year.")
    day_created: str = Field(..., example="2025-07-14", description="Creation date string (matches lab structure).")
    status: PlanStatus = Field(default="active", example="active", description="The current status of the plan.")
    jar_recommendations: Optional[str] = Field(None, example="Suggest increasing 'long_term_savings' jar by 5%", description="Text or JSON string with recommendations for jar adjustments.")

class BudgetPlanCreate(BudgetPlanBase):
    """
    Model used when creating a new budget plan via the API.
    """
    pass

class BudgetPlanUpdate(BaseModel):
    """
    Model used when updating an existing budget plan. All fields are optional.
    """
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    detail_description: Optional[str] = Field(None, max_length=5000)
    status: Optional[PlanStatus] = Field(None)
    jar_recommendations: Optional[str] = Field(None)

class BudgetPlanInDB(BudgetPlanBase):
    """
    Model representing a budget plan as it is stored in the database.
    """
    id: str = Field(alias="_id", description="The unique identifier for the plan.", example="60d5ecf3e7b3c2a4c8f3b3a6")
    user_id: str = Field(description="The ID of the user who owns this plan.", example="60d5ecf3e7b3c2a4c8f3b3a2")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True