# P6 re-run C (Stata): four design variants of Appendix F. Written 2026-10-25 in the cloud; the Stata code has NOT been run (no Stata here).
Variants: lead1 (treatment date one quarter earlier), hktw (Hong Kong and Taiwan added), pre60 (60 pre-treatment quarters), nobreakrule (data-break rule off). 12 core episodes each, SCM and ridge ASCM, with placebo p-values.
Uses the same Mata solver as the main re-estimation (stage 6, which matched Python), so a match here checks the variant windows and donor sets through an independent program.
## Run
1. Copy this folder to e.g. C:/rerun_stata_20261025 (any path without Japanese characters). Edit `global ROOT` in stata/00_master_variants.do.
2. Smoke test: uncomment `global VTAGS "lead1"` and `global EPLIST "DE2007Q1 NL2012Q4"`; then the full run (remove both). Time: the ASCM fits with 20+ comparison countries (JP2014, LU2015) are the slowest.
3. Send back output/replication_log_variants.txt and output/compare_variants.csv.
## Compared
J, pre-RMSPE (0.01), fit ratio (0.5 %), mean gap (0.01 pp), placebo p (exact), lambda (same grid point). Targets: data/targets_variants_python.csv (from the Python result files of stage 4 and 5).
## Limits
- Windows and comparison-country lists of the variants are written by the Python code (data/variants_p6.dta); the HK/TW series are the files of the UK project, built into data/p6_wide_hktw.dta by Python. Rules for donors were checked independently in R for the main windows (re-run A), not for these variants.
- The permutation aggregation of Table F1 (averages over 11 episodes) is not repeated here; the comparison is at the episode level.
- Not covered: the factor models, the Eurostat vintage, the "no rate change in the pre-window" row, and the "drop two quarters" row (computed from stored gap paths).
