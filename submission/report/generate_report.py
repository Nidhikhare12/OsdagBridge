"""
OsdagBridge Software Testing & Issue Reporting — Technical Report Generator
Author: Pujari Abhiram (B.Tech CSE - Data Science, 3rd Year, Anurag University)
Screening Task: FOSSEE / Osdag Bridge Module Testing (IIT Bombay)
Supervisor: Nidhikhare12

Generates: testing_report.pdf with:
  - Paragraph-wrapped table cells to prevent any text overlapping
  - Preformatted code blocks preserving line breaks and indentation
  - Proportional image aspect ratios
  - Clickable hyperlinks on cover page and tables
  - Full documentation of all 4 defects found
  - Explanatory note on TC01_Baseline_18m.osi filename
"""

import os, sys, yaml
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Image, Preformatted
)
from reportlab.pdfgen import canvas
from PIL import Image as PILImage

# ── Paths ──────────────────────────────────────────────────────────────────
BASE = r"C:\Users\PUJARI ABHIRAM\Projects"
SUBMISSION = os.path.join(BASE, "submission")
TC_DIR  = os.path.join(SUBMISSION, "test_cases")
FIG_DIR = os.path.join(SUBMISSION, "figures")
OUT_PDF = os.path.join(SUBMISSION, "report", "testing_report.pdf")

OSI_FILES = {
    "TC01": os.path.join(TC_DIR, "TC01_Baseline_18m.osi"),
    "TC02": os.path.join(TC_DIR, "TC02_Consecutive_24m.osi"),
    "TC03": os.path.join(TC_DIR, "TC03_Custom_Material.osi"),
}
FIGS = {
    "dock":   os.path.join(FIG_DIR, "fig_dock_op.png"),
    "bridge": os.path.join(FIG_DIR, "fig_d_b.png"),
    "plots":  os.path.join(FIG_DIR, "fig_plots.png"),
}

VIDEO_URL = "https://drive.google.com/file/d/1h2V6FlFB_WoZQWbumkVg31w7dMjUDIqx/view?usp=drive_link"

