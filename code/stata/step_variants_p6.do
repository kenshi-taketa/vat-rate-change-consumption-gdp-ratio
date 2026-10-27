* ====================================================================
* P6 re-run C (Stata): four design variants of Appendix F, SCM and ridge ASCM, 12 core episodes each (4 x 12 x 2 = 96 fits, each with placebos).
*   lead1       treatment date one quarter earlier (40 pre quarters, 21 post quarters)
*   hktw        Hong Kong and Taiwan added to the comparison countries
*   pre60       pre-treatment window of 60 quarters
*   nobreakrule data-break rule switched off (MX, IE, GR not dropped)
* Uses the same independent Stata/Mata solver as steps 3+7 (exact active-set SCM, own leave-one-quarter-out CV for the ridge penalty).
* The windows and the comparison-country lists of each variant are written by the Python code (data/variants_p6.dta), as for the main run.
* Output: output/stata_variants.csv, output/compare_variants.csv (MATCH flag per row).
* Optional: global VTAGS "lead1 pre60"  /  global EPLIST "DE2007Q1 JP2014Q2"  restrict the run.
* Usage: edit ROOT in 00_master_variants.do, then  do 00_master_variants.do
* ====================================================================
clear all
set more off
global DATA "${ROOT}/data"
global OUTD "${ROOT}/output"
capture mkdir "${OUTD}"
capture confirm file "${DATA}/p6_wide_hktw.dta"
if _rc {
    display as error "Data not found under ROOT = ${ROOT}"
    exit 601
}
use "${DATA}/variants_p6.dta", clear
global NV = _N
forvalues i = 1/$NV {
    global ep`i' = ep[`i']
    global tg`i' = tag[`i']
    global cc`i' = cc[`i']
    global w0`i' = w0[`i']
    global t2`i' = t2[`i']
    global T0`i' = T0[`i']
    global dn`i' = donors[`i']
}
use "${DATA}/p6_wide_hktw.dta", clear
sort t
quietly assert t == _n - 1
drop t year quarter
do "${ROOT}/stata/p6_mata.do"
mata: p6load()
clear
tempfile resf
tempname ph
postfile `ph' str10 ep str12 tag str5 est double(J pre_rmspe ratio mean_gap slope p_ratio rank_ratio lam) using `resf', replace
forvalues i = 1/$NV {
    local e "${ep`i'}"
    local g "${tg`i'}"
    if "${EPLIST}" != "" & strpos(" ${EPLIST} ", " `e' ") == 0 continue
    if "${VTAGS}" != "" & strpos(" ${VTAGS} ", " `g' ") == 0 continue
    forvalues k = 1/2 {
        local en = cond(`k' == 1, "scm", "ascm")
        mata: runep("${cc`i'}", "${dn`i'}", ${w0`i'}, ${t2`i'}, ${T0`i'}, `k')
        matrix RR = R
        post `ph' ("`e'") ("`g'") ("`en'") (RR[1,10]) (RR[1,1]) (RR[1,3]) (RR[1,4]) (RR[1,5]) (RR[1,8]) (RR[1,9]) (RR[1,6])
        display as text "`g' `e' `en': J=" RR[1,10] "  mean gap " %7.3f RR[1,4] "  ratio " %7.3f RR[1,3] "  p " %6.4f RR[1,8]
    }
}
postclose `ph'
use `resf', clear
export delimited using "${OUTD}/stata_variants.csv", replace
tempfile stata
save `stata'
import delimited using "${DATA}/targets_variants_python.csv", clear varnames(1) case(preserve)
rename (J pre_rmspe ratio mean_gap slope p_ratio rank_ratio lam) (J_py pre_py ratio_py gap_py slope_py p_py rank_py lam_py)
merge 1:1 ep tag est using `stata', keep(match) nogenerate
gen byte ok = abs(ratio - ratio_py) < 0.005*ratio_py + 0.005 & abs(mean_gap - gap_py) < 0.01 & abs(pre_rmspe - pre_py) < 0.01 & abs(p_ratio - p_py) < 1e-6 & J == J_py
replace ok = 0 if est == "ascm" & (abs(lam/lam_py - 1) > 0.01)
display _n as text "=== Stata vs Python, design variants ==="
list tag ep est J mean_gap gap_py ratio ratio_py p_ratio p_py ok, noobs sepby(tag ep) abbreviate(12)
quietly count
local n = r(N)
quietly count if ok
display as result "Variants summary: " r(N) " of `n' rows match the Python results (ratio 0.5%, gap 0.01 pp, p exact, lambda same grid point)"
bysort tag est: egen n_ok = total(ok)
bysort tag est: gen n_all = _N
display _n as text "By variant and estimator (rows that match / all rows):"
preserve
    keep tag est n_ok n_all
    duplicates drop
    list, noobs
restore
export delimited using "${OUTD}/compare_variants.csv", replace
