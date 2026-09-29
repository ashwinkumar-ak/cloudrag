from backend.chunking import TextChunker


def main():
    chunker = TextChunker(
        chunk_size=100,
        overlap_sentences=1,
    )

    text = (
        "CloudRAG is a document intelligence platform. "
        "This is an intentionally extremely long sentence "
        "designed to exceed the configured chunk size so that "
        "we can verify that the chunker falls back to word based "
        "splitting instead of producing an unexpectedly large chunk. "
        "PostgreSQL stores the resulting embeddings."
    )

    chunks = chunker.split(text)

    for index, chunk in enumerate(chunks):
        print(f"Chunk {index}: {chunk!r}")


if __name__ == "__main__":
    main()