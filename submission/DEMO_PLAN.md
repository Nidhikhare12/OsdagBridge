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


## Capture setup

- Record a 1920 × 1080 display at 30 frames per second. Set Windows display scaling and the application window so text remains readable.
- Keep the application and PDF viewer maximized. For the PDF, use approximately 125–150% zoom and pan to the table, footer or chart being discussed.
- Open the baseline PDF, the final PDF, the six-page technical report, and a terminal at the repository root before recording.
- Use the actual successful test log at submission/evidence/pytest.log or run the documented command in the supported environment. Show the real output.
- Use a visible caption such as “Analysis in progress — time cut” before a cut and “Analysis completed” after it. Keep the original log available.
- A voiceover is optional. The spoken lines above can instead appear as on-screen captions.

## Screen and caption checklist

| Time | Screen or exact page | Suggested caption |
| --- | --- | --- |
| 0:00–0:25 | Desktop input dock after loading submission/test-design.osi | “Saved 30 m test bridge” |
| 0:25–0:55 | Design progress and completed output | “Actual analysis; time cut shown” |
| 0:55–1:20 | Report options and newly generated PDF | “Application report generation” |
| 1:20–1:55 | Technical report pages 5–6, then final PDF pages 9, 31–32 and 35 | “Continuation headers, footer clearance, dimensions” |
| 1:55–2:25 | Final PDF pages 13–14 and the alternate-input evidence | “Configured inputs and available analysis data” |
| 2:25–3:00 | Final PDF pages 42–45 | “Recorded efficiencies; verified ratios only” |
| 3:00–3:20 | Final PDF pages 51–52, then src/osdagbridge/core/reports/styles.py | “BOQ quantities; reinforcement estimated” |
| 3:20–3:45 | submission/evidence/pytest.log, git log and source tree | “24 tests passed; local feature branch” |

## Before publishing the recording

- Replay the entire local file. Confirm that the correct application, PDF and terminal are legible.
- Confirm that analysis cuts are marked and no scene implies that unavailable ratios passed.
- Check audio if present. A silent recording is acceptable according to the public Osdag instructions.
- Verify that no unrelated notifications, private tabs, credentials, or personal files appear.
- Confirm that the final file opens and that the selected hosting permissions permit reviewers to view it.
- Save the local recording and obtain a shareable URL yourself.
