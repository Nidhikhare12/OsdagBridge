
import re

from osdagbridge.core.reports.chap2 import _bracing_tables


def test_bracing_tables_have_matching_column_counts():
    latex = _bracing_tables({}, 3)

    tables = re.findall(
        r"\\begin\{longtable\}\{((?:[^{}]|\{[^{}]*\})*)\}(.*?)\\end\{longtable\}",
        latex,
        re.DOTALL,
    )

    assert len(tables) == 2

    expected_columns = [5, 4]

    for (column_definition, table_content), expected in zip(
        tables, expected_columns
    ):
        columns = re.findall(r"[LCR]\{[\d.]+cm\}", column_definition)
        assert len(columns) == expected

        rows = [
            line.split(r"\\", 1)[0]
            for line in table_content.splitlines()
            if r"\\" in line and r"\caption" not in line
        ]

        assert rows, "No table rows were found"

        for row in rows:
            assert row.count("&") + 1 == expected
