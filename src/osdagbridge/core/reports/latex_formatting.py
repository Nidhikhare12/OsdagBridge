
from osdagbridge.core.reports.report_utils import _tex


def preamble(project_name, job_number, report_date, report_version='Rev 0'):
    pn = _tex(project_name)
    jn = _tex(job_number)
    rd = _tex(report_date)
    rv = _tex(report_version)

    return r"""
\documentclass[12pt,a4paper]{report}

% Packages
\usepackage[a4paper, margin=1in]{geometry}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{caption}

\captionsetup{
    labelfont=bf,
    justification=raggedright,
    singlelinecheck=false,
    format=plain
}
\usepackage{subcaption}
\usepackage{multirow}
\usepackage{colortbl}
\usepackage{longtable}
\setlength{\LTleft}{\fill}
\setlength{\LTright}{\fill}
\usepackage{titlesec}
\usepackage{titletoc}
\usepackage{lastpage}
\usepackage{makecell}
\usepackage{etoolbox}
\usepackage{needspace}

\numberwithin{table}{chapter}
\numberwithin{figure}{chapter}

% Table layout and spacing
\setlength{\tabcolsep}{6pt}
\renewcommand{\arraystretch}{1.12}
\setlength{\LTpre}{0pt}
\setlength{\LTpost}{6pt}
\setlength{\arrayrulewidth}{0.5pt}
\setlength{\extrarowheight}{0.6pt}

% Prevent tables from overflowing past the page bottom
\BeforeBeginEnvironment{table}{\needspace{5\baselineskip}}
\BeforeBeginEnvironment{longtable}{\needspace{5\baselineskip}}

\definecolor{osdagGreen}{HTML}{91B014}
\setlength{\headheight}{28pt}
\fancypagestyle{main}{
  \fancyhf{}
  \fancyhead[L]{\small\parbox[b]{0.60\headwidth}{\raggedright """ + pn + r""" $|$ """ + jn + r"""}}
  \fancyhead[R]{\small\parbox[b]{0.34\headwidth}{\raggedleft """ + rd + r""" $|$ """ + rv + r"""}}
  \fancyfoot[L]{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{Page \thepage\\ of \pageref{LastPage}}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vspace{-20pt}%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
      \vspace{4pt}%
    }{%
      \vspace{-8pt}%
    }%
    \color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}%
  }
}
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{\small\parbox[b]{0.60\headwidth}{\raggedright """ + pn + r""" $|$ """ + jn + r"""}}
  \fancyhead[R]{\small\parbox[b]{0.34\headwidth}{\raggedleft """ + rd + r""" $|$ """ + rv + r"""}}
  \fancyfoot[L]{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vspace{-20pt}%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
      \vspace{4pt}%
    }{%
      \vspace{-8pt}%
    }%
    \color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}%
  }
}
\fancypagestyle{firstpage}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \fancyfoot[L]{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{}
  \renewcommand{\footrule}{\vspace{-8pt}\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}}
}
\pagestyle{main}
\setstretch{1.15}

% Custom Commands
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

% Software-default asterisk
\newcommand{\sdstar}{\textsuperscript{*}}
\newbool{hasSDonPage}
\boolfalse{hasSDonPage}
\newcommand{\markSD}{\global\booltrue{hasSDonPage}}
\renewcommand{\sdstar}{\textsuperscript{*}\markSD{}}
\AddToHook{shipout/before}{\global\boolfalse{hasSDonPage}}

\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{2cm} \large Design Report}
\author{}
\date{}

\begin{document}
"""
