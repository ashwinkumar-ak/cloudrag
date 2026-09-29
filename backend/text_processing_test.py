from backend.text_processing import split_sentences


def main():
    text = (
        "CloudRAG is a document intelligence platform. "
        "It accepts documents and processes their contents. "
        "The system creates embeddings for semantic search!"
    )

    sentences = split_sentences(text)

    for index, sentence in enumerate(sentences):
        print(f"Sentence {index}: {sentence!r}")


if __name__ == "__main__":
    main()