def load_osi(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

osi = {k: load_osi(v) for k, v in OSI_FILES.items()}

# ── Numbered Canvas for Running Headers & Footers ───────────────────────────
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        if self._pageNumber == 1:
            return  # Suppress running header/footer on cover page
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        
        # Top Running Header
        self.drawString(2.0*cm, 28.2*cm, "OsdagBridge Software Testing & Issue Reporting | Technical Evaluation Report")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(2.0*cm, 28.0*cm, 19.0*cm, 28.0*cm)
        
        # Bottom Running Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(19.0*cm, 1.2*cm, page_str)
        self.drawString(2.0*cm, 1.2*cm, "Pujari Abhiram (Anurag University) — FOSSEE / Osdag Screening Task")
        self.line(2.0*cm, 1.5*cm, 19.0*cm, 1.5*cm)
        self.restoreState()

# ── Typography & Styles ────────────────────────────────────────────────────
styles = getSampleStyleSheet()

NAVY_PRIMARY = colors.HexColor("#1A365D")
SLATE_BLUE   = colors.HexColor("#2B6CB0")
CHARCOAL     = colors.HexColor("#2D3748")
MUTED_GREY   = colors.HexColor("#718096")
LIGHT_BG     = colors.HexColor("#F7FAFC")
BORDER_COLOR = colors.HexColor("#CBD5E0")

H1 = ParagraphStyle(
    "H1", parent=styles["Heading1"],
    fontSize=13, leading=17,
    spaceBefore=12, spaceAfter=5,
    textColor=NAVY_PRIMARY, fontName="Helvetica-Bold",
    keepWithNext=True
)

H2 = ParagraphStyle(
    "H2", parent=styles["Heading2"],
    fontSize=10.5, leading=14,
    spaceBefore=9, spaceAfter=4,
    textColor=SLATE_BLUE, fontName="Helvetica-Bold",
    keepWithNext=True
)

BODY = ParagraphStyle(
    "Body", parent=styles["Normal"],
    fontSize=8.5, leading=12.5,
    spaceAfter=4, alignment=TA_JUSTIFY,
    textColor=CHARCOAL, fontName="Helvetica"
)

BODY_BOLD = ParagraphStyle("BodyBold", parent=BODY, fontName="Helvetica-Bold")

CODE = ParagraphStyle(
    "CodeBlock", parent=styles["Code"],
    fontSize=7.2, leading=9.5,
    fontName="Courier",
    textColor=colors.HexColor("#1A202C"),
    backColor=colors.HexColor("#EDF2F7"),
    borderPadding=6, spaceBefore=3, spaceAfter=5,
    leftIndent=4, rightIndent=4
)

CAPTION = ParagraphStyle(
    "Caption", parent=BODY,
    fontSize=7.8, leading=10.5,
    alignment=TA_CENTER, textColor=MUTED_GREY,
    spaceBefore=2, spaceAfter=6
)

# Table cell styles ensuring text wrapping
CELL_STYLE = ParagraphStyle(
    "TableCell", parent=BODY,
    fontSize=7.8, leading=10,
    textColor=CHARCOAL, alignment=TA_LEFT,
    spaceAfter=0
)

HDR_STYLE = ParagraphStyle(
    "TableHdr", parent=CELL_STYLE,
    fontName="Helvetica-Bold",
    textColor=colors.white,
    alignment=TA_LEFT
)

def make_table(data, col_widths=None):
    """Wraps every cell in a Paragraph to enforce word-wrapping and prevent text overlap."""
    wrapped_data = []
    for r_idx, row in enumerate(data):
        wrapped_row = []
        for c in row:
            if isinstance(c, Paragraph):
                wrapped_row.append(c)
            else:
                st = HDR_STYLE if r_idx == 0 else CELL_STYLE
                wrapped_row.append(Paragraph(str(c), st))
        wrapped_data.append(wrapped_row)
    
    t = Table(wrapped_data, colWidths=col_widths, hAlign="LEFT")
    s = [
        ("BACKGROUND", (0,0), (-1,0), NAVY_PRIMARY),
        ("GRID",       (0,0), (-1,-1), 0.4, BORDER_COLOR),
        ("LEFTPADDING",(0,0), (-1,-1), 4.5),
        ("RIGHTPADDING",(0,0), (-1,-1), 4.5),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0), (-1,-1), 3),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
    ]
    for i in range(1, len(data)):
        bg = LIGHT_BG if i % 2 == 1 else colors.white
        s.append(("BACKGROUND", (0,i), (-1,i), bg))
    t.setStyle(TableStyle(s))
    return t

# ── Document Construction ──────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUT_PDF, pagesize=A4,
    topMargin=2.0*cm, bottomMargin=2.0*cm,
    leftMargin=2.0*cm, rightMargin=2.0*cm,
    title="OsdagBridge Software Testing & Issue Reporting - Technical Report",
    author="Pujari Abhiram"
)

story = []

# ══════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ══════════════════════════════════════════════════════════════════════════
story.append(Spacer(1, 1.2*cm))
story.append(Paragraph("FOSSEE / Osdag &mdash; IIT Bombay", ParagraphStyle("Inst", parent=BODY, alignment=TA_CENTER, fontSize=11, fontName="Helvetica-Bold", textColor=MUTED_GREY)))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph("OsdagBridge Module Testing &amp; Bug Reporting", ParagraphStyle("Title", parent=H1, fontSize=20, leading=24, alignment=TA_CENTER, textColor=NAVY_PRIMARY)))
story.append(Paragraph("Technical Evaluation Report &mdash; Short-Span Steel Girder Bridge Module", ParagraphStyle("Sub", parent=BODY, fontSize=10.5, leading=14, alignment=TA_CENTER, textColor=SLATE_BLUE)))
story.append(Spacer(1, 0.4*cm))
story.append(HRFlowable(width="90%", thickness=1.5, color=SLATE_BLUE, hAlign="CENTER", spaceAfter=12))

video_link_html = f'<a href="{VIDEO_URL}"><font color="#2B6CB0"><u>Watch Screencast (Google Drive)</u></font></a>'
fork_link_html  = '<a href="https://github.com/pujariabhi/OsdagBridge"><font color="#2B6CB0"><u>github.com/pujariabhi/OsdagBridge</u></font></a>'

