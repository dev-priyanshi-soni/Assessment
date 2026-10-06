from datetime import date
from typing import Any
from pydantic import BaseModel, Field

class Caller(BaseModel):
    caller_id: str
    tenant: str
    role: str

class AnswerRequest(BaseModel):
    question: str = Field(min_length=1)
    as_of: date

class Citation(BaseModel):
    chunk_id: str
    quote: str

class AnswerResponse(BaseModel):
    status: str
    answer: str | None
    citations: list[Citation]

class Extracted(BaseModel):
    benefit: str | None = None
    amount: float | None = None
    currency: str | None = None
    reference: str | None = None

class BatchDocument(BaseModel):
    document_id: str
    filename: str

class BatchMetadata(BaseModel):
    batch_id: str
    as_of: date
    documents: list[BatchDocument]

class BatchResult(BaseModel):
    document_id: str
    processing_status: str
    extracted: Extracted | None = None
    field_evidence: dict[str, str] = {}
    policy: AnswerResponse | None = None
    review_required: bool = True
    issues: list[str] = []
    duplicate_of: str | None = None
    error: dict[str, str] | None = None
