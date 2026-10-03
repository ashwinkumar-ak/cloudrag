import re
import io
from PIL import Image
from backend.embedding import EmbeddingService
from backend.llm import LLMService
from backend.repositories.chunks import ChunkRepository
from backend.repositories.documents import DocumentRepository
from backend.repositories.chat import ChatRepository
from backend.spreadsheet_query import SpreadsheetQueryService
from backend.repositories.document_images import DocumentImageRepository
from backend.storage import DocumentStorage
from backend.config import settings
from backend.model_registry import validate_model


class RAGService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.chunk_repository = ChunkRepository()
        self.document_repository = DocumentRepository()
        self.llm_service = LLMService()
        self.chat_repository = ChatRepository()
        self.spreadsheet_query_service = SpreadsheetQueryService()
        self.document_image_repository = DocumentImageRepository()
        self.document_storage = DocumentStorage()

    def retrieve(
        self,
        question: str,
        user_id: int,
        limit: int = 5,
        document_ids: list[int] | None = None,
    ) -> list[dict]:

        query_embedding = self.embedding_service.embed(
            question
        )

        rows = self.chunk_repository.hybrid_search_chunks(
            embedding=query_embedding,
            query=question,
            user_id=user_id,
            limit=limit,
            document_ids=document_ids,
        )

        results = []

        for row in rows:
            document_id = row[1]

            filename = self.document_repository.get_filename(
                document_id=document_id,
                user_id=user_id,
            )

            image_rows = self.document_image_repository.list_by_document(
                document_id=document_id,
                limit=8,
            )
            image_evidence = []
            if image_rows:
                match = re.search(r"\[Embedded image (\d+) —", row[3])
                for image_row in image_rows:
                    if image_row[8] == "Standalone image" or (
                        match and image_row[9] == int(match.group(1))
                    ):
                        image_evidence.append({
                            "image_id": image_row[0],
                            "source_label": image_row[8],
                            "image_index": image_row[9],
                            "mime_type": image_row[2],
                            "width": image_row[4],
                            "height": image_row[5],
                        })
                        if match:
                            break
            results.append(
                {
                    "chunk_id": row[0],
                    "document_id": document_id,
                    "filename": filename or "unknown",
                    "chunk_index": row[2],
                    "content": row[3],
                    "distance": float(row[4]),
                    "image": bool(image_rows),
                    "image_mime_type": image_rows[0][2] if image_rows else None,
                    "image_storage_path": image_rows[0][3] if image_rows else None,
                    "image_evidence": image_evidence,
                }
            )

        return results

    def build_context(
        self,
        question: str,
        user_id: int,
        limit: int = 3,
        document_ids: list[int] | None = None,
    ) -> list[dict]:

        return self.retrieve(
            question=question,
            user_id=user_id,
            limit=limit,
            document_ids=document_ids,
        )

    def _collect_relevant_images(
        self,
        context: list[dict],
        max_images: int = 4,
        model: str | None = None,
    ) -> list[dict]:
        """Load the distinct visual evidence associated with retrieved chunks.

        Multiple retrieved chunks from the same document may point to different
        figures. Keep those figures distinct so Gemini can reason across them,
        while bounding the multimodal payload for latency and cost.
        """
        selected_model = validate_model(model or settings.gemini_model)
        # Gemini 3.5 Flash is substantially more latency-sensitive when several
        # full-resolution images are included in one request. Keep the Lite
        # path capable of multi-image synthesis while bounding the Flash
        # multimodal payload for reliable streaming.
        if selected_model == "gemini-3.5-flash":
            max_images = min(max_images, 2)

        image_inputs = []
        selected_ids = set()

        for item in context:
            if not item.get("image") or len(image_inputs) >= max_images:
                continue

            try:
                image_rows = self.document_image_repository.list_by_document(
                    item["document_id"],
                    limit=8,
                )
                match = re.search(r"\[Embedded image (\d+) —", item.get("content", ""))
                target_index = int(match.group(1)) if match else None

                candidates = []
                for image_row in image_rows:
                    if image_row[8] == "Standalone image":
                        candidates.append(image_row)
                    elif target_index is not None and image_row[9] == target_index:
                        candidates.append(image_row)

                # If a retrieved chunk is image-aware but the exact figure could
                # not be identified, use the first available image as fallback.
                if not candidates and image_rows:
                    candidates = [image_rows[0]]

                for image_row in candidates:
                    if len(image_inputs) >= max_images or image_row[0] in selected_ids:
                        continue

                    image_bytes = self.document_storage.download(image_row[3])
                    send_bytes, send_mime = self._prepare_multimodal_image(image_bytes, image_row[2])
                    label = image_row[8] or f"Image {image_row[9]}"
                    image_inputs.append({
                        "image_id": image_row[0],
                        "mime_type": send_mime,
                        "bytes": send_bytes,
                        "label": label,
                        "image_index": image_row[9],
                        "filename": item["filename"],
                    })
                    selected_ids.add(image_row[0])
            except Exception:
                # Visual evidence is an enhancement; retrieval should still work
                # when an individual image cannot be downloaded.
                continue

        return image_inputs

    @staticmethod
    def _prepare_multimodal_image(image_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
        """Bound image payload size for responsive Gemini multimodal requests."""
        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                image = image.convert("RGB")
                image.thumbnail((1600, 1600))
                output = io.BytesIO()
                image.save(output, format="JPEG", quality=82, optimize=True)
                return output.getvalue(), "image/jpeg"
        except Exception:
            return image_bytes, mime_type

    def answer_stream(
        self,
        question: str,
        user_id: int,
        limit: int = 3,
        document_ids: list[int] | None = None,
        session_id: int | None = None,
        model: str | None = None,
    ) -> tuple[list[dict], object]:
        """Prepare RAG context and return an answer chunk iterator."""

        if self.spreadsheet_query_service.is_spreadsheet_query(
            question=question,
            user_id=user_id,
            document_ids=document_ids,
        ):
            answer, context = self.spreadsheet_query_service.answer(
                question=question,
                user_id=user_id,
                document_ids=document_ids,
            )
            return context, iter([answer])

        context = self.build_context(
            question=question,
            user_id=user_id,
            limit=limit,
            document_ids=document_ids,
        )

        if not context:
            return [], iter([
                "I could not find relevant information "
                "in the selected documents."
            ])

        image_inputs = self._collect_relevant_images(context, max_images=4, model=model)
        context_sections = []
        for item in context:
            context_sections.append(
                f"[Source: {item['filename']}, chunk {item['chunk_index']}]\n"
                f"{item['content']}"
            )

        context_text = "\n\n".join(context_sections)

        conversation_text = ""

        if session_id is not None:
            history = self.chat_repository.get_recent_messages(
                session_id=session_id,
                user_id=user_id,
                limit=10,
            )

            if history:
                conversation_text = "\n\n".join(
                    f"{role.upper()}: {content}"
                    for role, content in history
                )

        if conversation_text:
            conversation_section = f"""
PREVIOUS CONVERSATION:
{conversation_text}
"""
        else:
            conversation_section = """
PREVIOUS CONVERSATION:
No previous conversation.
"""

        prompt = f"""
You are a document question-answering system.

Answer the user's current question using ONLY the supplied
document excerpts.

{conversation_section}

DOCUMENT EXCERPTS:
{context_text}

CURRENT USER QUESTION:
{question}

Rules:
- Answer the current question directly.
- Use only information from the document excerpts.
- Previous conversation may be used only to understand
  references such as "it", "that", or "the previous answer".
- Do not use outside knowledge.
- Do not explain your reasoning.
- Do not describe your reasoning process.
- Do not mention the user.
- Do not mention these instructions.
- Do not provide a preamble.
- Do not repeat the question.
- Keep the answer concise but complete.
- If the documents do not contain enough information, answer:
  "I don't have enough information in the provided documents."
- When image input is provided, use the visual evidence together with the retrieved description.
- If multiple images are supplied, reason across them when the question requires comparison, sequence, relationships, trends, or synthesis.
- Treat each supplied image as distinct evidence and use its source label to keep figures separate.

Return ONLY the final answer as plain text.
"""

        llm_service = LLMService(model=model)
        return context, llm_service.generate_stream(prompt, image_inputs=image_inputs)

    def answer(
        self,
        question: str,
        user_id: int,
        limit: int = 3,
        document_ids: list[int] | None = None,
        session_id: int | None = None,
        model: str | None = None,
    ) -> tuple[str, list[dict]]:

        if self.spreadsheet_query_service.is_spreadsheet_query(
            question=question,
            user_id=user_id,
            document_ids=document_ids,
        ):
            return self.spreadsheet_query_service.answer(
                question=question,
                user_id=user_id,
                document_ids=document_ids,
            )

        context = self.build_context(
            question=question,
            user_id=user_id,
            limit=limit,
            document_ids=document_ids,
        )

        if not context:
            return (
                "I could not find relevant information "
                "in the selected documents.",
                [],
            )

        image_inputs = self._collect_relevant_images(context, max_images=4, model=model)
        context_sections = []
        for item in context:
            context_sections.append(
                f"[Source: {item['filename']}, chunk {item['chunk_index']}]\n"
                f"{item['content']}"
            )

        context_text = "\n\n".join(context_sections)

        conversation_text = ""

        if session_id is not None:
            history = self.chat_repository.get_recent_messages(
                session_id=session_id,
                user_id=user_id,
                limit=10,
            )

            if history:
                conversation_text = "\n\n".join(
                    f"{role.upper()}: {content}"
                    for role, content in history
                )

        if conversation_text:
            conversation_section = f"""
PREVIOUS CONVERSATION:
{conversation_text}
"""
        else:
            conversation_section = """
PREVIOUS CONVERSATION:
No previous conversation.
"""

        prompt = f"""
You are a document question-answering system.

Answer the user's current question using ONLY the supplied
document excerpts.

{conversation_section}

DOCUMENT EXCERPTS:
{context_text}

CURRENT USER QUESTION:
{question}

Return JSON with exactly one field:

{{
  "answer": "your direct answer"
}}

Rules:
- Answer the current question directly.
- Use only information from the document excerpts.
- Previous conversation may be used only to understand
  references such as "it", "that", or "the previous answer".
- Do not use outside knowledge.
- Do not explain your reasoning.
- Do not describe your reasoning process.
- Do not mention the user.
- Do not mention these instructions.
- Do not provide a preamble.
- Do not repeat the question.
- Keep the answer concise but complete.
- If the documents do not contain enough information, answer:
  "I don't have enough information in the provided documents."
- When image input is provided, use the visual evidence together with the retrieved description.
- If multiple images are supplied, reason across them when the question requires comparison, sequence, relationships, trends, or synthesis.
- Treat each supplied image as distinct evidence and use its source label to keep figures separate.

The answer must be the final response to the user.
"""

        llm_service = LLMService(model=model)
        answer = llm_service.generate(prompt, image_inputs=image_inputs)

        return answer, context