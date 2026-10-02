import time
from pathlib import Path
from uuid import uuid4
from urllib.parse import quote

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Response
from fastapi.responses import JSONResponse, StreamingResponse
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
from backend.spreadsheet import parse_spreadsheet
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
    CompareRequest,
    CompareResponse,
    SessionResponse,
    UserResponse,
)
from backend.rag import RAGService
from backend.comparison import DocumentComparisonService
from backend.storage import DocumentStorage, StorageError
from backend.repositories.chunks import ChunkRepository
from backend.repositories.documents import DocumentRepository
from backend.repositories.chat import ChatRepository
from backend.repositories.users import UserRepository
from backend.security import (
    ASK_LIMIT,
    ASK_WINDOW,
    AUTH_LIMIT,
    AUTH_WINDOW,
    GENERAL_LIMIT,
    GENERAL_WINDOW,
    SEARCH_LIMIT,
    SEARCH_WINDOW,
    COMPARE_LIMIT,
    COMPARE_WINDOW,
    UPLOAD_LIMIT,
    UPLOAD_WINDOW,
    get_client_identifier,
    rate_limiter,
)


embedding_service = EmbeddingService()
chunk_repository = ChunkRepository()
document_repository = DocumentRepository()
ingestion_service = IngestionService()
rag_service = RAGService()
comparison_service = DocumentComparisonService()
chat_repository = ChatRepository()
user_repository = UserRepository()
document_storage = DocumentStorage()

bearer_scheme = HTTPBearer(
    auto_error=False,
)


app = FastAPI(
    title="CloudRAG API",
    description="Production-style document intelligence and RAG API",
    version="0.1.0",
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    # Keep API failures readable by browser clients even when an unexpected
    # exception occurs. Without this, Starlette's error response can bypass
    # the normal CORS response path and browsers report only "Failed to fetch".
    origin = request.headers.get("origin")
    headers = {}

    if origin and origin == settings.frontend_url:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Vary"] = "Origin"

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected server error occurred while processing the request."
        },
        headers=headers,
    )


@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start

    REQUEST_COUNT.inc()
    REQUEST_LATENCY.observe(duration)

    return response


@app.middleware("http")
async def security_middleware(request, call_next):
    client_id = get_client_identifier(request)
    path = request.url.path

    if path in {"/auth/login", "/auth/register"}:
        limit = AUTH_LIMIT
        window = AUTH_WINDOW
        key = f"auth:{client_id}"
        message = "Too many authentication attempts. Please try again later."
    elif path in {"/ask", "/ask/stream"}:
        limit = ASK_LIMIT
        window = ASK_WINDOW
        key = f"ask:{client_id}"
        message = "Too many RAG requests. Please try again later."
    elif path == "/documents/compare":
        limit = COMPARE_LIMIT
        window = COMPARE_WINDOW
        key = f"compare:{client_id}"
        message = "Too many comparison requests. Please try again later."
    elif path == "/search":
        limit = SEARCH_LIMIT
        window = SEARCH_WINDOW
        key = f"search:{client_id}"
        message = "Too many search requests. Please try again later."
    elif path == "/documents" and request.method == "POST":
        limit = UPLOAD_LIMIT
        window = UPLOAD_WINDOW
        key = f"upload:{client_id}"
        message = "Too many document uploads. Please try again later."
    else:
        limit = GENERAL_LIMIT
        window = GENERAL_WINDOW
        key = f"general:{client_id}"
        message = "Too many requests. Please try again later."

    if not rate_limiter.allow(key, limit, window):
        response = JSONResponse(
            status_code=429,
            content={"detail": message},
            headers={"Retry-After": str(window)},
        )
    else:
        content_length = request.headers.get("content-length")

        if (
            content_length
            and path == "/documents"
            and request.method == "POST"
        ):
            try:
                content_length_value = int(content_length)
            except ValueError:
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header."},
                )
            else:
                # Multipart/form-data has small framing overhead.
                max_request_bytes = settings.max_upload_size_bytes + (1024 * 1024)

                if content_length_value > max_request_bytes:
                    response = JSONResponse(
                        status_code=413,
                        content={
                            "detail": "Uploaded file is too large. Maximum file size is 20 MB."
                        },
                    )
                else:
                    response = await call_next(request)
        else:
            response = await call_next(request)

    rate_limiter.cleanup()

    if settings.security_headers_enabled:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        if settings.environment.lower() == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
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
# Background document processing
# ---------------------------------------------------------------------------


