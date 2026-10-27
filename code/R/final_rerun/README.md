# P6 final re-run (R + Stata): the remaining checks of Appendix F. Written 2026-10-25 in the cloud; NOTHING here has been run yet (no R or Stata in the cloud).
What it re-does, with code independent of the Python code, for all rows of Table F1:
main, drop the first two post quarters, treatment date 1 and 2 quarters earlier, Hong Kong and Taiwan added, Eurostat 2026 series, comparison countries with no rate change in the pre-window, 60 / 80 quarters / full pre-window, no data-break rule, and our own factor model. (gsynth: aggregated from the earlier R run.)
Unlike the earlier Stata run, the data, windows and comparison-country lists are built from the raw files in R (step 1), and every placebo fit is compared, not only the treated country.

## Order (Windows; set the working directory of R to this folder)
1. R:     setwd("<this folder>"); source("R/R1_build_inputs.R")        -> data_r\*.csv, output\R1_check_*.csv   (seconds)
2. Stata: edit `global ROOT` in stata\00_master_final.do; smoke test first (uncomment VTAGS "lead1" and EPLIST "DE2007Q1 NL2012Q4"), then full run   -> output\stata_long.csv, output\replication_log_final.txt
3. R:     source("R/R3_own_factor_model.R")                              -> output\ife_long_r.csv, output\R3_check_ife.csv   (about a minute)
4. R:     source("R/R2_compare_and_aggregate.R")                         -> output\R2_unit_comparison.csv, output\R2_tableF1_check.csv
Send back: the console output of steps 1, 3, 4 (or the output\*.csv files) and output\replication_log_final.txt.
Full Stata run: 10 variants x 12 episodes, treated + placebos, ridge ASCM only; the windows with 60 or more pre-quarters and 20+ countries are the slowest. If it takes too long, run `global VTAGS` in parts.

## Checks done in the cloud (same rules written in pandas, not the R code itself)
- Windows and comparison countries of all 112 runs (10 variants x 12 episodes, where the run exists) equal the Python ones; the R-style panels equal the Python panels (max difference 5e-12, same missing pattern).
- Table F1, rebuilt from the Python fits with the aggregation rule of R2, reproduces every number of the table (p-values within 0.01). The one-sided p-values of Panel B range from 0.42 to 0.79, as in the table note.
## Not covered
- The Bai-Perron search, the placebo-free parts of Section 6, and the conformal / prediction-interval steps (done earlier). gsynth is not re-run here; its row is aggregated from the R run of 21 October.
