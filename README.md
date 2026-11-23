# OsdagBridge -- LaTeX Report Generator Refactoring & Enhancements

## Project Overview

This repository contains the OsdagBridge project and work related to the
FOSSEE Winter Internship 2026 task: **OsdagBridge LaTeX Report Generator
Refactoring & Enhancements**.

OsdagBridge is a plugin for Osdag software used for the analysis and
design of short-span steel girder bridges. Its report-generation module
converts structural design outputs into PDF reports using Python,
PyLaTeX and LaTeX.

## Task Objectives

The internship task asks for the following improvements to the report
generator:

1.  Repeated column headers for tables that continue across pages, using
    PyLaTeX `LongTable` or LaTeX `longtable` header sections.
2.  Improved page layout, vertical spacing and footer clearance to
    prevent table or text overlap.
3.  Separate vehicle live-load and footway-load tables, with vehicle
    classes reflecting the options selected in the GUI.
4.  Utilization-ratio charts for steel plate girders, concrete deck
    slab, cross bracing and end diaphragms, including a red dashed
    reference line at UR = 1.0.
5.  Material-quantity charts for structural-steel tonnage and concrete
    volume versus reinforcement-steel weight.
6.  A centralized style configuration module for document geometry,
    typography, colours, tables, cell padding and headers/footers.

> **Implementation note:** Confirm each objective against the current
> Python source code and generated report before describing it as
> completed. The presence of a report PDF or a style file alone does not
> prove that a feature is fully implemented.

## Requirements

-   Miniconda or Anaconda
-   Git
-   Python environment defined by `environment.yml`
-   A LaTeX distribution such as MiKTeX (with `pdflatex` available on
    PATH)
-   Project dependencies installed from the environment file

## Setup

Clone your fork and enter the project directory:

``` bash
git clone https://github.com/<your-username>/OsdagBridge.git
cd OsdagBridge
```

Fetch the upstream repository and switch to the development branch, if
that is the branch used for the task:

``` bash
git remote add upstream https://github.com/Nidhikhare12/OsdagBridge.git
git fetch upstream
git checkout dev
```

Create and activate the Conda environment:

``` bash
conda env create -f environment.yml
conda activate osdagbridge-env
```

## Run the Application

From the project root:

``` bash
cd osdagbridge/src
python -m osdagbridge.desktop
```

In the GUI, run the bridge analysis using **Design**, then select
**Generate Report**.

## Run Tests

From the project root, activate the environment and run:

``` bash
python -m pytest -v tests
```

If your repository uses a different test directory or test command,
follow the instructions in that directory and update this section.

## Deliverables

The internship submission is expected to include:

-   Python source code for the report-generator changes.
-   Centralized style configuration, if implemented.
-   Automated tests.
-   `README.md` (this file).
-   `Technical_Changes.pdf`, describing actual code changes and modified
    filenames.
-   `Report_Before.pdf`, showing the original report output.
-   `Report_After.pdf`, showing the enhanced report output.

## Report Comparison

Use the same bridge design inputs for the before and after reports so
that the comparison focuses on report-generation changes rather than
different design inputs.

The reports should be checked for:

-   Repeated headers on multi-page tables.
-   Clear page breaks and no footer overlap.
-   Separate vehicle and footway load tables.
-   Utilization-ratio charts with the UR = 1.0 threshold.
-   Material-quantity charts populated from design results.
-   Consistent formatting across chapters.

## Repository and Collaboration

Add the internship repository owner/mentor account `Nidhikhare12` as a
collaborator if requested by the internship instructions. Share the URL
of your fork/repository in the final submission.

## Maintainer Notes

Before final submission, update this README with the exact source files
changed, the actual test results, and any known limitations. Do not
claim that a chart, table, or style enhancement is complete unless it is
present in the code and verified in a generated report.
