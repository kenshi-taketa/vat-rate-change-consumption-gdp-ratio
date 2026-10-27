# P6 re-run in R (A and B), prepared 2026-10-25 in the cloud (no R here: the R code has NOT been run)

## A. gsynth with data rebuilt from the raw files (A_gsynth_from_raw.R)
- Builds the 60-quarter windows and donor lists of the five gsynth episodes from the raw FRED files with R code, using the rules in Section 4 of the paper.
- Compares them with Python's ep_<episode>.csv (donor sets and data; tolerance 1e-6), then runs gsynth (same settings as before) on the R-built data.
- Edit ROOT (and EPDIR) at the top. Run: setwd("<an output folder>"); source("A_gsynth_from_raw.R").
- Outputs: A_window_check.csv, A_gsynth_results.csv, plus a printed comparison with the earlier gsynth run.
- Cloud check of the RULES only (same rules written in pandas, not Python's p6est.py): all five episodes give the same donor sets as the Python files; maximum data difference 2e-16.

## B. Permutation test and motive comparison (B_permutation_and_motive.R)
- Input data/ascm_placebo_gaps_core11.csv: the ridge-ASCM mean gap (pp) of the treated country and of each placebo country, for the 11 core increases. Written by Python from the stage-4 result files, so the placebo gaps are NOT re-estimated. What R re-does: the random-draw test (B = 100,000), the middle 95 % range, and the exact enumeration of the 50 arrangements.
- Run: setwd("<folder that contains data/>"); source("B_permutation_and_motive.R"). Output: B_results.csv.
- Expected (cloud check in Python of the same steps): mean gap -0.1215; one-sided p about 0.485 (paper 0.49), middle 95 % about [-2.3, 1.7]; motive difference -5.252, 2 of 50 arrangements as large, p = 0.04; four largest |difference| 4.28, 4.65, 5.252, 5.308.

## What this does and does not settle
- A removes "data for gsynth prepared by Python". B removes "aggregation not re-done". Neither re-estimates the SCM/ASCM placebos or the Bai-Perron search.