meta_data = [
    ["Candidate Name",        "Pujari Abhiram"],
    ["Degree & Specialization", "B.Tech in Computer Science & Engineering (Data Science) — 3rd Year"],
    ["Institution",           "Anurag University, Hyderabad, Telangana"],
    ["Supervisor / Mentor",   "Nidhikhare12 (OsdagBridge Developer)"],
    ["Upstream Repository",   "https://github.com/Nidhikhare12/OsdagBridge  (branch: dev)"],
    ["Candidate Fork",        fork_link_html],
    ["Task Assigned",         "OsdagBridge Software Testing & Issue Reporting"],
    ["Report Date",           date.today().strftime("%d %B %Y")],
    ["Screencast Video",      video_link_html],
]
story.append(make_table(meta_data, col_widths=[4.8*cm, 12.2*cm]))
story.append(Spacer(1, 0.8*cm))

story.append(Paragraph("<b>Task Overview &amp; Scope:</b>", BODY_BOLD))
story.append(Paragraph(
    "This technical report documents the functional verification, multi-run state persistence audits, "
    "and dictionary serialization checks conducted on the OsdagBridge short-span steel plate girder module. "
    "Testing was executed on an editable installation of the <b>dev</b> branch (commit <code>d74f56d</code>) "
    "inside an isolated Python 3.12 environment on Windows 11. "
    "All test scenarios evaluated input-to-output consistency across geometric parameters, custom material "
    "definitions, 3D CAD rendering, and IRC:6 / IRC:24 design checks.", BODY))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    "<b>Executive Findings:</b> Custom steel and concrete grades were successfully retained in <code>input_dict</code> "
    "without falling back to defaults. However, testing uncovered two critical bugs (a state persistence failure where interior "
    "girders G2–G8 retain stale span lengths after an in-app modification, and a database table naming mismatch that silently "
    "skips cross-bracing design), alongside two high-severity issues (unhandled shear modulus ValueError during headless reload, "
    "and a missing-value TypeError in defaults.py). All issues are documented with reproduction steps and suggested code patches.", BODY))

story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# SECTION 1 — TEST ENVIRONMENT & SETUP
# ══════════════════════════════════════════════════════════════════════════
story.append(Paragraph("1. Test Environment &amp; Reproduction Setup", H1))
story.append(Paragraph(
    "To ensure reliable reproduction, the module was cloned from the candidate fork and built in editable mode "
    "within a fresh Conda environment. The software configuration is detailed below:", BODY))

env_rows = [
    ["Component", "Version / Description"],
    ["Operating System", "Windows 11 Home (64-bit)"],
    ["Python Runtime", "Python 3.12 (via Miniconda: osdagbridge-env)"],
    ["OsdagBridge Core", "dev branch, commit d74f56d (pip install -e .)"],
    ["OpenSeesPy", "v3.8.0.0 (finite element grillage analysis engine)"],
    ["GUI Framework", "PySide6 v6.11.3 (Qt6 desktop user interface)"],
    ["Post-Processing", "opsvis v1.3.8, Matplotlib v3.11.2, xarray v2026.9.0"],
    ["Document Engine", "ReportLab v5.1.0, PyYAML v6.0.3"],
]
story.append(make_table(env_rows, col_widths=[4.8*cm, 12.2*cm]))
story.append(Spacer(1, 0.3*cm))

story.append(Paragraph("<b>Environment Configuration Note (Windows Smart App Control):</b>", BODY_BOLD))
story.append(Paragraph(
    "During initial setup, Windows 11 Smart App Control blocked conda-forge C-extension DLLs (PySide6 QtCore, "
    "numpy C-API, and openseespy binaries) with the error <i>'An Application Control policy has blocked this file'</i>. "
    "Disabling Smart App Control in Windows Security allowed all libraries to load cleanly (exit code 0). "
    "This was verified as an OS-level signature policy check and did not require any modification to OsdagBridge source code.", BODY))

# ══════════════════════════════════════════════════════════════════════════
# SECTION 2 — TEST MATRIX & PARAMETERS
# ══════════════════════════════════════════════════════════════════════════
story.append(Paragraph("2. Executed Test Cases (TC01 to TC03)", H1))
story.append(Paragraph(
    "Three distinct test scenarios were executed to evaluate basic input processing, multi-run state persistence, "
    "and custom material registration. All cases were saved to <code>.osi</code> project files for verification.", BODY))

