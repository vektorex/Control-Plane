from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "developer"] = Field(
        description="Role of the message author"
    )
    content: str = Field(min_length=1, description="Text content of the message")


class LLMGenerateRequest(BaseModel):
    model: str = Field(min_length=1, description="Target model identifier, e.g. gpt-4o-mini")
    messages: List[ChatMessage] = Field(min_length=1, description="Sequential chat message history")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, gt=0, description="Maximum completion tokens to generate")
    stream: Optional[bool] = Field(default=False, description="Whether to stream responses")


class TokenUsage(BaseModel):
    input_tokens: Optional[int] = Field(default=None, description="Number of prompt/input tokens")
    output_tokens: Optional[int] = Field(default=None, description="Number of completion/output tokens")
    total_tokens: Optional[int] = Field(default=None, description="Total tokens consumed")


class LLMGenerateResponse(BaseModel):
    content: str = Field(description="Generated completion text content")
    model: str = Field(description="Model that generated this completion")
    provider: Optional[str] = Field(default=None, description="Provider identifier, e.g. openai")
    usage: Optional[TokenUsage] = Field(default=None, description="Token usage statistics if available")
    finish_reason: Optional[str] = Field(default=None, description="Generation termination reason, e.g. stop, length")


class LLMStreamChunk(BaseModel):
    content: str = Field(default="", description="Delta text fragment")
    delta: Optional[str] = Field(default=None, description="Optional delta text")
    model: Optional[str] = Field(default="gpt-4o-mini", description="Model producing the stream")
    provider: Optional[str] = Field(default=None, description="Provider identifier")
    index: Optional[int] = Field(default=None, description="Chunk index")
    is_finished: bool = Field(default=False, description="Whether this is the terminal chunk")
    usage: Optional[TokenUsage] = Field(default=None, description="Final token usage statistics if available")
    finish_reason: Optional[str] = Field(default=None, description="Reason stream finished")
