import re


def split_sentences(text: str) -> list[str]:
    text = text.strip()

    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)

    return [sentence.strip() for sentence in sentences if sentence.strip()]