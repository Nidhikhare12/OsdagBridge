# OSI Test Files Repository

This directory contains saved OsdagBridge project files (`.osi`) used for automated testing, regression checking, and manual UI verification.

## File Organization

All test files follow the naming convention:
`TC_<CATEGORY>_<NUMBER>_<SHORT_DESCRIPTION>.osi`

For example:
- `TC_BI_001_span_12m_baseline.osi`: Minimum span baseline test.
- `TC_BI_002_span_45m_baseline.osi`: Maximum span baseline test.
- `TC_BI_008_skew_plus60deg.osi`: Maximum positive skew angle test.
- `TC_CM_001_custom_steel_grade.osi`: Custom steel properties test case.
- `TC_CM_005_custom_concrete_deck.osi`: Custom concrete deck properties test case.

## Structure of an .osi File

An `.osi` file in OsdagBridge is a serialized project definition containing the complete `input_dict` state. When loaded into the application, it populates both basic inputs and additional inputs dialogs.
