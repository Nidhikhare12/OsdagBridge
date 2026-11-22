"""LaTeX figure and placeholder embedding components."""

from pathlib import Path


def figure(
    path: str | Path,
    caption: str,
    width: str = r"\textwidth",
    height: str | None = None,
    label: str | None = None,
) -> str:
    """Format a figure environment for embedding images."""
    p = str(path).replace("\\", "/")
    opts = f"width={width}"
    if height:
        opts += f",height={height},keepaspectratio"

    label_cmd = f"\\label{{{label}}}\n" if label else ""
    return (
        r"\begin{figure}[H]" + "\n"
        r"\centering" + "\n"
        rf"\includegraphics[{opts}]{{{p}}}" + "\n"
        r"\vspace{0.5em}" + "\n"
        rf"\caption{{\small {caption}}}" + "\n"
        + label_cmd
        + r"\vspace{-0.5em}" + "\n"
        r"\end{figure}"
    )


def placeholder(caption: str, width: str = r"0.95\linewidth") -> str:
    """Format a structured placeholder box when a CAD figure or asset is unavailable."""
    return (
        r"\par\noindent\fbox{\parbox{" + width + r"}{" + "\n"
        r"\centering" + "\n"
        rf"\textit{{[ PLACEHOLDER: {caption} ]}}" + "\n"
        r"}}\par"
    )


def figure_or_placeholder(path: str | Path | None, caption: str, width: str = r"0.9\textwidth") -> str:
    """Embed figure if path is provided (file already copied to assets), else show placeholder box."""
    if path:
        p = str(path).replace("\\", "/")
        return (
            r"\begin{figure}[H]" + "\n"
            r"\centering" + "\n"
            rf"\includegraphics[width={width}]{{{p}}}" + "\n"
            rf"\caption{{\parbox{{\linewidth}}{{\centering\small {caption}}}}}" + "\n"
            r"\end{figure}"
        )
    return (
        r"\begin{figure}[H]" + "\n"
        r"\centering" + "\n"
        r"\fbox{\parbox{0.95\linewidth}{" + "\n"
        rf"\centering\textit{{[ PLACEHOLDER: {caption} ]}}" + "\n"
        r"}}" + "\n"
        rf"\caption*{{\parbox{{\linewidth}}{{\centering\small {caption}}}}}" + "\n"
        r"\end{figure}"
    )


def figure_embed(
    path: str | Path | None,
    caption: str,
    width: str = r"\textwidth",
    height: str | None = None,
) -> str:
    """Embed a real figure when path is provided (already copied); otherwise use an fbox placeholder."""
    if path:
        p = str(path).replace("\\", "/")
        opts = f"width={width}"
        if height:
            opts += f",height={height},keepaspectratio"
        return (
            r"\begin{figure}[H]" + "\n"
            r"\vspace{-0.5em}" + "\n"
            r"\centering" + "\n"
            rf"\includegraphics[{opts}]{{{p}}}" + "\n"
            r"\vspace{0.5em}" + "\n"
            rf"\caption{{\parbox{{\linewidth}}{{\centering\small {caption}}}}}" + "\n"
            r"\vspace{-0.5em}" + "\n"
            r"\end{figure}"
        )
    return (
        r"\par\noindent\fbox{\parbox{0.95\linewidth}{" + "\n"
        r"\centering" + "\n"
        rf"\textit{{[ PLACEHOLDER: {caption} ]}}" + "\n"
        r"}}\par"
    )
