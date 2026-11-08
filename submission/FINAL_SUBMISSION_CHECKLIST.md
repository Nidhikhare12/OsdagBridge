# Final FOSSEE submission checklist

The public Winter 2026 announcement lists **23 November 2026** as the registration and submission deadline. The public Osdag instructions request a resume PDF, video URL, report PDF and supporting ZIP. The submission form returned HTTP 401 during verification, so its precise fields, access requirements and validation cannot be independently confirmed.

- Winter announcement and registration: https://fossee.in/winter-internship/2026
- Osdag screening instructions: https://docs.google.com/document/d/e/2PACX-1vQqqS1s2_iLuFEb-Kb0qj2yU7200dCd9kG6EB3Y71c-jtzFnredQPAaQr699z3YaIAEYaQmRw8ymju9/pub
- Submission form: https://docs.google.com/forms/d/e/1FAIpQLSdED-LhYmCoaI6AkLBfhfnRjS_LSNf-KX88vLQqej4-oKsdZw/viewform
- Official task: https://docs.google.com/document/d/1CkrRTk1bH3JnEhLIM8RMJodouv-yUlIx/edit
- Applicant fork: https://github.com/Trunal2005/OsdagBridge

| Item | Local path or URL | Status and manual action |
| --- | --- | --- |
| Source repository | C:/Internship Task/fosses/osdag-bridge/OsdagBridge | Local branch prepared. A read-only check on 9 November found that the feature branch is absent on origin. Push it yourself, then check reviewer access. |
| Baseline report | C:/Internship Task/fosses/osdag-bridge/OsdagBridge/submission/Report_Before.pdf | Preserved baseline. Include in supporting ZIP and any relevant form field. |
| Enhanced report | C:/Internship Task/fosses/osdag-bridge/OsdagBridge/submission/Report_After.pdf | Generated report. Include in supporting ZIP and any relevant form field. |
| Technical changes report | C:/Internship Task/fosses/osdag-bridge/OsdagBridge/submission/Technical_Changes_Report.pdf | Six-page report with genuine side-by-side evidence. Provide in the report PDF field if appropriate. |
| Supporting ZIP | C:/Internship Task/fosses/osdag-bridge/OsdagBridge/submission/OsdagBridge_FOSSEE_Submission.zip | Upload as supporting files. Verify form limits and fields. |
| Resume PDF | No verified file located | Supply your own current PDF as submission/Resume.pdf and upload it in the resume field. Describe only verified education, skills and projects. |
| Demonstration video URL | Not yet created | Follow submission/DEMO_PLAN.md. Record the actual app, upload to YouTube or cloud storage, and submit the shareable URL. The public instructions allow a silent video. |
| Declaration or NOC PDF | No verified signed document | The Osdag instructions list an undertaking, self-declaration or NOC and say it can be submitted after selection, with NOC mandatory for semester-long internships. The authenticated form could not be checked. Verify the applicable requirement and provide the genuine document if requested. |
| Reviewer access | GitHub repository settings | Invite Nidhikhare12 yourself if the applicable task instructions require it. Confirm acceptance and access. |
| Form submission | Submission form link above | Review all fields, attach files and submit manually. No submission has been made. |

## Publication steps

1. Inspect the local changes and commit history with `git status --short` and `git log --oneline`.
2. When you are ready, run `git push -u origin feat/fossee-latex-reports`.
3. Open the fork on GitHub and select the feature branch. Check that the changed source, tests, and tracked documentation appear. Generated report PDFs and the ZIP are separate upload artifacts unless deliberately added.
4. In the repository settings, check reviewer visibility and invite the specified collaborator if required. Confirm access before submitting the link.
5. Use the branch URL `https://github.com/Trunal2005/OsdagBridge/tree/feat/fossee-latex-reports` only after verifying that the push succeeded.

## Suggested project description

Refactored the OsdagBridge LaTeX report pipeline to repeat table headers, improve pagination and layout, separate live-load inputs, visualize verified component utilization and material quantities, and centralize report styles. Added report-generation and real pdfTeX regression checks. The reports document unavailable cross-bracing and diaphragm ratios and preserve the test design's failing girder checks.


## Resume and recording

A targeted search of the workspace, Desktop and Documents did not identify a resume PDF. Tailor your own resume to the software-development task using only experience you can substantiate. The supplied technical report already identifies your confirmed education and GitHub account.

No local video or video URL was produced. Follow DEMO_PLAN.md for the screen-by-screen script, 1920 × 1080 recording setup, time-cut labeling and quality checks.
