from typing import Dict, List, Optional
from pydantic import BaseModel


class UpdateDescriptionRequest(BaseModel):
    description: Optional[str]
    place_data: Dict


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict] = None
    error: Optional[str] = None 