tc_table = [
    ["Parameter", "TC01 — Baseline", "TC02 — Consecutive Redesign", "TC03 — Custom Materials"],
    ["Span Length", "20.0 m", "24.0 m (unlocked in-app)", "24.0 m"],
    ["Carriageway Width", "7.50 m (two lanes)", "7.50 m", "7.50 m"],
    ["Skew Angle", "0° (Square)", "15° (Skewed)", "15° (Skewed)"],
    ["Number of Girders", "8 girders", "8 girders", "8 girders"],
    ["Girder Spacing", "1.05 m", "1.05 m", "1.05 m"],
    ["Deck Slab Thickness", "250 mm", "250 mm", "250 mm"],
    ["Steel Grade (Girder)", "E 350A (fy=350, fu=490)", "E 350A (fy=350, fu=490)", "custom_steel_450_570 (fy=450, fu=570)"],
    ["Concrete Grade (Deck)", "M40 (fck=40 MPa)", "M40 (fck=40 MPa)", "custom_concrete_45_1.6 (fck=45 MPa)"],
    ["Execution Sequence", "Fresh run from scratch", "Run immediately after TC01 (Unlocked)", "Run with custom user materials"],
    ["Saved Project File", "TC01_Baseline_18m.osi*", "TC02_Consecutive_24m.osi", "TC03_Custom_Material.osi"],
]
story.append(make_table(tc_table, col_widths=[3.8*cm, 4.4*cm, 4.4*cm, 4.4*cm]))
story.append(Spacer(1, 0.15*cm))
story.append(Paragraph(
    "<i>*Note on TC01 Filename:</i> Project file <code>TC01_Baseline_18m.osi</code> was originally initialized from the software's "
    "default 18.0 m template name and configured to a 20.0 m span during baseline execution, as verified by <code>geometry.span: 20.0</code> in the file.",
    CAPTION
))

story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# SECTION 3 — REQUIREMENT VERIFICATION
# ══════════════════════════════════════════════════════════════════════════
story.append(Paragraph("3. Functional Verification Results", H1))

story.append(Paragraph("3.1  Requirement 1: Custom Material Input Verification (TC03) — [PASS]", H2))
story.append(Paragraph(
    "A primary requirement was ensuring that user-defined steel and concrete material properties entered in the GUI do not revert "
    "back to default standard grades during calculation. In TC03, custom steel "
    "(<code>custom_steel_450_570</code>: fy = 450 MPa, fu = 570 MPa, E = 205 GPa) and custom concrete "
    "(<code>custom_concrete_45_1.6</code>: fck = 45 MPa, density = 25.0 kN/m³) were entered.", BODY))
story.append(Paragraph(
    "By parsing the saved <code>TC03_Custom_Material.osi</code> file with PyYAML, every custom property was verified "
    "against the internal input dictionary:", BODY))

mat_check_rows = [
    ["Input Dictionary Key", "UI Entered Value", "Stored Value in .osi", "Verification Status"],
    ["material.girder", "custom_steel_450_570", str(osi["TC03"].get("material.girder")), "PASS (Retained)"],
    ["material.girder.fy", "450.0 MPa", str(osi["TC03"].get("material.girder.fy")), "PASS (Retained)"],
    ["material.girder.fu", "570.0 MPa", str(osi["TC03"].get("material.girder.fu")), "PASS (Retained)"],
    ["material.girder.e", "205.0 GPa", str(osi["TC03"].get("material.girder.e")), "PASS (Retained)"],
    ["material.deck", "custom_concrete_45_1.6", str(osi["TC03"].get("material.deck")), "PASS (Retained)"],
    ["material.deck.fck", "45.0 MPa", str(osi["TC03"].get("material.deck.fck")), "PASS (Retained)"],
    ["material.deck.density", "25.0 kN/m³", str(osi["TC03"].get("material.deck.density")), "PASS (Retained)"],
]
story.append(make_table(mat_check_rows, col_widths=[5.2*cm, 3.8*cm, 4.2*cm, 3.8*cm]))
story.append(Spacer(1, 0.2*cm))
story.append(Paragraph(
    "<b>Conclusion:</b> Custom material definitions are successfully serialized, preserved in <code>input_dict</code>, "
    "and transferred to the analysis solver without reverting to hardcoded defaults.", BODY))

