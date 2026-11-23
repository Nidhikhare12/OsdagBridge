"""Chapter 6 — CAD drawings and visualizations.

Only render figures actually exported by the design run. If no CAD assets are
available, provide one concise availability statement instead of empty frames
or repeated placeholder messages.
"""


def ch6_drawings(fig_paths):
    fig_paths = fig_paths or {}
    groups = [
        ("Bridge Configuration and Layout", [
            ("final_geometry", "girder_3d", "Overall 3D Bridge Superstructure"),
            ("cross_section", "girder_end", "Typical Cross Section"),
            ("plan", "girder_top", "Bridge Top View"),
        ]),
        ("Plate Girder — Detailed Views", [
            ("girder_front", None, "Plate Girder Side View"),
            ("girder_end", None, "Plate Girder End View"),
        ]),
        ("Cross Bracing Detail", [
            ("cb_diagram", "cross_bracing", "Cross Bracing Layout"),
            ("cb_bracing", None, "Cross Bracing — Member Section"),
            ("cb_top_chord", None, "Cross Bracing — Top Chord Section"),
            ("cb_bottom_chord", None, "Cross Bracing — Bottom Chord Section"),
        ]),
        ("End Diaphragm Detail", [
            ("ed_diagram", None, "End Diaphragm Layout"),
            ("ed_bracing", None, "End Diaphragm — Member Section"),
            ("ed_top_chord", None, "End Diaphragm — Top Chord Section"),
            ("ed_bottom_chord", None, "End Diaphragm — Bottom Chord Section"),
        ]),
    ]

    # Resolve all assets first so an entirely empty CAD export becomes one
    # useful note, not four mostly blank pages.
    resolved = []
    used_paths = set()
    missing = []
    for heading, specs in groups:
        items = []
        for primary_key, fallback_key, caption in specs:
            path = fig_paths.get(primary_key)
            if not path and fallback_key:
                path = fig_paths.get(fallback_key)
            if not path or not isinstance(path, str) or path in used_paths:
                missing.append(caption)
                continue
            used_paths.add(path)
            items.append((path, caption))
        resolved.append((heading, items))

    if not used_paths:
        return "\n\n".join([
            r"\chapter{Drawings and Visualizations}",
            r"\label{ch:drawings}",
            "The current design run did not supply CAD figure assets. No drawings have "
            "been fabricated or represented by empty placeholders.",
            r"\begin{itemize}",
            r"\item Overall bridge superstructure and plan",
            r"\item Typical cross-section and plate-girder views",
            r"\item Cross-bracing layout and member sections",
            r"\item End-diaphragm layout and member sections",
            r"\end{itemize}",
            r"\noindent\textit{The numerical design and quantity results are reported in the preceding chapters.}",
        ]) + "\n"

    sections = [r"\chapter{Drawings and Visualizations}",
                r"\label{ch:drawings}",
                "This chapter contains CAD views exported by the current design run."]
    for heading, items in resolved:
        if not items:
            continue
        sections.extend([r"\ReportTopicBreak", r"\section{" + heading + "}"])
        for path, caption in items:
            safe_caption = caption.replace("&", r"\&")
            safe_path = path.replace("\\", "/")
            sections.append(
                r"\begin{figure}[H]" + "\n"
                + r"\centering" + "\n"
                + r"\includegraphics[width=0.88\textwidth,height=0.66\textheight,keepaspectratio]{\detokenize{"
                + safe_path + r"}}" + "\n"
                + r"\caption{" + safe_caption + "}" + "\n"
                + r"\end{figure}"
            )
    if missing:
        sections.append(
            r"\noindent\footnotesize Views not supplied by this design run: "
            + "; ".join(missing).replace("&", r"\&") + ".\normalsize"
        )
    return "\n\n".join(sections) + "\n"
