from osdagbridge.core.reports.latex_tables import longtable
from osdagbridge.core.reports.report_utils import _tex


def ch1_project_info(m):
    def _row(label, value):
        return r"\cellcolor{osdagGreenLight}\textbf{" + label + r"} & " + value + r" \\" + "\n\\hline"

    rows = "\n".join([
        _row("Project Name", _tex(m.project_name)),
        _row("Project Location", _tex(m.project_location)),
        _row("Designer", _tex(m.designer)),
        _row("Reviewer", _tex(m.reviewer)),
        _row("Organization", _tex(m.company)),
        _row("Client", _tex(m.client)),
        _row("Software Version", "OsdagBridge"),
    ])
    return r"""
\chapter{Project Information}

This section records all project metadata as entered by the designer.

\section{Project and Design Team Details}
\label{sec:project-details}

""" + longtable("param_value", None, None, rows) + r"""

\section{Applicable Codes and Standards}
\label{sec:codes}

\begin{itemize}
\item Indian Roads Congress (IRC) 5: General Features of Design
\item Indian Roads Congress (IRC) 6: Loads and Load Combinations
\item Indian Roads Congress (IRC) 22: Composite Construction (Limit State Design)
\item Indian Roads Congress (IRC) 24: Steel Road Bridges (Limit State Method)
\item Indian Roads Congress (IRC) 112: Concrete Road Bridges (deck design)
\item Indian Roads Congress Special Publication (IRC SP) 114: Seismic Design of Road Bridges
\item Indian Standard (IS) 800: General Construction in Steel
\item Indian Standard (IS) 2062: Hot Rolled Structural Steel Specification
\item Indian Standard (IS) 6006: Steel Bearings
\end{itemize}
"""
