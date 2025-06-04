from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class BruteforceRequest(BaseModel):
    hash_to_crack: str = Field(..., description="The hash to be cracked.")
    max_length: int = Field(..., gt=0, description="Maximum length of the password to try.")
    charset: Optional[str] = Field(None, description="Optional custom charset. Defaults to alphanumeric if not provided.")
    # For variant 5, 'hash_type' is mentioned but not specified if it's part of request or server-decided.
    # Assuming it might be part of the request in a more complex scenario or determined by server.
    # For now, let's assume the server handles 'rar' or a specific type implicitly.

class TaskCreationResponse(BaseModel):
    task_id: str
    message: str

# WebSocket Message Schemas
class WebSocketMessageBase(BaseModel):
    task_id: str
    status: str

class TaskStartedMessage(WebSocketMessageBase):
    status: str = "STARTED"
    hash_type: str # e.g., "rar"
    charset_length: int
    max_length: int

class TaskProgressMessage(WebSocketMessageBase):
    status: str = "PROGRESS"
    progress: float # Percentage, 0.0 to 100.0
    current_combination: Optional[str] = None
    combinations_per_second: Optional[float] = None

class TaskCompletedMessage(WebSocketMessageBase):
    status: str = "COMPLETED"
    result: Optional[str] = Field(None, description="Found password, or null if not found.")
    elapsed_time: str # Formatted time string, e.g., "00:05:23"

class TaskFailedMessage(WebSocketMessageBase):
    status: str = "FAILED"
    error: str

# Generic response for actions like cancel
class TaskActionResponse(BaseModel):
    task_id: str
    message: str 