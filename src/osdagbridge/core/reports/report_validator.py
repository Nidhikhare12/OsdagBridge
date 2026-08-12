"""Lightweight structural validation for generated LaTeX reports."""

from dataclasses import dataclass, field
import re


@dataclass
class LatexValidationResult:
    """Errors found before the LaTeX compiler is invoked."""

    errors: list[str] = field(default_factory=list)

    @property
    def passed(self):
        return not self.errors


_ENVIRONMENT_PATTERN = re.compile(r"\\(?P<action>begin|end)\{(?P<name>[^}]+)\}")
_PACKAGE_PATTERN = re.compile(r"\\usepackage(?:\[[^]]*\])?\{(?P<packages>[^}]+)\}")
_LABEL_PATTERN = re.compile(r"\\label\{(?P<label>[^}]+)\}")
_REFERENCE_PATTERN = re.compile(r"\\(?:ref|pageref|autoref)\{(?P<label>[^}]+)\}")


def validate_latex_source(source):
    """Return structural errors that would otherwise surface only in pdflatex.

    This intentionally checks LaTeX structure rather than trying to parse the
    full language.  It catches the report regressions that are inexpensive to
    identify before invoking an external compiler: mismatched environments,
    duplicate packages and labels, broken references, and incomplete
    ``longtable`` continuation headers.
    """
    result = LatexValidationResult()

    if source.count(r"\begin{document}") != 1:
        result.errors.append("Expected exactly one \\begin{document}.")
    if source.count(r"\end{document}") != 1:
        result.errors.append("Expected exactly one \\end{document}.")

    stack = []
    for match in _ENVIRONMENT_PATTERN.finditer(source):
        action, name = match.group("action", "name")
        if action == "begin":
            stack.append((name, match.start()))
        elif not stack:
            result.errors.append(f"Unexpected \\end{{{name}}}.")
        elif stack[-1][0] != name:
            result.errors.append(
                f"Mismatched environment: expected \\end{{{stack[-1][0]}}} "
                f"before \\end{{{name}}}."
            )
        else:
            stack.pop()
    result.errors.extend(f"Missing \\end{{{name}}}." for name, _ in stack)

    packages = []
    for match in _PACKAGE_PATTERN.finditer(source):
        packages.extend(package.strip() for package in match.group("packages").split(","))
    duplicates = sorted({package for package in packages if packages.count(package) > 1})
    result.errors.extend(f"Duplicate LaTeX package: {package}." for package in duplicates)

    labels = _LABEL_PATTERN.findall(source)
    duplicate_labels = sorted({label for label in labels if labels.count(label) > 1})
    result.errors.extend(f"Duplicate LaTeX label: {label}." for label in duplicate_labels)

    known_labels = set(labels) | {"LastPage"}
    missing_labels = sorted(set(_REFERENCE_PATTERN.findall(source)) - known_labels)
    result.errors.extend(f"Reference to missing label: {label}." for label in missing_labels)

    for index, table_start in enumerate(
        (match.start() for match in re.finditer(r"\\begin\{longtable\}", source)),
        start=1,
    ):
        table_end = source.find(r"\end{longtable}", table_start)
        table = source[table_start:table_end] if table_end != -1 else source[table_start:]
        if r"\caption" not in table:
            result.errors.append(f"Longtable {index} is missing a caption.")
        header = re.search(r"\\endfirsthead(?P<header>.*?)\\endhead", table, re.DOTALL)
        if not header:
            result.errors.append(f"Longtable {index} is missing a continuation header.")
        elif not header.group("header").strip():
            result.errors.append(f"Longtable {index} has an empty continuation header.")

    return result
