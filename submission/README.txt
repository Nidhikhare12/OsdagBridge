OsdagBridge Report Generator — submission pack (local, git-ignored)

IF ONLY ONE PDF AND ONE VIDEO ARE ALLOWED:
  PDF   -> OsdagBridge_Submission.pdf
           (merged: Technical Report + Report_Before + Report_After + Report_Real_Design)
  VIDEO -> Demo_Video_1080p.mp4
           (upload as unlisted YouTube; silent 1920x1080, 75 s)

Individual PDFs also included:
  Technical_Report.pdf      technical changes document
  Report_Before.pdf         baseline output
  Report_After.pdf          enhanced output (all six fixes)
  Report_Real_Design.pdf    full real OpenSees design verification

Supporting video:
  Demo_Live_X11_1080p.mp4   34 s real-time Xvfb/X11 capture (optional second link)

images/  — key screenshots for the PR description / report:
  ci_before_after.png   before vs after load tables
  ur_chart.png          UR chart with 1.0 threshold
  material_chart.png    Chapter 7 quantity charts
  real_page30.png       G4 rows clear of footer
  gui_window.png        real desktop UI
  live_preview.png      in-app live PDF preview

Full artefact set (all PDFs, videos, screenshots, .tex sources, ZIP) is in ../deliverables/.
CI publishes every built PDF to https://github.com/danish9661/OsdagBridge/tree/ci-reports
