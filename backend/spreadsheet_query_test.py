from decimal import Decimal

from backend.spreadsheet_query import SpreadsheetQueryService


def test_currency_sum_uses_displayed_whole_dollars():
    service = SpreadsheetQueryService()

    rows = [
        {
            "id": 1,
            "document_id": 1,
            "filename": "sales.xlsx",
            "row_number": 2,
            "data": {"Postcode": 2198, "Value": "100.49"},
            "display_data": {"Postcode": "2198", "Value": "$100"},
        },
        {
            "id": 2,
            "document_id": 1,
            "filename": "sales.xlsx",
            "row_number": 3,
            "data": {"Postcode": 2198, "Value": "200.51"},
            "display_data": {"Postcode": "2198", "Value": "$201"},
        },
    ]

    assert service._calculation_value(rows[0], "Value") == Decimal("100")
    assert service._calculation_value(rows[1], "Value") == Decimal("201")
    assert sum(
        service._calculation_value(row, "Value") for row in rows
    ) == Decimal("301")
