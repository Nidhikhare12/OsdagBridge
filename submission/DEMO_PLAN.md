# Demonstration script

Target length is 3 minutes 45 seconds. Use the actual application, input, reports and terminal. Mark any cut during the analysis.

**0:00–0:25 — Project and input**

Open the OsdagBridge desktop application. Load submission/test-design.osi. Show the 30 m span, 7.5 m carriageway, four girders and Mumbai location.

Say: “This test bridge has failing structural checks. The same saved input is used for the baseline and enhanced reports.”

**0:25–0:55 — Analysis**

Click Design. Show the running progress, make a clearly marked time cut, then show the completed analysis log and girder failure.

Say: “The application performs the structural analysis. The report presents the results produced by that run.”

**0:55–1:20 — Generate report**

Open Design Report, select all chapters, figures and the table of contents, and save a fresh PDF. Show the completed report.

**1:20–1:55 — Headers, footer and dimensions**

Open the baseline and enhanced reports. Show the stiffener continuation on enhanced pages 31–32, then the single girder summary heading on page 35. Show the 1670 mm girder depth in Chapter 2.

Say: “Every stiffener row carries its own girder label, and repeated headers are generated for continuation pages.”

**1:55–2:25 — Load tables**

Show the separate vehicle and footpath tables in Chapter 3. Open the alternate-input evidence and show the selected Class A and 70R Tracked values and custom footpath setting.

Say: “The report identifies these as configured inputs. The current solver has limitations in applying the selected vehicles and custom pressure.”

**2:25–3:00 — Checks and chart**

Show the bracing table, the overall summary and the vertical component chart and horizontal red 1.0 limit in Chapter 5. Point out 0.740 and 0.610 as stored Osdag efficiencies and the unavailable matching capacities and statuses. Show the failing girder ratio and unavailable diaphragm entry.

Say: “The export does not identify which denominator produced each bracing efficiency. The chart therefore marks the verified bracing ratio unavailable. The deck chart uses a reinforcement crack-control check, while the table also reports a separate crack-width check.”

**3:00–3:20 — Quantities and styling**

Show the Chapter 7 material table and chart, the estimated reinforcement label, and the unavailable diaphragm weight. Point out the consistent footer, headings and spacing.

**3:20–3:45 — Tests and evidence**

Show the actual pytest output and the preserved logs, report TeX and asset directory.

Say: “The regression suite includes real pdfTeX compilation and checks repeated headers, pagination, report result mapping and missing values. The evidence package records the source commit and report hash.”
