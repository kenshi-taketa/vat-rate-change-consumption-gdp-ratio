# Do VAT Rate Changes Bend the Consumption-to-GDP Ratio?

Code, inputs, download records and result files for the paper
"Do VAT Rate Changes Bend the Consumption-to-GDP Ratio? Evidence from Synthetic Controls in a Cross-Country Panel"
by Kenshi Taketa (Aoyama Gakuin University).

## What is here

| Folder | Contents |
|---|---|
| `code/fetch/` | Scripts that download the FRED series and record the download (no API key is needed). |
| `code/python/` | The main estimation: ridge-augmented synthetic control, placebo and permutation tests, conformal sets, prediction intervals. Read `code/python/README_code.md` first. |
| `code/stata/`, `code/R/` | Independent re-runs in Stata and R (see the README in each folder). |
| `code/figures_tables/` | Scripts for Figures 1-3 and Tables 1-3 (`not_checked/` holds the scripts for the other tables; see below). |
| `inputs/` | Our own inputs: the list of VAT rate changes with dates and sources, the core episodes, the episode candidates, and our classification of motives. |
| `logs/` | Download log (series, URL, time, size, MD5), summary of the download, and the series start dates. |
| `results/` | Result files used for the paper's tables and figures. |
| `CHECKSUMS.txt` | SHA-256 of every file in this repository. |

## Data

The outcome is y = ln C - ln Y, with C = private consumption and Y = GDP, both real indices from the OECD (2015 = 100), quarterly:
FRED series `NAEXKP02{CC}Q661S` (consumption) and `NAEXKP01{CC}Q661S` (GDP), where `{CC}` is the two-letter country code.
Eurostat series (2026 vintage) are used for one robustness check.

**We do not copy the files of the data providers.** All series are public. `logs/fred_download_log_20261015.csv` lists every series with its URL, the time of download, the file size, the MD5 and the number of observations, so that you can download the same series and check whether your copy matches ours. The series are revised over time; a new download may differ from ours, and the MD5 shows whether it does.
The download log has no column for the name of the computer used (we removed it).
Six series were not available at download (see `logs/fetch_summary_20261015.txt`).

Japan before 1994 uses a spliced series (the ESRI retrospective series scaled to the OECD series). The file with the spliced series is not included, and which script builds it has not been confirmed (`code/fetch/stage2_remaining_checks_20261015.py` holds the stage-2 checks). Whether the spliced file may be shared has not been decided.

## How to run

1. Download the series: `python code/fetch/fetch_fred_panel_20261015.py` (Python 3.8+, standard library only). It writes `raw_fred_<date>/`, a download log and a summary next to the script.
2. Estimation, in this order (details and arguments in `code/python/README_code.md`):
   `run_stage4.py` -> `aggregate_stage4.py` -> `stage4_extra.py`, and `compare_rerun.py` to compare with the stored results.
3. Figures 1-3 and Tables 1-3 from the stored results, run from the root of this repository:

```
export P6_DATA=.  P6_STAGE4_OUT=results  P6_OUT=.
python code/figures_tables/P6_make_fig1_pdf_20261027.py
python code/figures_tables/P6_make_figs23_pdf_20261027.py
python code/figures_tables/make_tables_en.py      # Tables 1-3 (written next to the script)
```

The per-episode estimation results used by Figure 2 are stored in `results/res_pickles_20261015.zip`. Unzip it inside `results/` (it creates `results/res/`) before running the Figure 2-3 script.

Random seeds: permutation across episodes 20261015 (B = 100,000 draws); prediction intervals (scpi) 20261010.

## What has been checked

- Figures 1-3 and Tables 1-3 were rebuilt from the files in this repository (run on 2026-10-27); the mean gap of the 11 increases (-0.12) and its 95% range (-2.32 to +1.74) match the paper.
- Tables 4-7 and the appendix tables: their scripts are in `code/figures_tables/not_checked/`. They read files (for example `s5/`, `s10/`, `kink/out2/`) that are not in this repository, and we have not run them in this layout.
- `code/R/final_rerun/` and `code/stata/` were written to re-do the checks of Appendix E; the Stata part has not been run by us in the cloud (no Stata there). The online appendix (S1) reports what was compared.
- The estimation scripts (`code/python/`) need the raw FRED files, which you download in step 1, and the Japan splice file. We have not run the whole chain from a fresh download in this repository layout.

## License

Code: MIT (see `LICENSE`). The data of the OECD, FRED and Eurostat follow the terms of those providers.

## Citation

Taketa, K. (2026). Do VAT Rate Changes Bend the Consumption-to-GDP Ratio? Evidence from Synthetic Controls in a Cross-Country Panel. Working paper. [Update with the journal reference or DOI when available.]