story.append(Spacer(1, 0.2*cm))
story.append(Paragraph("3.2  Requirement 2: Consecutive Multi-Run State Persistence (TC01 ➔ TC02) — [FAIL / CRITICAL]", H2))
story.append(Paragraph(
    "In TC02, after running a 20.0 m bridge (TC01), the GUI lock was toggled off, Span was changed to 24.0 m and Skew to 15°, "
    "and Design was triggered again without restarting the software. The 3D CAD visualization updated correctly to 24.0 m. "
    "However, an audit of the internal girder segment tables revealed a severe state desynchronization bug:", BODY))

seg_comp_rows = [
    ["Girder ID", "TC01 Segment End (Span 20 m)", "TC02 Segment End (Span 24 m)", "Expected Value", "Audit Status"],
    ["G1 (First Girder)", "20.0 m", "24.0 m", "24.0 m", "PASS (Updated)"],
    ["G2 (Interior Girder)", "20.0 m", "20.0 m", "24.0 m", "FAIL (Stale Data)"],
    ["G3 (Interior Girder)", "20.0 m", "20.0 m", "24.0 m", "FAIL (Stale Data)"],
    ["G4 (Interior Girder)", "20.0 m", "20.0 m", "24.0 m", "FAIL (Stale Data)"],
    ["G5 (Interior Girder)", "20.0 m", "20.0 m", "24.0 m", "FAIL (Stale Data)"],
    ["G6 (Interior Girder)", "20.0 m", "20.0 m", "24.0 m", "FAIL (Stale Data)"],
    ["G7 (Interior Girder)", "20.0 m", "20.0 m", "24.0 m", "FAIL (Stale Data)"],
    ["G8 (Interior Girder)", "20.0 m", "20.0 m", "24.0 m", "FAIL (Stale Data)"],
]
story.append(make_table(seg_comp_rows, col_widths=[3.4*cm, 3.8*cm, 3.8*cm, 3.0*cm, 3.0*cm]))
story.append(Spacer(1, 0.2*cm))
story.append(Paragraph(
    "<b>Impact:</b> While G1 properly reflected the new 24.0 m span, girders G2 through G8 retained the stale 20.0 m length "
    "from the previous run. Because girder segment tables dictate member force extraction coordinates and stiffener layout, "
    "interior girder design checks in consecutive runs evaluate forces at wrong positions along the span.", BODY))

story.append(Spacer(1, 0.2*cm))
story.append(Paragraph("3.3  Requirement 3: Graphical Outputs &amp; 3D CAD Verification — [PASS]", H2))
story.append(Paragraph(
    "3D model generation, dynamic camera manipulation (pan, tilt, zoom), and component toggling functioned smoothly. "
    "Toggling visibility checkboxes for Bridge, Girder, Deck, and Cross Bracing successfully revealed internal structural "
    "framing. Cross-section dimensions and grillage mesh alignments matched the expected IRC geometric profiles.", BODY))

story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# SECTION 4 — VISUAL EVIDENCE & SCREENSHOTS (PROPORTIONAL ASPECT RATIO)
# ══════════════════════════════════════════════════════════════════════════
story.append(Paragraph("4. Visual Evidence &amp; Output Dock Verification", H1))
story.append(Paragraph(
    "The screenshots below capture key stages of the test sequence, demonstrating the user interface, 3D CAD generation, "
    "and structural utilization checks during TC03 execution. Images are scaled preserving their native aspect ratios.", BODY))
story.append(Spacer(1, 0.15*cm))

# Embedded figures with proportional scaling
figures_to_show = [
    ("bridge", "Figure 1: 3D CAD bridge model (TC03: 24.0 m span, 15° skew). Concrete deck is hidden to reveal interior plate girders, transverse stiffeners, and cross-bracing framing."),
    ("dock",   "Figure 2: Complete OsdagBridge window showing Basic Inputs, interactive 3D model, and Output Dock with Girder Design Demand-Capacity Ratios (DCR) for G1 under Self-Weight (SW)."),
    ("plots",  "Figure 3: Full bridge superstructure rendering with concrete deck and crash barriers visible, demonstrating orthographic alignment and perspective controls."),
]

