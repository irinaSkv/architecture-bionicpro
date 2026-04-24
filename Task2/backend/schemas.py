from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class ReportResponse(BaseModel):
    username: str
    total_usage: int
    active_sessions: int
    last_activity: Optional[str] = None
    report_data: Dict[str, Any] = {}

    class Config:
        from_attributes = True