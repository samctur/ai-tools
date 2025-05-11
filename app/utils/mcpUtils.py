import uuid
from datetime import datetime
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field


class Context(BaseModel):
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "api"
    model_type: str


class MCPMessageWrapper(BaseModel):
    task: str  # Topic e.g. "generate.image", "embed.vector"
    input: Dict[str, Any]
    input_type: str
    output_type: Any
    context: Context
    metadata: Optional[Dict[str, Any]] = {}
    output: Optional[Dict[str, Any]] = None