def process_uploaded_document(
    document_id: int,
    storage_path: str,
    filename: str,
    content_type: str,
) -> None:
    try:
        document_repository.update_progress(
            document_id=document_id,
            status="processing",
            stage="parsing",
            progress=10,
            error_message=None,
        )

        document_storage_content = document_storage.download(storage_path)

        spreadsheet_rows = None
        if Path(filename).suffix.lower() in {".xlsx", ".xlsm", ".csv"}:
            spreadsheet_rows = parse_spreadsheet(
                filename=filename,
                content=document_storage_content,
            )

        text = extract_text(
            filename=filename,
            content=document_storage_content,
        )

        if not text.strip():
            raise DocumentParseError(
                "No readable text was found in the document."
            )

        ingestion_service.process_document(
            document_id=document_id,
            text=text,
            spreadsheet_rows=spreadsheet_rows,
        )
    except Exception as exc:
        message = str(exc).strip() or "Document processing failed."
        try:
            document_repository.update_progress(
                document_id=document_id,
                status="failed",
                stage="failed",
                progress=0,
                error_message=message[:1000],
            )
        except Exception:
            pass


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
            processing_stage=row[5],
            processing_progress=row[6],
            error_message=row[7],
            created_at=row[8],
            updated_at=row[9],
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
        processing_stage=row[5],
        processing_progress=row[6],
        error_message=row[7],
        created_at=row[8],
        updated_at=row[9],
    )


@app.delete(
    "/documents/{document_id}",
)
def delete_document(
    document_id: int,
    user_id: int = Depends(get_current_user_id),
):
    storage_path = document_repository.get_storage_path(
        document_id=document_id,
        user_id=user_id,
    )

    if storage_path:
        try:
            document_storage.delete(storage_path)
        except StorageError as exc:
            raise HTTPException(
                status_code=502,
                detail=str(exc),
            ) from exc

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


