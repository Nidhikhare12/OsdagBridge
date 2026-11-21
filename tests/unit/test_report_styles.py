"""Tests for the centralized report style post-processor."""

from osdagbridge.core.reports import styles


SAMPLE_TABLE = r"""\begin{longtable}{|L{3cm}|C{2cm}|}
\caption{\textbf{Sample table}}
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
Alpha & 1 \\
\hline
Beta & 2 \\
\hline
\end{longtable}
"""


def test_longtable_headers_are_repeated():
    styled = styles._repeat_longtable_headers(SAMPLE_TABLE)
    assert r"\endfirsthead" in styled
    assert r"\endhead" in styled
    # The bold header row must appear twice: first page + continuation pages.
    assert styled.count(r"\textbf{Parameter} & \textbf{Value}") == 2
    # Body rows stay single.
    assert styled.count("Alpha & 1") == 1


def test_existing_headers_are_not_duplicated():
    table = SAMPLE_TABLE.replace(
        r"\hline" + "\n" + r"Alpha & 1",
        r"\endhead" + "\n" + r"\hline" + "\n" + r"Alpha & 1",
    )
    styled = styles._repeat_longtable_headers(table)
    assert styled.count(r"\endhead") == 1


def test_heading_protection_uses_valid_latex():
    styled = styles._protect_headings(r"\section{Design Checks}" + "\n")
    expected = (
        r"\needspace{" + str(styles.PAGE_BOTTOM_THRESHOLD_LINES)
        + r"\baselineskip}" + "\n" + r"\section{Design Checks}"
    )
    assert expected in styled
    assert not styled.startswith("eedspace")  # no mangled backslash escapes
