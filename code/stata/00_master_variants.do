* P6 re-run C: design variants in Stata.  1. Set ROOT to the folder rerun_stata_20261025 (forward slashes).  2. do this file.
clear all
macro drop _all
set more off
global ROOT "C:/rerun_stata_20261025"      // <-- edit this line
* global VTAGS "lead1"                      // optional: run one variant first (lead1 hktw pre60 nobreakrule)
* global EPLIST "DE2007Q1 NL2012Q4"         // optional: smoke test with two episodes
capture mkdir "${ROOT}/output"
capture log close
log using "${ROOT}/output/replication_log_variants.txt", replace text
display "Stata version: " c(stata_version) "   flavor: " c(flavor) "   " c(current_date) " " c(current_time)
do "${ROOT}/stata/step_variants_p6.do"
log close
