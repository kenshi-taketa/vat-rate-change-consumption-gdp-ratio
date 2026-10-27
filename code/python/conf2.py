"""P6 stage 4: conformal inference, validated against the Japan paper (JP2014 SCM q=1 95%: [-13.8,4.5], reproduced exactly with the paper's window/donors).
Same procedure as P1 b4b_refit.py/conformal_std.py: for each theta, subtract theta from post outcome, refit weights on pre+post, mean|u| (q=1) or RMS (q=2) of post block, T circular shifts, 95% set {p>0.05}, grid -30..+20 step 0.1.
SCM and ridge ASCM (lambda by leave-one-quarter-out CV with re-fit weights, 1-SE rule, as p6est.ascm_lambda).
usage: python conf2.py RAW SPL VAT CORE OUT [est ...]"""
import sys, json, time, numpy as np, pandas as pd
from multiprocessing import Pool
from p6est import *
# _center はアンダースコア始まりなので、import * では入らない。別に読み込む。
from p6est import _center
# 引数: RAW=FRED の CSV フォルダ、SPL=日本のつなぎ系列、VAT=税率変更の一覧、CORE=核エピソード、OUT=出力先。
# 最後に推定法(scm、ascm)を並べると、その推定法だけ実行する。省略すると両方。
RAW, SPL, VAT, CORE, OUT = sys.argv[1:6]; ESTS = sys.argv[6:] or ['scm', 'ascm']
# データを読み、核エピソード(tier = core)だけを対象にする。
Y = load_y(RAW, SPL); chg = load_changes(VAT); core = pd.read_csv(CORE, encoding='utf-8-sig'); core = core[core.tier == 'core']
# 検定する「変更後の真の gap」θ の候補: −30 から +20 パーセントポイントまで、0.1 刻み(501個)。
GRID = np.round(np.arange(-30, 20.0001, 0.1), 1)
# 重みを推定し直して、残差 u = y − Xw を返す。est='scm' は通常の SCM、'ascm' は ridge 補正つき(p6est.py と同じ手順)。
def resid(y, X, est):
    w = scm_qp(y, X)
    if est == 'ascm':
        lam = ascm_lambda(y, X, w); Xc = _center(X)
        w = w + np.linalg.solve(Xc.T @ Xc + lam * np.eye(X.shape[1]), Xc.T @ (y - X @ w))
    return y - X @ w
# 1つの(エピソード, 推定法)について、すべての θ の p値を求め、95%・90% の信頼集合を作る。T0=40(変更前)、T=60(全期間)。
def one(a):
    e, est = a; c, t0 = e[:2], pd.Period(e[2:], 'Q'); pre, post, don = donor_set(Y, chg, c, t0, 40, 20)
    # 窓の最初の四半期を 0 にそろえ、処置国の y(y)と比較国の X を取り出す。
    D = Y - Y.loc[pre[0]]; win = list(pre) + list(post); y = D.loc[win, c].values; X = D.loc[win, don].values; T0, T = 40, 60
    # 各 θ について: 変更後の y から θ(%ポイント → 100で割る)を引き、重みを前+後の全期間で推定し直して、残差 u を保存する。
    us = []
    for th in GRID:
        ya = y.copy(); ya[T0:] -= th / 100; us.append(resid(ya, X, est))
    res = {}
    # 検定統計量は2種類: q=1 は後期の残差の平均絶対値、q=2 は後期の残差の二乗平均平方根(RMS)。
    for q in (1, 2):
        # 各 θ の p値: 残差 u を円環状に T 通りずらし、後期ブロックの統計量を並べる。s[0] が実際の並び。
        # p = ずらした統計量が s[0] 以上になる割合。
        ps = []
        for u in us:
            s = np.array([(np.abs(blk).mean() if q == 1 else np.sqrt((blk ** 2).mean())) for blk in (u[[(T0 + j + k) % T for k in range(T - T0)]] for j in range(T))])
            ps.append(np.mean(s >= s[0] - 1e-15))
        # p_zero = θ=0 の p値。pmax = p値の最大(信頼集合が空にならないかの目安)、theta_pmax = そのときの θ。
        ps = np.array(ps); r = dict(ep=e, est=est, q=q, J=len(don), p_zero=float(ps[np.argmin(np.abs(GRID))]), pmax=float(ps.max()), theta_pmax=float(GRID[np.argmax(ps)]))
        # 信頼集合 = p値が al(10% または 5%)より大きい θ の集まり。その最小・最大を ci90/ci95 として記録する。
        # edge = 集合が θ の探索範囲(−30〜+20)の端に達しているか(Trueなら、範囲を広げても区間は端まで続く)。
        for al in (0.10, 0.05):
            ok = GRID[ps > al]; k = int(round((1 - al) * 100))
            r[f'ci{k}_lo'] = float(ok.min()) if len(ok) else None; r[f'ci{k}_hi'] = float(ok.max()) if len(ok) else None
            r[f'ci{k}_edge'] = bool(len(ok) and (ok.min() == GRID[0] or ok.max() == GRID[-1]))
        res[q] = (r, ps.tolist())
    return a, res
if __name__ == '__main__':
    # 全エピソード × 推定法の仕事を作り、2プロセスで並列に実行する。
    jobs = [(e, est) for est in ESTS for e in core.episode]; t = time.time(); rows, curves = [], {}
    with Pool(2) as p:
        for a, res in p.imap_unordered(one, jobs):
            for q, (r, ps) in res.items(): rows.append(r); curves[f'{a[0]}_{a[1]}_q{q}'] = ps
            print(a, round(time.time() - t), flush=True)
    # 結果を conformal_core_v2.csv(区間)と conformal_core_v2_curves.json(θごとの p値の曲線)に保存する。
    df = pd.DataFrame(rows).sort_values(['est', 'q', 'ep']); df.to_csv(f'{OUT}/conformal_core_v2.csv', index=False)
    json.dump(dict(grid=GRID.tolist(), p=curves), open(f'{OUT}/conformal_core_v2_curves.json', 'w'))
    print(df.round(3).to_string())
