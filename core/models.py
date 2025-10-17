from typing import List, Optional
from pydantic import BaseModel

class Attachment(BaseModel):
    name: str
    url: str

class TaskRequest(BaseModel):
    email: str
    secret: str
    task: str
    round: int
    nonce: str
    brief: Optional[str] = None
    checks: Optional[List[str]] = []
    evaluation_url: str
    attachments: Optional[List[Attachment]] = []
