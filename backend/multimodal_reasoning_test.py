import sys
import types
import unittest
from unittest.mock import Mock

# RAG repository modules import psycopg at module load time. These tests only
# exercise multimodal selection/formatting and never open a database connection.
sys.modules.setdefault("psycopg", types.SimpleNamespace(connect=None))

from backend.llm import LLMService
from backend.rag import RAGService


class MultiImageReasoningTests(unittest.TestCase):
    def test_collects_distinct_figures_from_multiple_retrieved_chunks(self):
        service = RAGService.__new__(RAGService)
        service.document_image_repository = Mock()
        service.document_storage = Mock()

        # id, document_id, mime, path, width, height, description,
        # created_at, source_label, image_index
        rows = [
            (11, 7, "image/png", "docs/fig-1.png", 800, 600, "Figure one", None, "Embedded image 1", 1),
            (12, 7, "image/png", "docs/fig-2.png", 800, 600, "Figure two", None, "Embedded image 2", 2),
        ]
        service.document_image_repository.list_by_document.return_value = rows
        service.document_storage.download.side_effect = [b"one", b"two"]

        context = [
            {
                "image": True,
                "document_id": 7,
                "filename": "report.pdf",
                "content": "[Embedded image 1 — page 2] Figure one",
            },
            {
                "image": True,
                "document_id": 7,
                "filename": "report.pdf",
                "content": "[Embedded image 2 — page 4] Figure two",
            },
        ]

        images = service._collect_relevant_images(context, max_images=4)

        self.assertEqual([image["image_id"] for image in images], [11, 12])
        self.assertEqual([image["image_index"] for image in images], [1, 2])
        self.assertEqual([image["bytes"] for image in images], [b"one", b"two"])

    def test_llm_labels_each_visual_input(self):
        service = LLMService.__new__(LLMService)
        parts = service._build_parts(
            "Answer the question.",
            [
                {
                    "mime_type": "image/png",
                    "bytes": b"first",
                    "label": "Embedded image 1",
                    "filename": "report.pdf",
                },
                {
                    "mime_type": "image/png",
                    "bytes": b"second",
                    "label": "Embedded image 2",
                    "filename": "report.pdf",
                },
            ],
        )

        self.assertEqual(parts[0]["text"], "VISUAL EVIDENCE 1: Embedded image 1 from report.pdf. Use this image as distinct visual evidence.")
        self.assertEqual(parts[2]["text"], "VISUAL EVIDENCE 2: Embedded image 2 from report.pdf. Use this image as distinct visual evidence.")
        self.assertEqual(parts[-1]["text"], "Answer the question.")


if __name__ == "__main__":
    unittest.main()
