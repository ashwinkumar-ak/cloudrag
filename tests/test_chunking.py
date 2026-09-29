from backend.chunking import TextChunker


def test_empty_text_returns_no_chunks():
    chunker = TextChunker()

    assert chunker.split("") == []


def test_short_text_returns_one_chunk():
    chunker = TextChunker(chunk_size=100)

    text = "CloudRAG is a document intelligence platform."

    chunks = chunker.split(text)

    assert chunks == [text]


def test_sentences_are_preserved():
    chunker = TextChunker(
        chunk_size=65,
        overlap_sentences=1,
    )

    text = (
        "CloudRAG stores documents. "
        "Documents are converted into chunks. "
        "Chunks receive embeddings."
    )

    chunks = chunker.split(text)

    assert chunks == [
        "CloudRAG stores documents. Documents are converted into chunks.",
        "Documents are converted into chunks. Chunks receive embeddings.",
    ]


def test_long_sentence_falls_back_to_word_splitting():
    chunker = TextChunker(chunk_size=50)

    text = (
        "This is a deliberately long sentence that "
        "cannot fit inside one chunk."
    )

    chunks = chunker.split(text)

    assert len(chunks) > 1

    for chunk in chunks:
        assert len(chunk) <= 50


def test_long_sentence_splits_at_word_boundaries():
    chunker = TextChunker(chunk_size=30)

    text = (
        "CloudRAG processes documents "
        "and creates embeddings."
    )

    chunks = chunker.split(text)

    assert len(chunks) > 1

    for chunk in chunks:
        assert len(chunk) <= 30
        assert chunk == chunk.strip()
        assert "  " not in chunk