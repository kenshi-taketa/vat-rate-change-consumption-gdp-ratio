import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from multiprocessing import Pool
from p6est import *
import run_lnc as L
P = sys.argv[1]
Yr = load_y(f'{P}/raw_fred_20261015', f'{P}/panel_japan_spliced_20261015.csv')   # ln C - ln Y
Yc = L.Y                                                                         # ln C

chg = load_changes(f'{P}/vat_rate_changes.csv')
Yy = Yc - Yr                                                                     # ln Y (identity); same NaN pattern
inc = ['DE2007Q1','GB1979Q2','GB1991Q2','GB2011Q1','HU2012Q1','JP1997Q2','JP2014Q2','LU2015Q1','NL2012Q4','NZ2010Q4','SI2013Q3']
def work(e):
    c, q = e[:2], e[2:]; t0 = pd.Period(q, 'Q')
    pre, post, don = donor_set(Yr, chg, c, t0, 40, 20, False, True)
    Dr = Yr - Yr.loc[pre[0]]; Dc = Yc - Yc.loc[pre[0]]; Dy = Yy - Yy.loc[pre[0]]
    out = {}
    for u in [c] + don:
        pool = [d for d in don if d != u]
        f = fit(Dr, u, pool, pre, post, True); w = f['w']
        gr = 100 * f['gap_post'].mean()
        gc = 100 * (Dc.loc[post, u].values - Dc.loc[post, pool].values @ w).mean()
        gy = 100 * (Dy.loc[post, u].values - Dy.loc[post, pool].values @ w).mean()
        out[u] = (gr, gc, gy)
    return e, out
if __name__ == '__main__':
    with Pool(4) as p: res = dict(p.imap_unordered(work, inc))
    pickle.dump(res, open('out/dec_res.pkl', 'wb'))
