import sys, os, csv, pickle
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from multiprocessing import Pool
import p6est
from p6est import *
P = sys.argv[1]; OUT = sys.argv[2]
RAW = f'{P}/raw_fred_20261015'; SPL = f'{P}/panel_japan_spliced_20261015.csv'
def load_lnc(raw, spliced):
    cc = sorted({f[8:10] for f in os.listdir(raw) if f.startswith('NAEXKP02')})
    Y = {}
    for c in cc:
        d = {}
        for dd, v in list(csv.reader(open(f'{raw}/NAEXKP01{c}Q661S.csv')))[1:]:
            if v in ('', '.'): continue
            d[pd.Period(f"{dd[:4]}Q{(int(dd[5:7]) - 1) // 3 + 1}", 'Q')] = float(v)
        Y[c] = np.log(pd.Series(d)).dropna()
    sp = pd.read_csv(spliced); sp['p'] = [pd.Period(f"{d[:4]}Q{(int(d[5:7]) - 1) // 3 + 1}", 'Q') for d in sp.date]
    Y['JP'] = np.log(sp.set_index('p')['gdp_idx'])
    idx = pd.period_range('1960Q1', '2023Q3', freq='Q')
    return pd.DataFrame({c: Y[c].reindex(idx) for c in Y})
Y = load_lnc(RAW, SPL); chg = load_changes(f'{P}/vat_rate_changes.csv')
core = pd.read_csv(f'{P}/core_episodes_20261015.csv', encoding='utf-8-sig')
eps = list(core.episode)
def work(e):
    c, q = e[:2], e[2:]
    r = run_episode(Y, chg, c, pd.Period(q, 'Q'), 40, 20, False, True, True, ('ascm',))
    return e, r
if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    with Pool(int(sys.argv[3])) as p:
        res = dict(p.imap_unordered(work, eps))
    pickle.dump(res, open(f'{OUT}/lny_res.pkl', 'wb'))
    for e in eps:
        r = res[e]
        print(e, None if r is None else (r['J'], round(r['ascm']['mean_gap'], 2), round(r['ascm']['p_ratio'], 3), round(r['ascm']['pre_rmspe'], 2)), flush=True)