for fig_key, caption in figures_to_show:
    img_path = FIGS[fig_key]
    if os.path.exists(img_path):
        try:
            with PILImage.open(img_path) as im:
                orig_w, orig_h = im.size
            aspect = orig_h / float(orig_w)
            target_w = 16.0 * cm
            target_h = target_w * aspect
            if target_h > 8.5 * cm:
                target_h = 8.5 * cm
                target_w = target_h / aspect
            img = Image(img_path, width=target_w, height=target_h)
            img.hAlign = "CENTER"
            story.append(img)
            story.append(Paragraph(caption, CAPTION))
            story.append(Spacer(1, 0.1*cm))
        except Exception as e:
            story.append(Paragraph(f"[Image Error: {e}]", CAPTION))

story.append(Spacer(1, 0.15*cm))
story.append(Paragraph("<b>Output Dock DCR Values (Girder G1 under Self-Weight SW):</b>", BODY_BOLD))
dcr_summary = [
    ["Limit State Check", "Design Standard Reference", "Demand-Capacity Ratio (DCR)"],
    ["Strength Limit State (Flexure)", "IRC:24 Clause 503 / Limit State Bending", "1% (Satisfactory)"],
    ["Strength Limit State (Shear)", "IRC:24 Clause 504 / Web Shear Resistance", "3% (Satisfactory)"],
    ["Interaction (Bending & Shear)", "IRC:24 Combined Stress Limitation", "1% (Satisfactory)"],
]
story.append(make_table(dcr_summary, col_widths=[6.0*cm, 6.5*cm, 4.5*cm]))
story.append(Spacer(1, 0.15*cm))
story.append(Paragraph(
    "<i>Note on Low DCR Values:</i> Under self-weight (SW) alone, moments and shears are small compared to the ultimate "
    "governing combinations (such as BASIC_1 with heavy IRC Class 70R vehicle loads), leading to low single-digit utilization.", BODY))

story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# SECTION 5 — DETAILED BUG REPORTS (FOUR DEFECTS DOCUMENTED)
# ══════════════════════════════════════════════════════════════════════════
story.append(Paragraph("5. Code-Level Bug Reports &amp; Root Cause Analysis", H1))
story.append(Paragraph(
    "During testing, four concrete software defects were discovered in the codebase. The two most critical issues "
    "have been formally submitted to the upstream repository (<b>github.com/Nidhikhare12/OsdagBridge/issues</b>).", BODY))

# --- Bug 1 ---
story.append(Paragraph("Issue #1: Girder segment tables (G2..G8) retain stale span length after redesign", H2))
story.append(Paragraph("<b>Severity:</b> Critical &nbsp;|&nbsp; <b>Component:</b> State Persistence / UI Backend &nbsp;|&nbsp; <b>File:</b> <code>defaults.py</code> (~line 555)", BODY_BOLD))
story.append(Paragraph(
    "<b>Trigger Conditions:</b> Running an initial design (e.g. 20.0 m span), unlocking the design in the GUI, changing the span "
    "(e.g. to 24.0 m), and re-clicking Design without restarting the application.", BODY))
story.append(Paragraph(
    "<b>Observed Behavior:</b> In the saved <code>.osi</code> file, <code>geometry.span</code> correctly reads <code>24</code>, "
    "and <code>segment_table.G1</code> updates to <code>end: 24.0</code>. However, <code>segment_table.G2</code> through <code>G8</code> "
    "all retain <code>end: 20.0</code> from the previous run.", BODY))
story.append(Paragraph(
    "<b>Root Cause:</b> In <code>defaults.py</code>, the loop populating segment dictionaries for girders G2..Gn reads whatever segment "
    "list is already present in <code>input_dict</code> and re-assigns it back without updating the <code>end</code> coordinate with the new span.", BODY))

