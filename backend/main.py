import time

from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST

from backend.auth import (
    create_access_token,
    hash_password,
    require_bearer_token,
    verify_password,
)
from backend.config import settings
from backend.document_parser import (
    DocumentParseError,
    extract_text,
)
from backend.embedding import EmbeddingService
from backend.health import get_health_status, is_ready
from backend.ingestion import IngestionService
from backend.llm import LLMGenerationError
from backend.metrics import (
    get_metrics,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    RAG_REQUEST_COUNT,
    RAG_REQUEST_LATENCY,
)
from backend.models import (
    AskRequest,
    AskResponse,
    ChatMessageResponse,
    CreateSessionRequest,
    Document,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    SearchRequest,
    SearchResult,
    SessionResponse,
    UserResponse,
)
from backend.rag import RAGService
from backend.repositories.chunks import ChunkRepository
from backend.repositories.documents import DocumentRepository
from backend.repositories.chat import ChatRepository
from backend.repositories.users import UserRepository


embedding_service = EmbeddingService()
chunk_repository = ChunkRepository()
document_repository = DocumentRepository()
ingestion_service = IngestionService()
rag_service = RAGService()
chat_repository = ChatRepository()
user_repository = UserRepository()

bearer_scheme = HTTPBearer(
    auto_error=False,
)


app = FastAPI(
    title="CloudRAG API",
    description="Production-style document intelligence and RAG API",
    version="0.1.0",
)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start

    REQUEST_COUNT.inc()
    REQUEST_LATENCY.observe(duration)

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> int:
    return require_bearer_token(
        credentials=credentials,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def get_user_response(user_row) -> UserResponse:
    return UserResponse(
        id=user_row[0],
        email=user_row[1],
        created_at=user_row[3],
        updated_at=user_row[4],
    )


@app.get("/health")
def health_check():
    return {
        "service": settings.app_name,
        "environment": settings.environment,
        **get_health_status(),
    }


@app.get("/live")
def liveness_check():
    return {"status": "alive"}


@app.get("/ready")
def readiness_check():
    if not is_ready():
        raise HTTPException(
            status_code=503,
            detail="Required dependencies are not ready",
        )

    return {"status": "ready"}


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


@app.post(
    "/auth/register",
    response_model=LoginResponse,
    status_code=201,
)
def register(request: RegisterRequest):
    email = request.email.strip().lower()

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required.",
        )

    existing_user = user_repository.get_by_email(email)

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    try:
        password_hash = hash_password(request.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    try:
        user_id = user_repository.create_user(
            email=email,
            password_hash=password_hash,
        )
    except Exception as exc:
        # Handles a possible race against the UNIQUE email constraint.
        if user_repository.get_by_email(email):
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists.",
            ) from exc

        raise HTTPException(
            status_code=500,
            detail="Unable to create account.",
        ) from exc

    user = user_repository.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=500,
            detail="Account was created but could not be loaded.",
        )

    access_token = create_access_token(
        user_id=user_id,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.jwt_access_token_expire_minutes,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=get_user_response(user),
    )


