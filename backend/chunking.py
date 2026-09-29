from backend.text_processing import split_sentences


class TextChunker:
    def __init__(
        self,
        chunk_size: int = 1000,
        overlap_sentences: int = 1,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        if overlap_sentences < 0:
            raise ValueError("overlap_sentences must not be negative")

        self.chunk_size = chunk_size
        self.overlap_sentences = overlap_sentences

    def split(self, text: str) -> list[str]:
        sentences = split_sentences(text)

        if not sentences:
            return []

        chunks = []
        current_sentences = []

        for sentence in sentences:
            if len(sentence) > self.chunk_size:
                if current_sentences:
                    chunks.append(" ".join(current_sentences))
                    current_sentences = []

                chunks.extend(self._split_long_sentence(sentence))
                continue

            candidate = " ".join(
                current_sentences + [sentence]
            )

            if (
                current_sentences
                and len(candidate) > self.chunk_size
            ):
                chunks.append(" ".join(current_sentences))

                overlap_count = min(
                    self.overlap_sentences,
                    len(current_sentences),
                )

                current_sentences = current_sentences[-overlap_count:]

            current_sentences.append(sentence)

        if current_sentences:
            chunks.append(" ".join(current_sentences))

        return chunks

    def _split_long_sentence(self, sentence: str) -> list[str]:
        words = sentence.split()

        chunks = []
        current_words = []

        for word in words:
            candidate = " ".join(current_words + [word])

            if (
                current_words
                and len(candidate) > self.chunk_size
            ):
                chunks.append(" ".join(current_words))
                current_words = []

            current_words.append(word)

        if current_words:
            chunks.append(" ".join(current_words))

        return chunks