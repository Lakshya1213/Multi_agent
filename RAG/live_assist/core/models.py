from __future__ import annotations

from enum import Enum
from typing import Any, Optional, Union

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class Speaker(str, Enum):
    CUSTOMER = "Customer"
    WORKER = "Worker"
    ASSISTANT = "Assistant"
    UNKNOWN = "Unknown"


class ProductType(str, Enum):
    ILTS = "ILTS"
    FGF = "FGF"
    FINRAKSHAK = "FinRakshak"
    BHARAT_BOND = "BharatBond"
    SWP = "SWP"


class RewriteQuestion(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rewriten_question: str = Field(
        default="",
        validation_alias=AliasChoices("rewriten_question", "question"),
        serialization_alias="rewriten_question",
    )
    product: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str = ""


class LiveFeedbackWebhookBody(BaseModel):
    transcript: str
    speaker: str
    timestamp: Optional[Union[int, float, str]] = None
    call_id: str
    hasInterruptions: bool = False
    raw_text: Optional[str] = None
    translated_text: Optional[str] = None
    source: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LiveFeedbackRequest(BaseModel):
    body: LiveFeedbackWebhookBody


class ManualQuestionRequest(BaseModel):
    call_id: str
    question: str
    timestamp: Optional[Union[int, float, str]] = None
    source: str = "agent_manual_question"
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentInfo(BaseModel):
    document_id: str
    user_id: str
    filename: str
    status: str = "ingesting"
    uploaded_at: float
    chunk_count: int = 0
    total_tokens: int = 0
    error: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentUploadResponse(BaseModel):
    status: str
    job_id: str
    document_id: str
    filename: str
    message: str


class JobStage(BaseModel):
    stage: str
    message: str
    ts: float


class JobStatusResponse(BaseModel):
    job_id: str
    document_id: str
    user_id: str
    filename: str
    status: str
    submitted_at: float
    updated_at: float
    stages: list[JobStage] = Field(default_factory=list)
    chunk_count: int = 0
    total_tokens: int = 0
    error: Optional[str] = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo] = Field(default_factory=list)


class TranscriptTurn(BaseModel):
    session_id: str
    speaker: Speaker
    timestamp: float
    raw_text: str
    translated_text: Optional[str] = None
    source: str = "unknown"
    triggered_live_assist: bool = False
    workflow_target: str = "stored_only"
    product: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def display_text(self) -> str:
        return (self.translated_text or self.raw_text).strip()


class AssistResult(BaseModel):
    status: str
    answer: str = ""
    summary_result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