@app.post(
    "/auth/login",
    response_model=LoginResponse,
)
def login(request: LoginRequest):
    email = request.email.strip().lower()

    user = user_repository.get_by_email(email)

    if not user or not verify_password(
        request.password,
        user[2],
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    access_token = create_access_token(
        user_id=user[0],
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.jwt_access_token_expire_minutes,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=get_user_response(user),
    )


@app.get(
    "/auth/me",
    response_model=UserResponse,
)
def get_current_user(
    user_id: int = Depends(get_current_user_id),
):
    user = user_repository.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User account no longer exists.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return get_user_response(user)


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


@app.get(
    "/documents",
    response_model=list[Document],
)
def list_documents(
    user_id: int = Depends(get_current_user_id),
):
    rows = document_repository.list_documents(
        user_id=user_id,
    )

    return [
        Document(
            id=row[0],
            filename=row[1],
            content_type=row[2],
            file_size=row[3],
            status=row[4],
            created_at=row[5],
            updated_at=row[6],
        )
        for row in rows
    ]


@app.get(
    "/documents/{document_id}",
    response_model=Document,
)
def get_document(
    document_id: int,
    user_id: int = Depends(get_current_user_id),
):
    row = document_repository.get_document(
        document_id=document_id,
        user_id=user_id,
    )

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return Document(
        id=row[0],
        filename=row[1],
        content_type=row[2],
        file_size=row[3],
        status=row[4],
        created_at=row[5],
        updated_at=row[6],
    )


@app.delete(
    "/documents/{document_id}",
)
def delete_document(
    document_id: int,
    user_id: int = Depends(get_current_user_id),
):
    deleted = document_repository.delete_document(
        document_id=document_id,
        user_id=user_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return {
        "document_id": document_id,
        "status": "deleted",
    }


@app.post(
    "/documents",
)
async def upload_document(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Document must not be empty",
        )

    try:
        text = extract_text(
            filename=file.filename,
            content=content,
        )
    except DocumentParseError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail=(
                "No readable text was found in the document."
            ),
        )

    try:
        document_id = ingestion_service.ingest_text(
            user_id=user_id,
            filename=file.filename,
            content_type=(
                file.content_type
                or "application/octet-stream"
            ),
            text=text,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document ingestion failed: {exc}",
        ) from exc

    return {
        "document_id": document_id,
        "filename": file.filename,
        "status": "completed",
    }


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@app.post(
    "/search",
    response_model=list[SearchResult],
)
def search(
    request: SearchRequest,
    user_id: int = Depends(get_current_user_id),
):
    document_ids = request.document_ids or None

    if document_ids:
        owned_document_ids = []

        for document_id in document_ids:
            document = document_repository.get_document(
                document_id=document_id,
                user_id=user_id,
            )

            if document:
                owned_document_ids.append(document_id)

        if not owned_document_ids:
            return []

        document_ids = owned_document_ids

    query_embedding = embedding_service.embed(
        request.query
    )

    rows = chunk_repository.search_chunks(
        embedding=query_embedding,
        user_id=user_id,
        limit=request.limit,
        document_ids=document_ids,
    )

    return [
        SearchResult(
            chunk_id=row[0],
            document_id=row[1],
            chunk_index=row[2],
            content=row[3],
            distance=float(row[4]),
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# RAG
# ---------------------------------------------------------------------------


@app.post(
    "/ask",
    response_model=AskResponse,
)
def ask(
    request: AskRequest,
    user_id: int = Depends(get_current_user_id),
):
    start = time.perf_counter()

    RAG_REQUEST_COUNT.inc()

    try:
        session_id = request.session_id

        if session_id is not None:
            existing_session = chat_repository.get_session(
                session_id=session_id,
                user_id=user_id,
            )

            if not existing_session:
                raise HTTPException(
                    status_code=404,
                    detail="Session not found",
                )

        answer, context = rag_service.answer(
            question=request.question,
            user_id=user_id,
            limit=request.limit,
            document_ids=request.document_ids or None,
            session_id=session_id,
        )

        if session_id is None:
            session_id = chat_repository.create_session(
                user_id=user_id,
                title=generate_session_title(
                    request.question
                ),
            )

        session = chat_repository.get_session(
            session_id=session_id,
            user_id=user_id,
        )

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found",
            )

        if session[1] == "New Chat":
            chat_repository.update_title(
                session_id=session_id,
                user_id=user_id,
                title=generate_session_title(
                    request.question
                ),
            )

        chat_repository.add_message(
            session_id=session_id,
            user_id=user_id,
            role="user",
            content=request.question,
        )

        chat_repository.add_message(
            session_id=session_id,
            user_id=user_id,
            role="assistant",
            content=answer,
        )

        return AskResponse(
            answer=answer,
            citations=context,
            session_id=session_id,
        )

    except LLMGenerationError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    finally:
        duration = time.perf_counter() - start
        RAG_REQUEST_LATENCY.observe(duration)


# ---------------------------------------------------------------------------
# Chat sessions
# ---------------------------------------------------------------------------


@app.post(
    "/sessions",
    response_model=SessionResponse,
)
def create_session(
    request: CreateSessionRequest,
    user_id: int = Depends(get_current_user_id),
):
    session_id = chat_repository.create_session(
        user_id=user_id,
        title=request.title.strip() or "New Chat",
    )

    session = chat_repository.get_session(
        session_id=session_id,
        user_id=user_id,
    )

    return SessionResponse(
        id=session[0],
        title=session[1],
        created_at=session[2],
        updated_at=session[3],
    )


@app.get(
    "/sessions",
    response_model=list[SessionResponse],
)
def list_sessions(
    user_id: int = Depends(get_current_user_id),
):
    rows = chat_repository.list_sessions(
        user_id=user_id,
    )

    return [
        SessionResponse(
            id=row[0],
            title=row[1],
            created_at=row[2],
            updated_at=row[3],
        )
        for row in rows
    ]


@app.get(
    "/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
)
def get_session_messages(
    session_id: int,
    user_id: int = Depends(get_current_user_id),
):
    session = chat_repository.get_session(
        session_id=session_id,
        user_id=user_id,
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    rows = chat_repository.get_messages(
        session_id=session_id,
        user_id=user_id,
    )

    return [
        ChatMessageResponse(
            id=row[0],
            session_id=row[1],
            role=row[2],
            content=row[3],
            created_at=row[4],
        )
        for row in rows
    ]


@app.delete(
    "/sessions/{session_id}",
)
def delete_session(
    session_id: int,
    user_id: int = Depends(get_current_user_id),
):
    deleted = chat_repository.delete_session(
        session_id=session_id,
        user_id=user_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    return {
        "session_id": session_id,
        "deleted": True,
    }


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


@app.get("/metrics")
def metrics():
    return Response(
        content=get_metrics(),
        media_type=CONTENT_TYPE_LATEST,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def generate_session_title(question: str) -> str:
    title = " ".join(question.strip().split())

    if not title:
        return "New Chat"

    if len(title) <= 60:
        return title.rstrip("?.!")

    return title[:57].rstrip() + "..."