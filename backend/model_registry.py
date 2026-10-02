"""Supported text-generation models for CloudRAG V2."""

DEFAULT_MODEL = "gemini-3.5-flash-lite"

MODEL_CATALOG = {
    "gemini-3.5-flash-lite": {
        "id": "gemini-3.5-flash-lite",
        "name": "Gemini 3.5 Flash-Lite",
        "description": "Fast, cost-efficient model for everyday RAG chat.",
    },
    "gemini-3.5-flash": {
        "id": "gemini-3.5-flash",
        "name": "Gemini 3.5 Flash",
        "description": "More capable model for complex questions and synthesis.",
    },
}


def get_model_catalog() -> list[dict]:
    return list(MODEL_CATALOG.values())


def validate_model(model: str | None) -> str:
    selected = (model or DEFAULT_MODEL).strip()

    if selected not in MODEL_CATALOG:
        raise ValueError(
            f"Unsupported model '{selected}'. "
            f"Supported models: {', '.join(MODEL_CATALOG)}"
        )

    return selected
