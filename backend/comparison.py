from backend.llm import LLMService
from backend.rag import RAGService


class DocumentComparisonService:
    TOPICS = [
        "purpose and overall summary",
        "main features capabilities or functions",
        "requirements architecture process or implementation details",
        "performance cost metrics or quantitative information",
        "limitations risks assumptions or important caveats",
    ]

    def __init__(self):
        self.rag_service = RAGService()
        self.llm_service = LLMService()

    def compare(self, document_ids: list[int], user_id: int) -> dict:
        if len(document_ids) != 2 or document_ids[0] == document_ids[1]:
            raise ValueError("Select exactly two different documents to compare.")

        contexts = {}
        seen = set()

        for document_id in document_ids:
            document_chunks = []
            for topic in self.TOPICS:
                for item in self.rag_service.retrieve(
                    question=topic,
                    user_id=user_id,
                    limit=3,
                    document_ids=[document_id],
                ):
                    key = item["chunk_id"]
                    if key not in seen:
                        seen.add(key)
                        document_chunks.append(item)

            contexts[document_id] = document_chunks[:12]

        filenames = {}
        for document_id in document_ids:
            filename = self.rag_service.document_repository.get_filename(
                document_id=document_id,
                user_id=user_id,
            )
            if not filename:
                raise ValueError("One or both selected documents were not found.")
            filenames[document_id] = filename

        prompt_parts = [
            "Compare exactly these two documents using ONLY the supplied evidence.",
            "Do not invent facts, calculations, or details that are absent from the evidence.",
            "If a document has no supplied excerpts, explicitly state that the document contains no indexed text available for comparison.",
            "Do not treat missing evidence as a substantive similarity or difference.",
            "Write a useful but concise Markdown comparison using exactly these headings:",
            "# Overview",
            "# Similarities",
            "# Differences",
            "# Important Details",
            "# Limitations",
            "Under Similarities and Differences, use bullet points. If there are no supported similarities, say: No supported similarities were found in the supplied evidence.",
            "If there are no supported differences, say: No supported differences were found in the supplied evidence.",
            "Under Limitations, mention missing/empty evidence when applicable.",
            "Do not include a Sources section; citations are attached separately by the application.",
            "",
        ]

        for document_id in document_ids:
            prompt_parts.append(f"DOCUMENT: {filenames[document_id]}")
            if not contexts[document_id]:
                prompt_parts.append("[No indexed text available for this document]")
            else:
                for index, item in enumerate(contexts[document_id], start=1):
                    prompt_parts.append(
                        f"[Excerpt {index} | chunk {item['chunk_index']}]:\n{item['content'][:1400]}"
                    )
            prompt_parts.append("")

        answer = self.llm_service.generate(
            "\n".join(prompt_parts),
            max_output_tokens=700,
        )

        citations = []
        for document_id in document_ids:
            for item in contexts[document_id]:
                citations.append(
                    {
                        "chunk_id": item["chunk_id"],
                        "document_id": item["document_id"],
                        "filename": item["filename"],
                        "chunk_index": item["chunk_index"],
                        "content": item["content"],
                        "distance": item["distance"],
                    }
                )

        return {
            "answer": answer,
            "citations": citations,
            "documents": [
                {"id": document_id, "filename": filenames[document_id]}
                for document_id in document_ids
            ],
        }