@app.get(
    "/documents/{document_id}/download",
)
def download_document(
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

    storage_path = document_repository.get_storage_path(
        document_id=document_id,
        user_id=user_id,
    )

    if not storage_path:
        raise HTTPException(
            status_code=404,
            detail="Original document file is not available.",
        )

    try:
        content = document_storage.download(storage_path)
    except StorageError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    filename = Path(row[1]).name
    encoded_filename = quote(filename)

    return StreamingResponse(
        iter([content]),
        media_type=row[2] or "application/octet-stream",
        headers={
            "Content-Disposition": (
                f"attachment; filename*=UTF-8''{encoded_filename}"
            )
        },
    )


@app.post(
    "/documents",
    status_code=202,
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    filename = Path(file.filename).name
    content = await file.read()

    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail="Uploaded file is too large. Maximum file size is 20 MB.",
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Document must not be empty",
        )

    content_type = (
        file.content_type
        or "application/octet-stream"
    )

    storage_path = (
        f"users/{user_id}/"
        f"{uuid4().hex}-{filename}"
    )

    try:
        document_storage.upload(
            path=storage_path,
            content=content,
            content_type=content_type,
        )
    except StorageError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    try:
        document_id = document_repository.create_document(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            file_size=len(content),
            storage_path=storage_path,
        )

        background_tasks.add_task(
            process_uploaded_document,
            document_id,
            storage_path,
            filename,
            content_type,
        )
    except Exception as exc:
        try:
            document_storage.delete(storage_path)
        except StorageError:
            pass

        raise HTTPException(
            status_code=500,
            detail="Document could not be queued for processing.",
        ) from exc

    return {
        "document_id": document_id,
        "filename": filename,
        "status": "pending",
        "processing_stage": "pending",
        "processing_progress": 0,
        "storage": "stored",
    }


@app.post(
    "/documents/{document_id}/retry",
    response_model=Document,
    status_code=202,
)
def retry_document(
    document_id: int,
    background_tasks: BackgroundTasks,
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

    if row[4] != "failed":
        raise HTTPException(
            status_code=409,
            detail="Only failed documents can be retried.",
        )

    storage_path = document_repository.get_storage_path(
        document_id=document_id,
        user_id=user_id,
    )

    if not storage_path:
        raise HTTPException(
            status_code=404,
            detail="Original document file is not available.",
        )

    document_repository.update_progress(
        document_id=document_id,
        status="pending",
        stage="pending",
        progress=0,
        error_message=None,
    )

    background_tasks.add_task(
        process_uploaded_document,
        document_id,
        storage_path,
        row[1],
        row[2],
    )

    updated = document_repository.get_document(
        document_id=document_id,
        user_id=user_id,
    )

    return Document(
        id=updated[0],
        filename=updated[1],
        content_type=updated[2],
        file_size=updated[3],
        status=updated[4],
        processing_stage=updated[5],
        processing_progress=updated[6],
        error_message=updated[7],
        created_at=updated[8],
        updated_at=updated[9],
    )


@app.post(
    "/documents/compare",
    response_model=CompareResponse,
)
def compare_documents(
    request: CompareRequest,
    user_id: int = Depends(get_current_user_id),
):
    if len(request.document_ids) != 2 or request.document_ids[0] == request.document_ids[1]:
        raise HTTPException(
            status_code=400,
            detail="Select exactly two different documents to compare.",
        )

    rows = [
        document_repository.get_document(document_id, user_id)
        for document_id in request.document_ids
    ]

    if any(row is None for row in rows):
        raise HTTPException(status_code=404, detail="Document not found.")

    if any(row[4] != "completed" for row in rows):
        raise HTTPException(
            status_code=409,
            detail="Both documents must finish processing before they can be compared.",
        )

    try:
        return comparison_service.compare(
            document_ids=request.document_ids,
            user_id=user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        # Return a controlled API error instead of an unhandled 500. This also
        # lets the CORS middleware expose the response to the Vercel frontend.
        raise HTTPException(
            status_code=500,
            detail="Document comparison failed. Check the Render logs for the underlying error.",
        ) from exc


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
            citations=context,
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


@app.post("/ask/stream")
def ask_stream(
    request: AskRequest,
    user_id: int = Depends(get_current_user_id),
):
    """Stream an answer as Server-Sent Events (SSE)."""
    start = time.perf_counter()
    RAG_REQUEST_COUNT.inc()

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

    try:
        context, answer_chunks = rag_service.answer_stream(
            question=request.question,
            user_id=user_id,
            limit=request.limit,
            document_ids=request.document_ids or None,
            session_id=session_id,
        )
    except LLMGenerationError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    if session_id is None:
        session_id = chat_repository.create_session(
            user_id=user_id,
            title=generate_session_title(request.question),
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
            title=generate_session_title(request.question),
        )

    chat_repository.add_message(
        session_id=session_id,
        user_id=user_id,
        role="user",
        content=request.question,
    )

    def event_stream():
        answer_parts = []

        import json

        yield (
            "event: meta\n"
            f"data: {json.dumps({'session_id': session_id, 'citations': context})}\n\n"
        )

        try:
            for chunk in answer_chunks:
                if not chunk:
                    continue
                answer_parts.append(chunk)
                yield (
                    "event: token\n"
                    f"data: {json.dumps({'text': chunk})}\n\n"
                )

            answer = "".join(answer_parts).strip()

            if not answer:
                raise LLMGenerationError(
                    "The language model returned an empty answer."
                )

            chat_repository.add_message(
                session_id=session_id,
                user_id=user_id,
                role="assistant",
                content=answer,
                citations=context,
            )

            yield (
                "event: done\n"
                f"data: {json.dumps({'session_id': session_id})}\n\n"
            )
        except Exception as exc:
            yield (
                "event: error\n"
                f"data: {json.dumps({'detail': str(exc)})}\n\n"
            )
        finally:
            duration = time.perf_counter() - start
            RAG_REQUEST_LATENCY.observe(duration)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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
            citations=row[4] or [],
            created_at=row[5],
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