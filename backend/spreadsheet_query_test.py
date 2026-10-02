import sys
import types

fake_psycopg = types.ModuleType("psycopg")
sys.modules.setdefault("psycopg", fake_psycopg)

from backend.spreadsheet_query import SpreadsheetQueryService


class FakeRepository:
    def __init__(self, rows):
        self.rows = rows

    def get_rows(self, user_id, document_ids=None):
        return self.rows


def make_service(rows):
    service = SpreadsheetQueryService()
    service.repository = FakeRepository(rows)
    return service


def rows():
    return [
        {
            "id": 1,
            "document_id": 10,
            "filename": "sales.xlsx",
            "sheet_name": "Sales",
            "row_number": 2,
            "data": {"Postcode": 2198, "Sales_Rep_Name": "John", "Year": 2013, "Value": 77985.12610115489},
            "display_data": {"Postcode": "2198", "Sales_Rep_Name": "John", "Year": "2013", "Value": "$77,985"},
        },
        {
            "id": 2,
            "document_id": 10,
            "filename": "sales.xlsx",
            "sheet_name": "Sales",
            "row_number": 3,
            "data": {"Postcode": 2198, "Sales_Rep_Name": "Jane", "Year": 2012, "Value": 70963.43308910955},
            "display_data": {"Postcode": "2198", "Sales_Rep_Name": "Jane", "Year": "2012", "Value": "$70,963"},
        },
        {
            "id": 3,
            "document_id": 10,
            "filename": "sales.xlsx",
            "sheet_name": "Sales",
            "row_number": 4,
            "data": {"Postcode": 2198, "Sales_Rep_Name": "Ashish", "Year": 2011, "Value": 10618.600611133534},
            "display_data": {"Postcode": "2198", "Sales_Rep_Name": "Ashish", "Year": "2011", "Value": "$10,619"},
        },
    ]


def test_exact_filter_and_display_values():
    service = make_service(rows())
    answer, citations = service.answer(
        "Details of Value where Postcode = 2198",
        user_id=1,
    )
    assert "$77,985" in answer
    assert "$70,963" in answer
    assert "$10,619" in answer
    assert len(citations) == 3


def test_deterministic_sum():
    service = make_service(rows())
    answer, _ = service.answer(
        "What is the total Value where Postcode = 2198?",
        user_id=1,
    )
    assert "$159,567" in answer


def test_currency_sum_uses_displayed_precision():
    service = make_service(rows())
    answer, _ = service.answer(
        "Sum of Value where Postcode = 2198",
        user_id=1,
    )
    assert "$159,567" in answer
    assert "$159,567.16" not in answer
