"""Aggregation for Appendix Tables F.1 and F.2 (11 core increases, equal weights).
Written 2026-10-28 for the check of these tables; same permutation scheme as aggregate_stage4.py
(B = 100,000 draws, seed 20261015; each episode's reference set = its placebo gaps + the treated gap).

Usage: python aggregate_f_tables.py LNC_PKL LNY_PKL DEC_PKL
  LNC_PKL = lnc_res.pkl   (from run_lnc.py)
  LNY_PKL = lny_res.pkl   (from run_lny.py)
  DEC_PKL = dec_res.pkl   (from P6_ratio_weights_decomposition_run_20261025.py)
Table F.1: weights fitted to ln C, and weights fitted to ln Y.
Table F.2: weights fitted to ln C - ln Y, applied to ln C - ln Y, ln C and ln Y.
"""
import pickle, sys, numpy as np
B = 100000
rng = np.random.default_rng(20261015)
inc = ['DE2007Q1','GB1979Q2','GB1991Q2','GB2011Q1','HU2012Q1','JP1997Q2','JP2014Q2','LU2015Q1','NL2012Q4','NZ2010Q4','SI2013Q3']
def agg(pls, obs, label):
    T0 = np.mean(obs)
    perm = sum(pls[i][rng.integers(0, len(pls[i]), B)] for i in range(len(pls))) / len(pls)
    p = (np.sum(np.abs(perm) >= abs(T0)) + 1) / (B + 1)
    print(f'{label}: mean gap {T0:.2f}  sd of random averages {perm.std():.1f}  two-sided p {p:.3f}  n={len(pls)}')
for tag, f in (('ln C', sys.argv[1]), ('ln Y', sys.argv[2])):
    R = pickle.load(open(f, 'rb'))
    pls, obs = [], []
    for e in inc:
        s = R[e]['ascm']; o = s['mean_gap']; obs.append(o)
        pls.append(np.array([v['mean_gap'] for v in s['placebo'].values()] + [o]))
    agg(pls, obs, 'F.1 weights fitted to ' + tag)
D = pickle.load(open(sys.argv[3], 'rb'))
for k, name in ((0, 'ln C - ln Y'), (1, 'ln C'), (2, 'ln Y')):
    pls, obs = [], []
    for e in inc:
        c = e[:2]; o = D[e][c][k]; obs.append(o)
        pls.append(np.array([v[k] for u, v in D[e].items() if u != c] + [o]))
    agg(pls, obs, 'F.2 ratio weights applied to ' + name)
