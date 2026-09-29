from datetime import datetime

from pydantic import BaseModel, Field


class Document(BaseModel):
    id: int
    filename: str
    content_type: str
    file_size: int
    status: str
    created_at: datetime
    updated_at: datetime


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    chunk_id: int
    document_id: int
    chunk_index: int
    content: str
    distance: float

class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=10)


class Citation(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    chunk_index: int
    content: str


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]