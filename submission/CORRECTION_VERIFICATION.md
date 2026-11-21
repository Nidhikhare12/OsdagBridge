# Cross-bracing correction

The captured G1–G2 diagonal demand is 8.049 kN and the exported efficiency is 0.740. The chord demand is 6.669 kN and the efficiency is 0.610. The previously displayed capacities 16.810 and 22.140 kN were read from Member.tension_capacity. Their direct quotients are 0.4788 and 0.3012 respectively, rather than the exported efficiencies. The export does not establish those capacities as the denominators of the compression checks.

The installed osdag_core compression_bolted.py assigns self.efficiency from axial force divided by member compression capacity at lines 1855 and 2370. It also assigns self.efficiency from axial force divided by the smaller of bolt-group and plate capacity at line 2146. The exported dictionary does not indicate which assignment or denominator produced each retained efficiency. The exact basis of 0.740 and 0.610 remains unresolved.

Chapter 5 displays the captured efficiencies as exported Osdag values, the analysed demands in kN, and unavailable matching capacities and statuses. The overall summary and chart do not represent these efficiencies as verified demand/capacity ratios. The compression result reader does not map Member.tension_capacity as a compression capacity. A component whose checks lack a verified basis is marked unavailable.

The deck chart uses composite minimum crack-control reinforcement divided by provided reinforcement. The crack-width check uses calculated crack width divided by the permitted crack width. These are distinct checks. Diaphragm results are unavailable in the supplied analysis.

This correction retains the recorded girder failures and keeps structural solver behavior unchanged.


Osdag also computes a minimum connection design force using 30 percent of member compression capacity. This intermediate computation does not identify which final denominator was retained for the captured efficiency.

The earlier corrected desktop report was produced from source commit d6fe841e7e50069b15998aba5483e91c5586dd30. Both pdfTeX passes returned zero. Its SHA-256 is e9895d685304129016bffa8aef839b6b087329ec9380cb4805ddbe5bab6ae551. All 57 pages were rendered and visually reviewed. The bracing table is on physical pages 42–43 and the chart is on page 45. The G4 stiffener continuation remains above the footer on pages 31–32 and the girder summary has one header on page 35.

The Python 3.12 test suite reported 23 passed, including real pdfTeX pagination and generated Chapter 5 tests. Two additional portable compilation passes succeeded and produced matching text and raster output on all 57 pages. The compiler log contains 13 overfull box notices and 20 recovered infinite glue notices. The page review and geometry scan found no footer crossing or clipping associated with these notices. No missing-character notice was emitted.

Requirement 3 remains partial because the solver does not consistently apply the selected vehicle and custom footpath settings. Requirement 4 remains partial because the bracing efficiency denominator is unresolved and end-diaphragm checks were not produced. The official task document exposed only its title through the accessible browser response. The six requirement descriptions in the supplied request informed the review.

An earlier concurrent test attempt emitted Windows native exception 0xc0000008. The subsequent serial test completed successfully. An initial sandboxed desktop attempt slowed in the Osdag design pool. The final successful desktop run used the existing environment outside the sandbox. Analysis still emitted thermal load warnings.

The applicant must record the demonstration, provide any required resume or institution NOC, and decide when to push or submit.

The 9 November report was subsequently regenerated from source commit 80e44e595357af4b6cb3e1efd0623cc1cb598cca with a vertical component chart, separated live-load unit columns and an unnumbered cover. Its PDF SHA-256 is 9f4fabeb7174c96fb061ada4149d0c37f156d9bd0c58d228115a6eaef4bd1ffa. The current result is in TEST_RESULTS.md.
