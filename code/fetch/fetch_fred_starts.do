* fetch_fred_starts.do  (P7: first/last observation of FRED quarterly series)
* Reads FRED public CSV files (no API key needed) and writes fred_series_starts.csv
* in the current working directory.
*
* How to run (Stata 14 or later, internet access needed):
*   cd "<folder that holds this project's files>"
*   do fetch_fred_starts.do
*
* Series:
*   PCE    = NAEXKP02{cc}Q189S   (OECD MEI, real private final consumption, SA, national currency)
*   GDP    = NAEXKP01{cc}Q189S   (OECD MEI, real GDP, SA, national currency)
*   GDP_EU = CLVMNACSCAB1GQ{cc}  (Eurostat-based real GDP, backup; European countries only)

version 14
clear all
set more off

local countries AT AU BE CA CH CL CO CZ DE DK EE ES FI FR GB GR HU IE IL IS IT JP KR LT LU LV MX NL NO NZ PL PT SE SI SK TR US
local eu AT BE CZ DE DK EE ES FI FR GR HU IE IT LT LU LV NL PL PT SE SI SK

tempname P
tempfile results
postfile `P' str2 country str6 kind str24 series_id str16 status str10 first_obs str10 last_obs long n_obs using `results', replace

foreach c of local countries {
    local jobs "PCE:NAEXKP02`c'Q189S GDP:NAEXKP01`c'Q189S"
    local isEU : list c in eu
    if `isEU' {
        local jobs "`jobs' GDP_EU:CLVMNACSCAB1GQ`c'"
    }
    foreach j of local jobs {
        gettoken kind sid : j, parse(":")
        local sid = substr("`sid'", 2, .)
        display as text "`c' `kind' `sid'"

        capture import delimited using "https://fred.stlouisfed.org/graph/fredgraph.csv?id=`sid'", clear varnames(1) stringcols(_all)
        local rc = _rc
        if `rc' != 0 {
            post `P' ("`c'") ("`kind'") ("`sid'") ("IMPORT RC `rc'") ("") ("") (0)
            continue
        }

        quietly ds
        local vars `r(varlist)'
        local v1 : word 1 of `vars'
        local v2 : word 2 of `vars'
        if "`v2'" == "" {
            post `P' ("`c'") ("`kind'") ("`sid'") ("BAD FORMAT") ("") ("") (0)
            continue
        }

        quietly gen double vv_ = real(`v2')
        quietly drop if missing(vv_)
        quietly sort `v1'
        quietly count
        local n = r(N)
        if `n' == 0 {
            post `P' ("`c'") ("`kind'") ("`sid'") ("NO DATA") ("") ("") (0)
            continue
        }

        local f = `v1'[1]
        local l = `v1'[_N]
        if substr("`f'", 5, 1) != "-" {
            post `P' ("`c'") ("`kind'") ("`sid'") ("BAD DATE") ("") ("") (0)
            continue
        }
        post `P' ("`c'") ("`kind'") ("`sid'") ("OK") ("`f'") ("`l'") (`n')
    }
}

postclose `P'
use `results', clear
export delimited using "fred_series_starts.csv", replace
list country kind status first_obs last_obs n_obs, sepby(country) noobs
display as text _n "Wrote fred_series_starts.csv in " c(pwd)
