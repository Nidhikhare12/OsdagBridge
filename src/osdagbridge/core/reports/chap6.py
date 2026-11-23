from osdagbridge.core.reports import styles as S
from osdagbridge.core.reports.latex_tables import figure, figure_row


def ch6_drawings(fig_paths):
    """Chapter 6 – Drawings and Visualizations.

    Figure numbers are assigned automatically by LaTeX (6.1 … 6.14):
      6.1 Overall 3D Bridge Superstructure     6.2 Typical Cross Section   6.3 Top View
      6.4 3D View of Plate Girders             6.5 Cross Section of Plate Girder
      6.6 Side View of Girder                  6.7 Cross Bracing Layout
      6.8-6.10 Cross-bracing bracing/top/bottom chord sections
      6.11 End Diaphragm Layout                6.12-6.14 end-diaphragm sections
    """
    W = S.FIGURE["default_width"]
    fp = fig_paths.get

    def _f(key, title, label):
        return figure(fp(key), title, width=W, label=label)

    cb_row = figure_row([
        (fp('cb_bracing'), 'Cross Bracing -- Bracing Section', 'fig:cb-bracing-sec'),
        (fp('cb_top_chord'), 'Cross Bracing -- Top Chord Section', 'fig:cb-top-chord'),
        (fp('cb_bottom_chord'), 'Cross Bracing -- Bottom Chord Section', 'fig:cb-bottom-chord'),
    ])
    ed_row = figure_row([
        (fp('ed_bracing'), 'End Diaphragm -- Bracing Section', 'fig:ed-bracing-sec'),
        (fp('ed_top_chord'), 'End Diaphragm -- Top Chord Section', 'fig:ed-top-chord'),
        (fp('ed_bottom_chord'), 'End Diaphragm -- Bottom Chord Section', 'fig:ed-bottom-chord'),
    ])

    return (r"""
\chapter{Drawings and Visualizations}
\label{ch:drawings}

This section presents CAD-generated views of the designed bridge and its components. All views are generated automatically by OsdagBridge using pythonOCC.

\section{Bridge Configuration and Layout}
\label{sec:bridge-layout}

""" + _f('final_geometry', 'Overall 3D Bridge Superstructure', 'fig:bridge-3d') + "\n"
        + _f('cross_section', 'Typical Cross Section', 'fig:cross-section') + "\n"
        + _f('girder_top', 'Top View', 'fig:top-view') + r"""

\section{Plate Girder --- Detailed Views}
\label{sec:girder-views}

""" + _f('girder_3d', '3D View of Plate Girders', 'fig:girder-3d') + "\n"
        + _f('section_preview', 'Cross Section of Plate Girder', 'fig:girder-xsec') + "\n"
        + _f('stiffener_preview', 'Side View of Girder', 'fig:girder-side') + r"""

\section{Cross Bracing Detail}
\label{sec:bracing-detail}

""" + _f('cb_diagram', 'Cross Bracing Layout', 'fig:cb-layout') + "\n" + cb_row + r"""

\section{End Diaphragm Detail}
\label{sec:diaphragm-detail}

""" + _f('ed_diagram', 'End Diaphragm Layout', 'fig:ed-layout') + "\n" + ed_row + "\n")
