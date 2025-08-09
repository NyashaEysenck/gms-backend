from pydantic import BaseModel

class GrantCall(BaseModel):
    """Exact match to frontend GrantCall structure"""
    id: str
    title: str
    type: str
    sponsor: str
    deadline: str
    scope: str
    eligibility: str
    requirements: str
    status: str
    visibility: str

    class Config:
        allow_population_by_field_name = True
