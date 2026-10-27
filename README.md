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
| `inputs/` | Our own inputs: the list of VAT rate changes with dates and sources, the core episodes, the episode candidates, and our classification of motives (including `japan_esri_retro_parsed_2780.csv`, the ESRI series before 1994, and `P6_ext34_source_status_20261022_v4.csv`, the classes of the 34 extended increases as in Table A.1). |
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

Japan before 1994 uses a spliced series. Before 1994Q1 we use the "simplified retrospective" series of the Economic and Social Research Institute (ESRI), Cabinet Office, Government of Japan (real, seasonally adjusted, 2015 chained prices; file `gaku-jk_2780.csv`; see the ESRI note at https://www.esri.cao.go.jp/jp/sna/data/data_list/h27_retroactive/pdf/h27sokyu_gaiyou.pdf). ESRI describes it as a reference series made by a simple method. The values as parsed are in `inputs/japan_esri_retro_parsed_2780.csv` (1980Q1-1995Q1; private consumption total and GDP, in billions of yen).
**Edited by the author:** we multiply each of the two ESRI series by one constant so that it equals the OECD value in 1994Q1, and we use the OECD (FRED) values from 1994Q1. The result is not an official figure of ESRI. The ESRI content is used under the Public Data License v1.0 of the Japanese government (compatible with CC BY 4.0). We do not copy the spliced file, because it also holds the OECD values; `code/fetch/build_japan_splice.py` rebuilds it from the ESRI file and the two FRED series (`NAEXKP02JPQ661S`, `NAEXKP01JPQ661S`). Our rebuild is identical, byte for byte, to the file used in the paper (MD5 dd0984f88daf33612bc496885513e7d6, 175 data rows).

## How to run

1. Download the series: `python code/fetch/fetch_fred_panel_20261015.py` (Python 3.8+, standard library only). It writes `raw_fred_<date>/`, a download log and a summary next to the script.
2. Japan splice (needed by the estimation): `python code/fetch/build_japan_splice.py raw_fred_<date> inputs/japan_esri_retro_parsed_2780.csv panel_japan_spliced_20261015.csv`.
3. Estimation, in this order (details and arguments in `code/python/README_code.md`):
   `run_stage4.py` -> `aggregate_stage4.py` -> `stage4_extra.py`, and `compare_rerun.py` to compare with the stored results.
4. Figures 1-3 and Tables 1-3 from the stored results, run from the root of this repository:

```
export P6_DATA=.  P6_STAGE4_OUT=results  P6_OUT=.
python code/figures_tables/P6_make_fig1_pdf_20261027.py
python code/figures_tables/P6_make_figs23_pdf_20261027.py
python code/figures_tables/make_tables_en.py      # Tables 1-3 (written next to the script)
```

The per-episode estimation results used by Figure 2 are stored in `results/res_pickles_20261015.zip`. Unzip it inside `results/` (it creates `results/res/`) before running the Figure 2-3 script.

Appendix Tables F.1 and F.2 (ln C and ln Y), from `code/python/`. The inputs are in one folder `P/` (the downloaded series in `P/raw_fred_20261015/`, `P/panel_japan_spliced_20261015.csv`, `P/vat_rate_changes.csv`, `P/core_episodes_20261015.csv`; the spliced Japan file is not in this repository, see above):

```
python run_lnc.py P OUT_C 2            # weights fitted to ln C   -> OUT_C/lnc_res.pkl
python run_lny.py P OUT_Y 2            # weights fitted to ln Y   -> OUT_Y/lny_res.pkl
mkdir out
python P6_ratio_weights_decomposition_run_20261025.py P OUT_C   # ratio weights applied to ln C and ln Y -> out/dec_res.pkl
python aggregate_f_tables.py OUT_C/lnc_res.pkl OUT_Y/lny_res.pkl out/dec_res.pkl
```

(The last number of the first two commands is the number of processes. The decomposition script imports `run_lnc.py`, which reads its second argument, so any folder name works there.) The stored outputs of this run are in `results/f_tables/`.

Random seeds: permutation across episodes 20261015 (B = 100,000 draws); prediction intervals (scpi) 20261010.

## What has been checked

Checked against the files in this repository (2026-10-27 and 2026-10-28):
- Figures 1-3 and Tables 1-3 are rebuilt by the scripts in `code/figures_tables/`; the mean gap of the 11 increases (-0.12) and its 95% range (-2.32 to +1.74) match the paper.
- Table 2 (gap, placebo p-value, conformal p-value and own-history kink p-value, 12 episodes), the first eight rows of Table 3, Appendix Table B.1 (donor pools and weights), C.2, C.3, E.1 (ASCM cells), E.2 (all 13 rows) and the 34 classes and evidence types in A.1 agree with the result files and inputs here.
- The main comparison of motive types (3 vs 7 episodes, difference -5.25, exact p = 0.04, from all 50 rearrangements of the labels) was recomputed independently from `results/episode_results.csv`.
- Appendix Tables A.2 and A.3 (other motive definitions; every row) and the online appendix Table S1 were recomputed from the inputs and result files here and agree with the paper. Core rows of Table A.2: the exact p-values (all arrangements of the labels) are 0.040, 0.040 (Japan 1997 as type (a)), 0.067 (Japan 1997 left out), 0.083 and 0.050; the paper prints 0.085 for the row "only episodes in the Gunter et al. sample" (a 5,000-draw value; the exact value is 0.083). The 5,000-draw value for "Japan 1997 left out" is 0.068.
- Appendix Tables F.1 and F.2 were recomputed from the downloaded FRED files (`results/f_tables/f_tables_check_20261028.txt`): F.1 ln C -3.47 (p = 0.04), ln Y -1.23 (p = 0.45); F.2 ratio -0.12 (sd 1.0, p = 0.91), ln C -4.06 (sd 6.6, p = 0.54), ln Y -3.94 (sd 6.9, p = 0.57). They equal the paper.
- Small difference between two scripts: the upper end of the 95% range for the synthetic-control (SCM) mean gap in Table 3 is 2.5436 when `aggregate_stage4.py` is run and 2.53 when `stage4_extra.py` is run; the paper gives +2.53 (the value of `stage4_extra.py`). We think the two scripts draw different random permutations for this range, but we have not confirmed this. The estimates themselves are not affected.
- The prediction intervals (`scpi`): `code/python/cft_core.py` was run again from the downloaded FRED files with `scpi_pkg` 4.0.0 (seed 20261010). All 12 episodes and all three interval types give exactly the stored `results/cft_core.csv`, including the counts of quarters in which the interval excludes zero (Table 2, last-but-two column, and the counts in the text).
- The leave-one-out numbers in the notes of Table A.2 were recomputed. The core row agrees (differences -4.6 to -6.9; exact p from 0.025 to 0.100, the paper prints 0.023 as the lower end, a 5,000-draw value). For the extended sample the differences agree (for example -3.61 without Estonia 2009 and -5.91 without New Zealand 2010). The p-values quoted there are 5,000-draw estimates, which move by about 0.003 from run to run; the exact values (all label arrangements) are 0.088 without Estonia 2009, 0.056 without Japan 2014 and 0.046 without New Zealand 2010 (the paper says 0.087, 0.057 and 0.049).
- The estimation code (`code/python/run_stage4.py`) was run again from the downloaded FRED files for the 21 main-specification episodes (all 12 core episodes included). The results equal the stored ones up to 1e-14.

Not yet checked:
- The `gsynth` row of Table E.1 (only five episodes' R results were at hand) is not re-run here.
- The scripts in `code/figures_tables/not_checked/` (older table numbering) run when the folder layout of the original project is rebuilt; their numbering does not follow the current paper.
- `code/R/final_rerun/` and `code/stata/` re-do the checks of Appendix E; the Stata part has not been run by us in the cloud (no Stata there). The online appendix (S1) reports what was compared.
- A fresh download of the FRED series and a comparison with `logs/fred_download_log_20261015.csv` (MD5) is still to be done on the author's computer.

## License

Code: MIT (see `LICENSE`). The data of the OECD, FRED and Eurostat follow the terms of those providers.

## Citation

Taketa, K. (2026). Do VAT Rate Changes Bend the Consumption-to-GDP Ratio? Evidence from Synthetic Controls in a Cross-Country Panel. Working paper. [Update with the journal reference or DOI when available.]
