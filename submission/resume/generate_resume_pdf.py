"""
Professional Resume Generator for Pujari Abhiram
Outputs: resume.pdf (clean, authentic 1-page format with clickable hyperlinks)
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

OUT_PDF = r"C:\Users\PUJARI ABHIRAM\Projects\resume\Pujari_Abhiram_Resume.pdf"

# ── Color Palette (Sophisticated Navy & Slate) ──────────────────────────────
COLOR_PRIMARY   = colors.HexColor("#1A365D")  # Deep Navy
COLOR_SECONDARY = colors.HexColor("#2B6CB0")  # Slate Blue for Links & Accents
COLOR_DARK      = colors.HexColor("#2D3748")  # Charcoal for Body Text
COLOR_MUTED     = colors.HexColor("#718096")  # Muted Grey for Dates / Locations
COLOR_LINE      = colors.HexColor("#CBD5E0")  # Soft Divider Line

styles = getSampleStyleSheet()

STYLE_NAME = ParagraphStyle(
    "Name",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=17,
    leading=21,
    alignment=TA_CENTER,
    textColor=COLOR_PRIMARY
)

STYLE_CONTACT = ParagraphStyle(
    "Contact",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.3,
    leading=11.5,
    alignment=TA_CENTER,
    textColor=COLOR_DARK
)

STYLE_SECTION = ParagraphStyle(
    "SectionTitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=12,
    textColor=COLOR_PRIMARY,
    spaceAfter=1.5,
    spaceBefore=3
)

STYLE_JOB_TITLE = ParagraphStyle(
    "JobTitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8.7,
    leading=10.5,
    textColor=COLOR_PRIMARY
)

STYLE_JOB_META = ParagraphStyle(
    "JobMeta",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.2,
    leading=10.5,
    alignment=TA_RIGHT,
    textColor=COLOR_MUTED
)

STYLE_BODY = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.0,
    leading=10.2,
    alignment=TA_LEFT,
    textColor=COLOR_DARK
)

STYLE_BULLET = ParagraphStyle(
    "Bullet",
    parent=STYLE_BODY,
    leftIndent=9,
    firstLineIndent=-6,
    spaceAfter=1.2
)

def section_header(title):
    return [
        Spacer(1, 1),
        Paragraph(title.upper(), STYLE_SECTION),
        HRFlowable(width="100%", thickness=0.8, color=COLOR_SECONDARY, spaceAfter=2.5, spaceBefore=0.5),
    ]

def two_column_header(left_html, right_html):
    t = Table(
        [[Paragraph(left_html, STYLE_JOB_TITLE), Paragraph(right_html, STYLE_JOB_META)]],
        colWidths=[5.4 * inch, 2.1 * inch]
    )
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
    ]))
    return t

doc = SimpleDocTemplate(
    OUT_PDF,
    pagesize=letter,
    topMargin=0.32 * inch,
    bottomMargin=0.32 * inch,
    leftMargin=0.45 * inch,
    rightMargin=0.45 * inch,
    title="Pujari Abhiram - Resume",
    author="Pujari Abhiram"
)

story = []

# ── Header ──────────────────────────────────────────────────────────────────
story.append(Paragraph("PUJARI ABHIRAM", STYLE_NAME))
story.append(Spacer(1, 1.5))

contact_line = (
    '+91 9390217454 &nbsp;|&nbsp; '
    '<a href="mailto:pujariabhiram06@gmail.com"><font color="#2B6CB0"><u>pujariabhiram06@gmail.com</u></font></a> &nbsp;|&nbsp; '
    '<a href="https://github.com/pujariabhi"><font color="#2B6CB0"><u>github.com/pujariabhi</u></font></a> &nbsp;|&nbsp; '
    '<a href="https://www.linkedin.com/in/pujari-abhiram-92a658372/"><font color="#2B6CB0"><u>linkedin.com/in/pujari-abhiram</u></font></a> &nbsp;|&nbsp; '
    'Hyderabad, India'
)
story.append(Paragraph(contact_line, STYLE_CONTACT))

# ── Education ───────────────────────────────────────────────────────────────
story.extend(section_header("Education"))

story.append(two_column_header(
    "<b>Anurag University</b> &mdash; B.Tech in Computer Science &amp; Engineering (Data Science)",
    "2024 &ndash; 2028 | Hyderabad"
))
story.append(Paragraph("&bull; <i>Third Year (Semester 3-1)</i> &nbsp;|&nbsp; Coursework: Data Structures, Machine Learning, DBMS, Applied Statistics, Discrete Math", STYLE_BULLET))

story.append(two_column_header(
    "<b>Narayana Junior College</b> &mdash; Intermediate (Class XII, MPC)",
    "2022 &ndash; 2024 | Hyderabad"
))
story.append(Paragraph("&bull; Aggregate: <b>93.9%</b> &nbsp;|&nbsp; State Board of Intermediate Education, Telangana", STYLE_BULLET))

story.append(two_column_header(
    "<b>Narayana School</b> &mdash; Secondary School Certificate (Class X)",
    "2022 | Nandigama"
))
story.append(Paragraph("&bull; Academic Performance: <b>GPA 9.7 / 10.0</b>", STYLE_BULLET))

# ── Experience & Open Source Contributions ──────────────────────────────────
story.extend(section_header("Experience & Open Source Contributions"))

story.append(two_column_header(
    "<b>Open Source Contributor &amp; Module Tester</b> &mdash; <i>FOSSEE / Osdag, IIT Bombay</i>",
    "<a href=\"https://github.com/pujariabhi/OsdagBridge\"><font color=\"#2B6CB0\"><u>github.com/pujariabhi/OsdagBridge</u></font></a>"
))
story.append(Paragraph(
    "&bull; Executed end-to-end testing and validation of the <b>OsdagBridge</b> short-span steel plate girder module, verifying grillage finite element analysis (OpenSeesPy) and limit state capacity checks against IRC:6 and IRC:24 design codes.",
    STYLE_BULLET
))
story.append(Paragraph(
    "&bull; Discovered and formally reported 4 code-level defects on upstream (<code>Nidhikhare12/OsdagBridge</code>), including a critical state-persistence bug in girder segment tables (<code>defaults.py</code>) and SQLite table alias mismatches in cross-bracing design.",
    STYLE_BULLET
))
story.append(Paragraph(
    "&bull; Authored a 9-section technical verification report with dictionary diff audits (<code>input_dict</code> vs <code>output_dict</code>) and compiled an open reproduction test suite with 3D CAD visualization benchmarks.",
    STYLE_BULLET
))

story.append(two_column_header(
    "<b>Data Analytics Virtual Intern</b> &mdash; <i>EduSkills &amp; AICTE (Supported by Google Cloud)</i>",
    "Apr 2026 &ndash; Jun 2026"
))
story.append(Paragraph(
    "&bull; Completed an 8-week structured virtual internship covering data ingestion, exploratory data analysis, and dashboard generation; earned Google Cloud Data Analytics credential (Cert ID: <code>4d43b5aafe37dcf5dce7</code>).",
    STYLE_BULLET
))

story.append(two_column_header(
    "<b>AI &amp; Machine Learning Trainee</b> &mdash; <i>iHub-Data, IIIT Hyderabad</i>",
    "May 2025 &ndash; Sep 2025"
))
story.append(Paragraph(
    "&bull; Selected for a 5-month intensive training program conducted at IIIT Hyderabad covering supervised/unsupervised machine learning, neural architectures, data preprocessing pipelines, and practical model evaluation.",
    STYLE_BULLET
))

# ── Projects ────────────────────────────────────────────────────────────────
story.extend(section_header("Technical Projects"))

story.append(two_column_header(
    "<b>Delivery Optimizer: Dynamic Routing &amp; Predictive ETA</b>",
    "<a href=\"https://github.com/pujariabhi/delivery-optimizer\"><font color=\"#2B6CB0\"><u>github.com/pujariabhi/delivery-optimizer</u></font></a>"
))
story.append(Paragraph(
    "&bull; Developed a full-stack real-time last-mile delivery optimization platform using Java 17, Spring Boot 3, React 18, and TypeScript; containerized deployment with Docker and Docker Compose.",
    STYLE_BULLET
))
story.append(Paragraph(
    "&bull; Implemented dynamic vehicle routing algorithms and predictive ETA calculations factoring in simulated traffic conditions and dispatch constraints.",
    STYLE_BULLET
))

story.append(two_column_header(
    "<b>Hugging Face NLP &amp; Vision Pipelines</b> &mdash; <i>Transformers, Diffusers, PyTorch</i>",
    "Applied Machine Learning"
))
story.append(Paragraph(
    "&bull; <b>NLP Pipeline:</b> Implemented abstractive text summarization and context-aware extractive question answering pipelines using pretrained Hugging Face transformer models; optimized tokenization and inference latency.",
    STYLE_BULLET
))
story.append(Paragraph(
    "&bull; <b>Vision &amp; Multimodal:</b> Built text-to-image synthesis workflows using Hugging Face Diffusers alongside Vision-Language models for automated image captioning (image-to-text).",
    STYLE_BULLET
))

story.append(two_column_header(
    "<b>Interactive Business Intelligence Dashboard</b> &mdash; <i>Qlik Sense, Associative Data Modeling</i>",
    "Analytics &amp; BI"
))
story.append(Paragraph(
    "&bull; Designed and deployed multi-dimensional analytical dashboards on Qlik Sense; modeled relational data schemas, calculated custom KPI expressions, and identified business trend anomalies.",
    STYLE_BULLET
))

# ── Certifications ──────────────────────────────────────────────────────────
story.extend(section_header("Certifications & Verified Credentials"))

cert_lines = [
    ("Qlik Data Analytics Certification &mdash; <i>Qlik</i> (Score: 88%, Exam ID: 434437571)", "https://www.credly.com/go/wVkshYIr"),
    ("Qlik Data Literacy Certification &mdash; <i>Qlik</i> (Foundational & Applied Analytics)", "https://www.credly.com/go/YIUtHApx"),
    ("Probability &amp; Statistics using Python &mdash; <i>Infosys Springboard</i>", "https://verify.onwingspan.com"),
    ("Introduction to MongoDB &mdash; <i>MongoDB, Inc.</i> (Credential: MDBfmm28lobcu)", None),
    ("Data Science 101 &mdash; <i>IBM SkillsBuild &amp; Developer Skills Network</i> (DS0101EN)", "https://courses.skillsbuild.skillsnetwork.site/certificates/e74221c8e09c42d09bbd9e515aa4cf78"),
    ("Data Fundamentals &mdash; <i>IBM SkillsBuild</i> (Credential: PLAN-BC0FAEE8E439)", None),
    ("Learn Programming with Java &mdash; <i>IBM SkillsBuild &amp; OpenClassrooms</i> (15 Hours)", None),
    ("Introduction to Data Science &amp; Networking Basics &mdash; <i>Cisco Networking Academy</i>", None),
]

for cert_text, url in cert_lines:
    if url:
        p_text = f"&bull; {cert_text} &nbsp;[<a href=\"{url}\"><font color=\"#2B6CB0\"><u>Verify</u></font></a>]"
    else:
        p_text = f"&bull; {cert_text}"
    story.append(Paragraph(p_text, STYLE_BULLET))

# ── Technical Skills ────────────────────────────────────────────────────────
story.extend(section_header("Technical Skills"))

skills_data = [
    [Paragraph("<b>Programming:</b>", STYLE_BODY), Paragraph("Python (NumPy, Pandas, Scikit-learn), Java, TypeScript, C, SQL", STYLE_BODY)],
    [Paragraph("<b>ML &amp; Frameworks:</b>", STYLE_BODY), Paragraph("Hugging Face (Transformers, Diffusers), PyTorch, Spring Boot, React, OpenSeesPy", STYLE_BODY)],
    [Paragraph("<b>Databases &amp; BI:</b>", STYLE_BODY), Paragraph("MySQL, MongoDB, SQLite, Qlik Sense (Associative Modeling &amp; KPI Design)", STYLE_BODY)],
    [Paragraph("<b>Developer Tools:</b>", STYLE_BODY), Paragraph("Git, GitHub, Docker, Docker Compose, Linux/Windows CLI, ReportLab, LaTeX", STYLE_BODY)],
]

t_skills = Table(skills_data, colWidths=[1.3 * inch, 6.2 * inch])
t_skills.setStyle(TableStyle([
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('LEFTPADDING', (0,0), (-1,-1), 2),
    ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ('TOPPADDING', (0,0), (-1,-1), 0.5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
]))
story.append(t_skills)

doc.build(story)
print(f"Resume generated successfully at: {OUT_PDF}")
