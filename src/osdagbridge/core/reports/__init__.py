"""Reports package."""
from .report_generator import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    ReportFigures,
    ReportPayload,
    ReportResult,
    build_report_payload,
    generate_report,
)
from .styles import (
    COLOR_OSDAG_GREEN,
    COLOR_HEADER_NAVY,
    COLOR_ZEBRA_LIGHT,
    COLOR_PASS,
    COLOR_FAIL,
    LATEX_COLOR_DEFINITIONS,
    ARRAY_STRETCH,
    TABLE_HEADER_FORMAT,
    get_preamble_styles,
    pass_indicator,
    fail_indicator,
    status_indicator,
)

from .chart_generator import (
    generate_ur_chart,
    generate_quantity_charts,
)

__all__ = [
    "ReportMetadata", "ReportOptions", "ReportRequest",
    "ReportFigures", "ReportPayload", "ReportResult",
    "build_report_payload", "generate_report",
    "COLOR_OSDAG_GREEN", "COLOR_HEADER_NAVY", "COLOR_ZEBRA_LIGHT",
    "COLOR_PASS", "COLOR_FAIL", "LATEX_COLOR_DEFINITIONS",
    "ARRAY_STRETCH", "TABLE_HEADER_FORMAT",
    "get_preamble_styles", "pass_indicator", "fail_indicator", "status_indicator",
    "generate_ur_chart", "generate_quantity_charts",
]