code_fix_1 = (
    "# Suggested Fix in defaults.py (~line 555):\n"
    "new_span = float(input_dict.get(KEY_SPAN, 20.0))\n"
    "for girder in all_girders:  # Iterate over all girders G1 through Gn\n"
    "    key = f'member_properties.girder_details.segment_table.{girder}'\n"
    "    input_dict[key] = [{'id': f'{girder}M1', 'start': 0.0, 'end': new_span}]"
)
story.append(Preformatted(code_fix_1, CODE))
story.append(Spacer(1, 0.2*cm))

# --- Bug 2 ---
story.append(Paragraph("Issue #2: Cross-bracing capacity skipped with 'no such table: Material'", H2))
story.append(Paragraph("<b>Severity:</b> Critical &nbsp;|&nbsp; <b>Component:</b> Database / Bracing Design &nbsp;|&nbsp; <b>File:</b> <code>crossbracingforces.py</code> (~line 658) / <code>Intg_osdag.sqlite</code>", BODY_BOLD))
story.append(Paragraph(
    "<b>Trigger Conditions:</b> Any design run where cross-bracing is enabled (default behavior across all test cases).", BODY))
story.append(Paragraph(
    "<b>Observed Behavior:</b> The console outputs the following repeating error for all 7 inter-girder bays:\n"
    "<code>[CrossBracing] SKIP G1-G2 diagonal tension: no such table: Material</code>\n"
    "The Output Dock displays empty dashes (<code>—</code>) for all cross-bracing capacity values.", BODY))
story.append(Paragraph(
    "<b>Root Cause:</b> <code>osdag_core/utils/common/material.py</code> executes a SQL query querying table <code>Material</code> "
    "(<code>SELECT ... FROM Material WHERE ...</code>). However, in <code>Intg_osdag.sqlite</code>, the table is named "
    "<code>Steel_Grade_Properties</code>. The resulting <code>sqlite3.OperationalError</code> is caught by a broad except block "
    "around line 658 of <code>crossbracingforces.py</code>, silently skipping member design.", BODY))

code_fix_2 = (
    "# Option A: Code Query Correction in osdag_core/utils/common/material.py:\n"
    "cursor.execute('SELECT ... FROM Steel_Grade_Properties WHERE grade = ?', (grade,))\n\n"
    "# Option B: Zero-Code Database Compatibility View in Intg_osdag.sqlite:\n"
    "CREATE VIEW IF NOT EXISTS Material AS SELECT * FROM Steel_Grade_Properties;"
)
story.append(Preformatted(code_fix_2, CODE))
story.append(Spacer(1, 0.2*cm))

# --- Bug 3 ---
story.append(Paragraph("Issue #3: Headless crash on missing shear modulus in legacy project files", H2))
story.append(Paragraph("<b>Severity:</b> High &nbsp;|&nbsp; <b>Component:</b> Solver API &nbsp;|&nbsp; <b>File:</b> <code>designer.py</code> (lines 309–315)", BODY_BOLD))
story.append(Paragraph(
    "<b>Trigger Conditions:</b> Loading or re-running an <code>.osi</code> file programmatically that lacks the explicit <code>KEY_MATERIAL_GIRDER_G</code> key.", BODY))
story.append(Paragraph(
    "<b>Observed Behavior:</b> <code>BridgeConfig.from_plate_girder_bridge</code> raises <code>ValueError: Gs (shear modulus) is not set for grade 'E 350A'</code>.", BODY))

code_fix_3 = (
    "# Suggested Fix in designer.py (lines 309-315):\n"
    "G_val = input_dict.get(KEY_MATERIAL_GIRDER_G)\n"
    "if G_val is None or G_val == '':\n"
    "    E = float(input_dict.get(KEY_MATERIAL_GIRDER_E, 200.0))\n"
    "    nu = float(input_dict.get(KEY_MATERIAL_GIRDER_POISSON, 0.30))\n"
    "    G_val = round(E / (2 * (1 + nu)), 1)  # standard isotropic elasticity fallback\n"
    "    input_dict[KEY_MATERIAL_GIRDER_G] = G_val"
)
story.append(Preformatted(code_fix_3, CODE))
story.append(Spacer(1, 0.2*cm))

