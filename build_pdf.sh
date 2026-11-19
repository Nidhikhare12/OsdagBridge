#!/usr/bin/env bash
# build_pdf.sh — headless OsdagBridge report generator
#
# Runs the full plate-girder analysis/design pipeline and compiles the
# LaTeX design report to PDF without needing the Qt GUI.
#
# Prerequisites:
#   - macOS or Linux with Miniconda installed at ~/miniconda3 (or edit
#     CONDA_SH below to point at your conda.sh)
#   - conda env "osdagbridge-env" created from environment.yml
#   - a real pdfTeX: TinyTeX at ~/Library/TinyTeX (macOS) or any TeX Live
#     install; the script prefers TinyTeX's pdflatex when present
#
# Usage:
#   ./build_pdf.sh [output_dir] [file_stem]
#   ./build_pdf.sh reports Report_After
#
# Defaults: output_dir=./reports  file_stem=Report_Before

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${1:-${REPO_ROOT}/reports}"
FILE_STEM="${2:-Report_Before}"

# --- Conda environment -------------------------------------------------------
# shellcheck disable=SC1091
source "${HOME}/miniconda3/etc/profile.d/conda.sh"
conda activate osdagbridge-env

# --- Ensure a real pdfTeX is on PATH ----------------------------------------
# The report generator shells out to `pdflatex`. A Tectonic shim may exist at
# ~/.local/bin/pdflatex and halt on the first LaTeX error; TinyTeX's real
# pdfTeX (installed at ~/Library/TinyTeX) tolerates recoverable errors in
# nonstopmode, matching the upstream toolchain. Prefer it explicitly.
TINYTEX_BIN="${HOME}/Library/TinyTeX/TinyTeX/bin/universal-darwin"
if [[ -x "${TINYTEX_BIN}/pdflatex" ]]; then
    export PATH="${TINYTEX_BIN}:${PATH}"
fi

# Headless Qt platform — the driver only uses compute helpers, but any stray
# widget import stays off the real display server.
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"

mkdir -p "${OUTPUT_DIR}"

echo "[build_pdf] env: $(python -c 'import sys;print(sys.prefix)')"
echo "[build_pdf] pdflatex: $(command -v pdflatex)"
echo "[build_pdf] output: ${OUTPUT_DIR}/${FILE_STEM}.pdf"

python "${REPO_ROOT}/tools/generate_baseline_report.py" "${OUTPUT_DIR}" "${FILE_STEM}"

# --- Clean up LaTeX intermediates --------------------------------------------
# generate_report compiles inside a temp dir and only copies .pdf/.tex back,
# but sweep the output dir anyway in case a manual compile left artifacts.
find "${OUTPUT_DIR}" -maxdepth 1 -type f \
    \( -name "*.aux" -o -name "*.log" -o -name "*.out" -o -name "*.xdv" \
       -o -name "*.fdb_latexmk" -o -name "*.fls" -o -name "*.synctex.gz" \
       -o -name "*.bbl" -o -name "*.blg" -o -name "*.nav" -o -name "*.snm" \
       -o -name "*.toc" -o -name "*.lof" -o -name "*.lot" -o -name "*.idx" \
       -o -name "*.ilg" -o -name "*.ind" -o -name "*.glo" -o -name "*.gls" \
       -o -name "*.ist" -o -name "*.acn" -o -name "*.acr" \) \
    -delete

echo "[build_pdf] done: ${OUTPUT_DIR}/${FILE_STEM}.pdf"
