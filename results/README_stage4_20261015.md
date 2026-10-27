# P6 stage 4 (full estimation) — provenance and how to run
Run on the Anthropic cloud container only (not on the user's PC). Python 3.13, numpy 2.5.3, scipy 1.18.1, pandas 3.0.5, statsmodels (pip). No Stata. OMP_NUM_THREADS=1.
Inputs: stage-2 files in the P6 folder (raw_fred_20261015/, panel_japan_spliced_20261015.csv, vat_rate_changes.csv, episode_candidates.csv, core_episodes_20261015.csv, P6_core14_announcement_motive_20261015.csv).

| file | role |
|---|---|
| p6est.py | donor rules, SCM (SLSQP), ridge ASCM (LOQO-CV, 1-SE), placebos |
| run_stage4.py + launch.sh | 130 episode tasks (59 extended at pre40; core at pre60/80/full, restricted, nobreakrule; GB1979Q3) -> out/res/*.pkl (zip) |
| aggregate_stage4.py | permutation aggregation (B=1e5, seed 20261015), strata, leave-one-out, cluster SE, spec curve -> out/*.csv, aggregate_results.json |
| kink/kink_aux.py (+ bai_perron_core_P1copy.py, read-only copy of the P1 file) | own-history kink regression per core episode, pooled kink |
| conformal_core.py | per-episode conformal sets (SCM, H0 constant post gap) |
Run: `bash launch.sh; python3 aggregate_stage4.py out EPISODES CORE MOTIVE 100000; python3 kink/kink_aux.py ...; python3 conformal_core.py ...` (arguments as in each script header).

Known deviations / limits (not hidden):
- Kink: Bai-Perron vectorised DP (same optimum as the P1 code), bootstrap B=500, seed 20261015. Bootstrap B=500 and B=2000 (seeds 20261015 and 1) give identical coefficients; the B=20 pilot (GB1991 -0.85) was unstable only because B was too small. The data are OECD Q661S, not the Japan paper's ESRI series, and there are no crisis dummies, so own-kink numbers are not comparable to the papers. A control break within +-2 quarters of a core tax date is dropped (GB1991Q1).
- Pooled kink: 11 increases, SE clustered by episode (11 clusters; small-cluster bias).
- Conformal (v2, conf2.py): same procedure as the P1 code (b4b_refit.py / conformal_std.py): theta subtracted from the post outcome, weights re-fit on pre+post, q=1 mean|u| or q=2 RMS, T circular shifts, 95% set {p>0.05}, grid -30..+20 step 0.1. VALIDATED: conf_validate.py reproduces the Japan paper's JP2014 SCM q=1 95% set [-13.8,+4.5] exactly with the paper's window/donors (IFS panel, T0=73, T1=22, 6 donors). JP1997 not reproduced (the IFS panel has 4 missing GB values in that window; how the P1 code handled it is unchecked). The earlier conformal_core.* (v1, single-q, SCM only) is superseded by conformal_core_v2.*.
  With P6's main setting (pre 40Q, post 20Q, 3-27 donors) the sets are wide: with ASCM 11 of 12 episodes hit the grid edge (uninformative); with SCM only FR1977, JP1997 are bounded on both sides; GB1991 (SCM) excludes 0 ([0.7, 20+]) and DE2007 (SCM) has p(0)=0.017.
- Not done in stage 4: Cattaneo-Feng-Titiunik intervals (scpi), HK/TW donors, figures, extended-59 tables by size group. -> stage 5.

- Added after the first save: cft_core.py (CFT intervals, scpi_pkg 4.0.0), stage4_extra.py (extended-sample group tables, extra spec cells, permutation draws, figure), conf_jp1997.py (JP1997 conformal reproduces the paper's [-1.6,+2.5] when GB is dropped as in the P1 code), conf2.py/conf_validate.py (conformal v2).