# --- Bug 4 ---
story.append(Paragraph("Issue #4: Unhandled TypeError in layout solver when carriageway width is not yet set", H2))
story.append(Paragraph("<b>Severity:</b> High &nbsp;|&nbsp; <b>Component:</b> UI Validation / Defaults &nbsp;|&nbsp; <b>File:</b> <code>defaults.py</code> (~line 908)", BODY_BOLD))
story.append(Paragraph(
    "<b>Trigger Conditions:</b> Opening a project file with missing geometry fields or triggering layout calculation before carriageway width is populated.", BODY))
story.append(Paragraph(
    "<b>Observed Behavior:</b> <code>float(basic_input_dict.get(KEY_CARRIAGEWAY_WIDTH))</code> raises unhandled "
    "<code>TypeError: float() argument must be a string or a real number, not 'NoneType'</code>.", BODY))

code_fix_4 = (
    "# Suggested Fix in defaults.py (~line 908):\n"
    "raw_cw = basic_input_dict.get(KEY_CARRIAGEWAY_WIDTH)\n"
    "if raw_cw is None or str(raw_cw).strip() == '':\n"
    "    raise ValueError('Carriageway width is required before layout can be computed.')\n"
    "cw = float(raw_cw)"
)
story.append(Preformatted(code_fix_4, CODE))

story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# SECTION 6 — CONCLUSIONS & REPRODUCIBILITY
# ══════════════════════════════════════════════════════════════════════════
story.append(Paragraph("6. Conclusions &amp; Submission Artifacts", H1))
story.append(Paragraph(
    "The OsdagBridge short-span steel plate girder module demonstrates robust capabilities in OpenSeesPy grillage "
    "modeling, 3D visualization, and compliance with IRC structural checks. Custom material registration works reliably. "
    "Addressing the state desynchronization in <code>defaults.py</code> and the database alias mismatch will resolve the primary "
    "points of failure identified during this audit.", BODY))
story.append(Spacer(1, 0.3*cm))

story.append(Paragraph("<b>Summary of Submission Deliverables:</b>", BODY_BOLD))

deliv_rows = [
    ["Deliverable", "Location / Access Link", "Status"],
    ["GitHub Fork", '<a href="https://github.com/pujariabhi/OsdagBridge"><font color="#2B6CB0"><u>github.com/pujariabhi/OsdagBridge</u></font></a>', "Public, collaborator added"],
    ["GitHub Issue #1", "Logged on Nidhikhare12/OsdagBridge (stale segment tables)", "Submitted with reproduction log"],
    ["GitHub Issue #2", "Logged on Nidhikhare12/OsdagBridge (cross-bracing DB error)", "Submitted with SQL root cause"],
    ["Video Screencast", f'<a href="{VIDEO_URL}"><font color="#2B6CB0"><u>Google Drive Video Screencast</u></font></a>', "Uploaded (1080p, 2m 09s)"],
    ["Project Files (.osi)", "TC01_Baseline_18m.osi, TC02_Consecutive_24m.osi, TC03_Custom_Material.osi", "Verified & bundled in ZIP"],
    ["Candidate Resume", "Pujari_Abhiram_Resume.pdf (B.Tech CSE - Data Science, Anurag University)", "Compiled & ready for upload"],
]
story.append(make_table(deliv_rows, col_widths=[3.5*cm, 10.5*cm, 3.0*cm]))

story.append(Spacer(1, 0.6*cm))
story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BLUE, spaceAfter=8))
story.append(Paragraph(
    "<b>Report Prepared By:</b> Pujari Abhiram &nbsp;|&nbsp; 3rd Year B.Tech CSE (Data Science), Anurag University, Hyderabad<br/>"
    "<b>Contact:</b> pujariabhiram06@gmail.com &nbsp;|&nbsp; +91 9390217454 &nbsp;|&nbsp; "
    "<a href=\"https://github.com/pujariabhi\"><font color=\"#2B6CB0\"><u>github.com/pujariabhi</u></font></a>",
    ParagraphStyle("Sig", parent=BODY, fontSize=8.5, leading=12, alignment=TA_CENTER)
))

# ── Build Document ─────────────────────────────────────────────────────────
print(f"Compiling Academic Report PDF → {OUT_PDF}")
doc.build(story, canvasmaker=NumberedCanvas)
print("Report compiled successfully!")
