from osdagbridge.core.reports.report_utils import _tex
from osdagbridge.core.reports.latex.tables import SimpleTable
from osdagbridge.core.reports.theme import get_active_theme


def ch1_project_info(m):
    theme = get_active_theme()
    tbl = SimpleTable(
        col_spec=theme.columns.CH1_KEY_VALUE,
        rows=[
            [r"\textbf{Project Name}", _tex(m.project_name)],
            [r"\textbf{Project Location}", _tex(m.project_location)],
            [r"\textbf{Designer}", _tex(m.designer)],
            [r"\textbf{Reviewer}", _tex(m.reviewer)],
            [r"\textbf{Organization}", _tex(m.company)],
            [r"\textbf{Client}", _tex(m.client)],
            [r"\textbf{Software Version}", "OsdagBridge"],
        ],
    )

    return rf"""
\chapter{{Project Information}}

This section records all project metadata as entered by the designer.

\section{{Project and Design Team Details}}
\label{{sec:project-details}}

{tbl.dumps()}


\section{{Applicable Codes and Standards}}
\label{{sec:codes}}

\begin{{itemize}}
\item Indian Roads Congress (IRC) 5: General Features of Design
\item Indian Roads Congress (IRC) 6: Loads and Load Combinations
\item Indian Roads Congress (IRC) 22: Composite Construction (Limit State Design)
\item Indian Roads Congress (IRC) 24: Steel Road Bridges (Limit State Method)
\item Indian Roads Congress (IRC) 112: Concrete Road Bridges (deck design)
\item Indian Roads Congress Special Publication (IRC SP) 114: Seismic Design of Road Bridges
\item Indian Standard (IS) 800: General Construction in Steel
\item Indian Standard (IS) 2062: Hot Rolled Structural Steel Specification
\item Indian Standard (IS) 6006: Steel Bearings
\end{{itemize}}
"""
