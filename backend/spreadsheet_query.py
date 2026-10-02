import re
from decimal import Decimal, ROUND_HALF_UP

from backend.repositories.spreadsheets import SpreadsheetRepository
from backend.spreadsheet import find_column, numeric_value, parse_literal, values_equal


class SpreadsheetQueryService:
    OPERATORS = (">=", "<=", "=", ">", "<")
    CALC_KEYWORDS = {
        "sum": "sum",
        "total": "sum",
        "average": "average",
        "avg": "average",
        "mean": "average",
        "count": "count",
        "how many": "count",
        "minimum": "min",
        "minimum value": "min",
        "min": "min",
        "maximum": "max",
        "maximum value": "max",
        "max": "max",
    }

    def __init__(self):
        self.repository = SpreadsheetRepository()

    def is_spreadsheet_query(
        self,
        question: str,
        user_id: int,
        document_ids: list[int] | None = None,
    ) -> bool:
        rows = self.repository.get_rows(user_id, document_ids)
        if not rows:
            return False

        lowered = question.lower()
        if any(keyword in lowered for keyword in (
            "where", "filter", "spreadsheet", "excel", "csv",
            "column", "row", "sum", "total", "average", "avg",
            "mean", "count", "minimum", "maximum", "min", "max",
            "greater than", "less than", "equals", "equal to",
        )):
            return True

        sample = rows[0]["data"]
        return any(find_column(sample, word) for word in re.findall(r"[A-Za-z][A-Za-z0-9_ -]*", question))

    def answer(
        self,
        question: str,
        user_id: int,
        document_ids: list[int] | None = None,
    ) -> tuple[str, list[dict]]:
        rows = self.repository.get_rows(user_id, document_ids)
        if not rows:
            return (
                "I could not find any completed spreadsheet data in the selected documents.",
                [],
            )

        filtered = self._apply_filters(rows, question)
        if not filtered:
            return "No matching spreadsheet rows were found.", []

        calculation = self._detect_calculation(question)
        if calculation:
            answer = self._calculate(calculation, question, filtered)
        else:
            answer = self._describe_rows(question, filtered)

        citations = [self._citation(row) for row in filtered[:10]]
        return answer, citations

    def _apply_filters(self, rows, question):
        result = rows
        for row in rows[:1]:
            columns = list(row["data"].keys())
            for column in columns:
                pattern = re.compile(
                    rf"{re.escape(column)}\s*(>=|<=|=|>|<|\bis\b|\bequals\b|\bequal to\b)\s*([^,;\n]+?)(?=\s+and\s+|\s+where\s+|[,;]|$)",
                    re.IGNORECASE,
                )
                for match in pattern.finditer(question):
                    operator = match.group(1).lower()
                    expected = parse_literal(match.group(2).strip())
                    result = [
                        item for item in result
                        if self._matches(item["data"].get(column), operator, expected)
                    ]

        return result

    def _matches(self, actual, operator, expected):
        if operator in {"=", "is", "equals", "equal to"}:
            return values_equal(actual, expected)

        actual_number = numeric_value(actual)
        expected_number = numeric_value(expected)
        if actual_number is None or expected_number is None:
            return False

        if operator == ">":
            return actual_number > expected_number
        if operator == "<":
            return actual_number < expected_number
        if operator == ">=":
            return actual_number >= expected_number
        if operator == "<=":
            return actual_number <= expected_number
        return False

    def _detect_calculation(self, question: str):
        lowered = question.lower()
        for keyword, calculation in sorted(self.CALC_KEYWORDS.items(), key=lambda item: -len(item[0])):
            if keyword in lowered:
                return calculation
        return None

    def _target_column(self, question, rows):
        columns = list(rows[0]["data"].keys())
        lowered = question.lower()

        # Prefer a column named after "of", e.g. "sum of Value".
        match = re.search(r"\b(?:of|for|on)\s+([A-Za-z][A-Za-z0-9_ -]*)", question, re.IGNORECASE)
        if match:
            candidate = find_column(rows[0]["data"], match.group(1).strip())
            if candidate:
                return candidate

        before_filters = re.split(r"\bwhere\b", lowered, maxsplit=1, flags=re.IGNORECASE)[0]
        for column in columns:
            if re.search(rf"\b{re.escape(column)}\b", before_filters, re.IGNORECASE):
                if any(numeric_value(row["data"].get(column)) is not None for row in rows):
                    return column

        for column in columns:
            if re.search(rf"\b{re.escape(column)}\b", before_filters, re.IGNORECASE):
                return column

        for column in columns:
            if any(numeric_value(row["data"].get(column)) is not None for row in rows):
                return column
        return None

    def _calculate(self, calculation, question, rows):
        column = self._target_column(question, rows)
        if calculation == "count":
            return f"Found {len(rows)} matching row{'s' if len(rows) != 1 else ''}."
        if not column:
            return "I found the matching rows, but I could not determine which column to calculate."

        numbers = [numeric_value(row["data"].get(column)) for row in rows]
        numbers = [value for value in numbers if value is not None]
        if not numbers:
            return f"The {column} column does not contain numeric values for the matching rows."

        if calculation == "sum":
            result = sum(numbers, Decimal("0"))
        elif calculation == "average":
            result = sum(numbers, Decimal("0")) / Decimal(len(numbers))
        elif calculation == "min":
            result = min(numbers)
        elif calculation == "max":
            result = max(numbers)
        else:
            return "I could not determine the requested calculation."

        formatted = self._format_result(result, rows, column)
        return f"{calculation.title()} of {column} for {len(rows)} matching row{'s' if len(rows) != 1 else ''}: {formatted}."

    def _describe_rows(self, question, rows):
        requested = self._requested_columns(question, rows[0]["data"])
        details = []
        for row in rows[:20]:
            if requested:
                values = [
                    f"{column}: {row['display_data'].get(column, row['data'].get(column, ''))}"
                    for column in requested
                ]
            else:
                values = [
                    f"{column}: {value}"
                    for column, value in row["display_data"].items()
                    if value != ""
                ]
            details.append("; ".join(values))

        prefix = f"Found {len(rows)} matching row{'s' if len(rows) != 1 else ''}."
        return prefix + " " + " | ".join(details)

    def _requested_columns(self, question, data):
        lowered = question.lower()
        match = re.search(r"\b(?:details?|values?|show|list|give me|what is|what are)\s+(?:of\s+)?(.+?)(?:\s+where\s+|$)", lowered)
        if not match:
            return []
        phrase = match.group(1)
        requested = []
        for part in re.split(r",|\band\b", phrase):
            column = find_column(data, part.strip())
            if column and column not in requested:
                requested.append(column)
        return requested

    def _citation(self, row):
        content = " | ".join(
            f"{key}: {value}"
            for key, value in row["display_data"].items()
            if value != ""
        )
        return {
            "chunk_id": row["id"],
            "document_id": row["document_id"],
            "filename": row["filename"],
            "chunk_index": row["row_number"],
            "content": content,
            "distance": 0.0,
        }

    @staticmethod
    def _format_result(value: Decimal, rows, column: str) -> str:
        rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        text = f"{rounded:,.2f}".rstrip("0").rstrip(".")
        sample = str(rows[0]["display_data"].get(column, ""))
        if "$" in sample:
            return f"${text}"
        if "%" in sample:
            return f"{text}%"
        return text
