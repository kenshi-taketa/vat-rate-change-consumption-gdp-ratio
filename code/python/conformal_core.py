"""P6 stage 4: per-episode conformal inference (Chernozhukov-Wuthrich-Zhu type, SCM weights re-fit on pre+post under H0: post gap = theta).
Statistic mean|u| over post quarters; 60 circular shifts; grid -30..+20 pp step 0.1; 95% set = {theta: p>0.05}. SCM only (non-negative weights).
usage: python conformal_core.py RAW SPL VAT CORE OUT"""
import sys, json, numpy as np, pandas as pd
from multiprocessing import Pool
from p6est import *
# 引数: RAW=FRED の CSV フォルダ、SPL=日本のつなぎ系列、VAT=税率変更の一覧、CORE=核エピソード、OUT=出力先。
RAW, SPL, VAT, CORE, OUT = sys.argv[1:6]
# データを読み、核エピソード(tier = core)だけを対象にする。
Y = load_y(RAW, SPL); chg = load_changes(VAT); core = pd.read_csv(CORE, encoding='utf-8-sig'); core = core[core.tier == 'core']
# 検定する「変更後の真の gap」θ の候補: −30 から +20 パーセントポイントまで、0.1 刻み。
GRID = np.round(np.arange(-30, 20.0001, 0.1), 1)
# 帰無仮説 θ のもとでの p値。後期の y から θ を引き、SCM の重みを前+後の全期間で推定し直す。
# 残差 u の後期の平均絶対値 s0 を、u を円環状にずらした T 通り(T=60)の値と比べる。p = ずらした値が s0 以上になる割合。
def pval(y, X, npre, th):
    ya = y.copy(); ya[npre:] -= th / 100; w = scm_qp(ya, X); u = ya - X @ w; T = len(u)
    s0 = np.abs(u[npre:]).mean(); s = [np.abs(np.roll(u, k)[npre:]).mean() for k in range(T)]
    return float(np.mean(np.array(s) >= s0 - 1e-15))
# 1エピソード: すべての θ について p値を求める。p>0.05 の θ の集まりが 95% 集合(区間)。
# p_zero = θ=0 の p値、contiguous = 集合が切れ目なくつながっているか。
def one(e):
    c, t0 = e[:2], pd.Period(e[2:], 'Q'); pre, post, don = donor_set(Y, chg, c, t0, 40, 20)
    D = Y - Y.loc[pre[0]]; win = list(pre) + list(post); y = D.loc[win, c].values; X = D.loc[win, don].values
    ps = np.array([pval(y, X, 40, th) for th in GRID]); ok = GRID[ps > 0.05]
    p0 = ps[np.argmin(np.abs(GRID))]
    return e, dict(p_zero=float(p0), lo=float(ok.min()) if len(ok) else None, hi=float(ok.max()) if len(ok) else None, n_in=int(len(ok)),
                   contiguous=bool(len(ok) and np.allclose(np.diff(ok), 0.1)), J=len(don))
if __name__ == '__main__':
    import time; s = time.time()
    # 2プロセスで並列実行し、結果を JSON と CSV に保存する。
    with Pool(2) as p: res = dict(p.map(one, list(core.episode), chunksize=1))
    json.dump(res, open(f'{OUT}/conformal_core.json', 'w'), indent=1)
    pd.DataFrame(res).T.to_csv(f'{OUT}/conformal_core.csv'); print(pd.DataFrame(res).T.to_string(), time.time() - s)
