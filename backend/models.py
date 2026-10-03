from datetime import datetime

from pydantic import BaseModel, Field


class Document(BaseModel):
    id: int
    filename: str
    content_type: str
    file_size: int
    status: str
    processing_stage: str
    processing_progress: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
    )
    document_ids: list[int] = Field(
        default_factory=list
    )


class SearchResult(BaseModel):
    chunk_id: int
    document_id: int
    chunk_index: int
    content: str
    distance: float


class AskRequest(BaseModel):
    model: str | None = None

    question: str = Field(min_length=1)

    limit: int = Field(
        default=5,
        ge=1,
        le=10,
    )

    document_ids: list[int] = Field(
        default_factory=list
    )

    session_id: int | None = None


class CitationImage(BaseModel):
    image_id: int
    source_label: str | None = None
    image_index: int
    mime_type: str
    width: int | None = None
    height: int | None = None


class Citation(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    chunk_index: int
    content: str
    distance: float
    image_evidence: list[CitationImage] = Field(default_factory=list)


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    session_id: int


class ChatSession(BaseModel):
    id: int
    title: str
    model: str
    created_at: datetime
    updated_at: datetime


class ChatMessage(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime


class CreateSessionRequest(BaseModel):
    title: str = Field(
        default="New Chat",
        min_length=1,
        max_length=200,
    )

    model: str | None = None


class ModelSelectionRequest(BaseModel):
    model: str = Field(min_length=1, max_length=100)


class SessionResponse(BaseModel):
    id: int
    title: str
    model: str
    created_at: datetime
    updated_at: datetime


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime


class User(BaseModel):
    id: int
    email: str
    created_at: datetime
    updated_at: datetime


class RegisterRequest(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=320,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class LoginRequest(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=320,
    )

    password: str = Field(
        min_length=1,
        max_length=128,
    )


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    updated_at: datetime


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class CompareRequest(BaseModel):
    model: str | None = None
    document_ids: list[int] = Field(min_length=2, max_length=2)


class CompareCitation(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    chunk_index: int
    content: str
    distance: float


class CompareResponse(BaseModel):
    answer: str
    citations: list[CompareCitation]
    documents: list[dict]
