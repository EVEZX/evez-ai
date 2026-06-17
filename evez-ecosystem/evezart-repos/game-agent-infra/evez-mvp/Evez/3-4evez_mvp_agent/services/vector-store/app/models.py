from pydantic import BaseModel, Field
from typing import Dict, Any

class EmbedRequest(BaseModel):
    session_id: str
    kind: str = "note"
    t_ms: int
    text: str = Field(min_length=1)
    metadata: Dict[str, Any] = {}

class SearchRequest(BaseModel):
    session_id: str
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
