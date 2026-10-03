from pathlib import Path

import fitz
from docx import Document as WordDocument
from openpyxl import load_workbook
from pptx import Presentation


SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".xlsm",
    ".csv",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


class DocumentParseError(RuntimeError):
    """Raised when a document cannot be parsed."""


def extract_text(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise DocumentParseError(
            f"Unsupported file type: {extension or 'unknown'}"
        )

    if extension in {".txt", ".md"}:
        return _extract_text_file(content)

    if extension == ".pdf":
        return _extract_pdf(content)

    if extension == ".docx":
        return _extract_docx(content)

    if extension == ".pptx":
        return _extract_pptx(content)

    if extension in {".xlsx", ".xlsm"}:
        return _extract_excel(content)

    if extension == ".csv":
        return _extract_csv(content)

    if extension in {".jpg", ".jpeg", ".png", ".webp"}:
        return "[Image document]"

    raise DocumentParseError(
        f"Unsupported file type: {extension}"
    )


def _extract_text_file(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentParseError(
            "Text file must be UTF-8 encoded."
        ) from exc


def _extract_pdf(content: bytes) -> str:
    try:
        document = fitz.open(
            stream=content,
            filetype="pdf",
        )

        pages = []

        for page_number, page in enumerate(document, start=1):
            text = page.get_text().strip()

            if text:
                pages.append(
                    f"[Page {page_number}]\n{text}"
                )

        document.close()

        return "\n\n".join(pages)

    except Exception as exc:
        raise DocumentParseError(
            "Failed to read PDF document."
        ) from exc


def _extract_docx(content: bytes) -> str:
    try:
        from io import BytesIO

        document = WordDocument(
            BytesIO(content)
        )

        sections = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                sections.append(text)

        for table_index, table in enumerate(
            document.tables,
            start=1,
        ):
            sections.append(
                f"[Table {table_index}]"
            )

            for row in table.rows:
                cells = [
                    cell.text.strip()
                    for cell in row.cells
                ]

                sections.append(
                    " | ".join(cells)
                )

        return "\n".join(sections)

    except Exception as exc:
        raise DocumentParseError(
            "Failed to read Word document."
        ) from exc


def _extract_pptx(content: bytes) -> str:
    try:
        from io import BytesIO

        presentation = Presentation(
            BytesIO(content)
        )

        slides = []

        for slide_number, slide in enumerate(
            presentation.slides,
            start=1,
        ):
            slide_text = []

            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text = shape.text.strip()

                    if text:
                        slide_text.append(text)

            if slide_text:
                slides.append(
                    f"[Slide {slide_number}]\n"
                    + "\n".join(slide_text)
                )

        return "\n\n".join(slides)

    except Exception as exc:
        raise DocumentParseError(
            "Failed to read PowerPoint presentation."
        ) from exc


def _extract_excel(content: bytes) -> str:
    try:
        from io import BytesIO

        workbook = load_workbook(
            BytesIO(content),
            read_only=True,
            data_only=True,
        )

        sheets = []

        for worksheet in workbook.worksheets:
            rows = [
                f"[Sheet: {worksheet.title}]"
            ]

            for row in worksheet.iter_rows(
                values_only=True
            ):
                values = []

                for value in row:
                    if value is None:
                        values.append("")
                    else:
                        values.append(str(value))

                if any(value.strip() for value in values):
                    rows.append(
                        " | ".join(values)
                    )

            if len(rows) > 1:
                sheets.append(
                    "\n".join(rows)
                )

        workbook.close()

        return "\n\n".join(sheets)

    except Exception as exc:
        raise DocumentParseError(
            "Failed to read Excel workbook."
        ) from exc

def _extract_csv(content: bytes) -> str:
    try:
        from backend.spreadsheet import parse_spreadsheet

        rows = parse_spreadsheet("data.csv", content)
        sections = []

        for row in rows:
            values = [
                f"{key}: {value}"
                for key, value in row["display_data"].items()
                if value != ""
            ]
            sections.append(
                f"[Sheet: CSV, Row {row['row_number']}]\n"
                + " | ".join(values)
            )

        return "\n\n".join(sections)
    except Exception as exc:
        raise DocumentParseError(
            "Failed to read CSV document."
        ) from exc
