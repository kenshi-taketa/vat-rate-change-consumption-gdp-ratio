"""P6 stage 4: episode-level SCM / ridge ASCM on the Q661S panel. numpy/pandas/scipy only.
Outcome y = ln C - ln Y (OECD MEI, 2015=100); JP 1980Q1-1993Q4 from the ESRI retroactive series scaled at 1994Q1.
Window: pre_n quarters before t0 (default 40), post 20 quarters from t0. Series are rebased to 0 at the first pre quarter."""
import os, csv
import numpy as np, pandas as pd
from scipy.optimize import minimize

# ridge 補正(ASCM)の罰則 λ の候補。10^-6 から 10^2 まで、対数で等間隔に 41 個。
LAMBDA_GRID = np.logspace(-6, 2, 41)
# データに断絶(系列の水準が不自然に飛ぶ)がある国。推定窓にその四半期が入るときは、その国を比較国(ドナー)から外す。
# MX=メキシコ1993Q1、IE=アイルランド2015Q1、GR=ギリシャ1990Q3(補遺C1)。
DATA_BREAKS = {'MX': '1993Q1', 'IE': '2015Q1', 'GR': '1990Q3'}   # donors excluded when the window contains the break (stage-2 checks)

# ==== (1) データ読み込み ====
# 各国の y = ln(消費) − ln(GDP) を作る。元データは FRED の OECD Q661S 系列(実質、季節調整済み)の CSV。
# NAEXKP02 = 消費の実質値(分子)、NAEXKP01 = GDP の実質値(分母)。
def load_y(raw, spliced):
    # raw フォルダにある NAEXKP02 のファイル名から、国コード(2文字)を取り出す。
    cc = sorted({f[8:10] for f in os.listdir(raw) if f.startswith('NAEXKP02')})
    Y = {}
    for c in cc:
        # CSV を1本読む。日付(YYYY-MM-DD)を四半期(Period)に直し、空欄と '.' は欠測として捨てる。
        def rd(s):
            return pd.Series({pd.Period(d[:7].replace('-01', 'Q1').replace('-04', 'Q2').replace('-07', 'Q3').replace('-10', 'Q4'), 'Q'): float(v)
                              for d, v in list(csv.reader(open(f'{raw}/{s}.csv')))[1:] if v not in ('', '.')})
        # y = ln(消費/GDP) = ln C − ln Y。欠測は落とす。
        Y[c] = np.log(rd(f'NAEXKP02{c}Q661S') / rd(f'NAEXKP01{c}Q661S')).dropna()
    # 日本だけは別ファイルを使う(1994年より前を ESRI の遡及系列でつないだもの)。
    sp = pd.read_csv(spliced)
    sp['p'] = [pd.Period(f"{d[:4]}Q{(int(d[5:7]) - 1) // 3 + 1}", 'Q') for d in sp.date]
    Y['JP'] = sp.set_index('p')['y_lncons_minus_lngdp']
    # 全ての国を共通の四半期の目盛り(1960Q1〜2023Q3)にそろえる。データのない期は NaN になる。
    idx = pd.period_range('1960Q1', '2023Q3', freq='Q')
    return pd.DataFrame({c: Y[c].reindex(idx) for c in Y})

# 税率変更の一覧(vat_rate_changes.csv)を読み、quarter 列を四半期(Period)にする。
def load_changes(path):
    v = pd.read_csv(path, encoding='utf-8-sig')
    v['p'] = [pd.Period(q, 'Q') for q in v.quarter]
    return v

# ==== (2) 比較国(ドナー)の選び方 ====
# treated = 処置国、t0 = 税率変更の四半期。pre_n = 変更前 40 四半期、post_n = 変更後 20 四半期。
def donor_set(Y, chg, treated, t0, pre_n=40, post_n=20, restricted=False, break_rule=True):
    # t0 の位置を探す。前後の窓が系列の範囲に収まらなければ、推定せずに None を返して終わる。
    i0 = Y.index.get_loc(t0)
    if i0 - pre_n < 0 or i0 + post_n > len(Y): return None, None, None
    # pre = 変更前の 40 四半期、post = 変更後の 20 四半期(t0 を含む)。
    pre, post = Y.index[i0 - pre_n:i0], Y.index[i0:i0 + post_n]
    win = list(pre) + list(post)
    # 処置国が窓の中で欠測を含むなら、推定しない。
    if Y.loc[win, treated].isna().any(): return None, None, None
    # 他の税率変更を探し始める四半期。通常は t0 から。restricted=True のときは窓の最初(pre[0])から探す(より厳しい条件)。
    lo = pre[0] if restricted else t0
    don = []
    # 各国を比較国の候補として、次の3つの条件で選ぶ。
    for c in Y.columns:
        if c == treated: continue
        # 条件1: 窓の中に欠測がない。
        if Y.loc[win, c].isna().any(): continue
        # 条件2: lo から post の最後までに、自国の標準税率の変更がない。
        if ((chg.country == c) & (chg.p >= lo) & (chg.p <= post[-1])).any(): continue
        # 条件3: 窓の中にデータ断絶の四半期がない(break_rule=False ならこの条件は使わない)。
        if break_rule and c in DATA_BREAKS and pd.Period(DATA_BREAKS[c], 'Q') in win: continue
        don.append(c)
    return pre, post, don

# ==== (3) 合成コントロール(SCM)の重み ====
# 変更前の期間で、処置国の y を最もよく再現する比較国の重みを探す。制約は「重みは 0 以上、合計 1」。
# 二次計画問題を SLSQP 法で解く。y = 処置国の系列、X = 比較国の系列(行=四半期、列=国)。
def scm_qp(y, X):
    T, J = X.shape
    # 比較国が1つなら、重みは 1。
    if J == 1: return np.ones(1)
    best = None
    # 初期値を2通り試す(等ウェイト、と、最も近い1国に寄せた点)。局所解を避けるため。
    for w0 in (np.full(J, 1.0 / J), np.eye(J)[int(np.argmin(((y[:, None] - X) ** 2).sum(0)))] * 0.9 + 0.1 / J):
        # 目的関数: 変更前の二乗誤差 Σ(y − Xw)^2(勾配 jac も与える)。制約: 重みの和 = 1。範囲: 各重みは 0〜1。
        r = minimize(lambda w: np.sum((y - X @ w) ** 2), w0, jac=lambda w: -2 * X.T @ (y - X @ w), method='SLSQP', bounds=[(0, 1)] * J,
                     constraints=({'type': 'eq', 'fun': lambda w: w.sum() - 1, 'jac': lambda w: np.ones(J)},), options={'maxiter': 2000, 'ftol': 1e-14})
        # 数値誤差で出た微小な負の値を 0 に切り、合計が 1 になるよう直して、二乗誤差を計算し直す。
        w = np.clip(r.x, 0, None); w /= w.sum(); f = np.sum((y - X @ w) ** 2)
        # 2つの初期値のうち、誤差が小さいほうを採用する。
        if best is None or f < best[0] - 1e-15: best = (f, w)
    return best[1]

# 各四半期で、比較国の平均を引く(中心化)。ridge 補正で使う。
def _center(X): return X - X.mean(axis=1, keepdims=True)

# ==== (4) ridge 補正(ASCM)の罰則 λ の選び方 ====
# 変更前の四半期を1期ずつ抜いて予測する交差検証(leave-one-out)。
# 各 t を除いて重みを作り直し(wt)、その残差 r に ridge 補正を加えて t 期を予測し、λ ごとに予測誤差の二乗を記録する。
def ascm_lambda(y, X, w, grid=LAMBDA_GRID):
    # Xc = 中心化した X。sq[k, t] = λ が grid[k] のとき、t 期を抜いた予測誤差の二乗。
    T0, J = X.shape; Xc = _center(X); sq = np.empty((len(grid), T0))
    for t in range(T0):
        # t 期を除いたデータで推定する。
        keep = np.arange(T0) != t
        # t 期抜きの SCM 重み wt と、その残差 r。
        wt = scm_qp(y[keep], X[keep]); r = y[keep] - X[keep] @ wt
        # 固有値分解を使うと、ridge の解 (Xc'Xc + λI)^-1 Xc' r を、λ ごとに素早く計算できる。
        s, V = np.linalg.eigh(Xc[keep].T @ Xc[keep]); Vb = V.T @ (Xc[keep].T @ r)
        # SCM だけによる t 期の予測。
        pred_c = X[t] @ wt
        # ridge 補正を加えた予測と実際の差の二乗。
        for k, lam in enumerate(grid): sq[k, t] = (y[t] - pred_c - X[t] @ (V @ (Vb / (s + lam)))) ** 2
    # m = λ ごとの平均予測誤差、se = その標準誤差、i = 平均誤差が最小の λ の位置。
    m = sq.mean(1); se = sq.std(1, ddof=1) / np.sqrt(T0); i = int(np.argmin(m))
    # 「1標準誤差ルール」: 最小誤差から 1 標準誤差以内で、いちばん大きい λ(いちばん強い罰則)を選ぶ。
    return max(grid[k] for k in range(len(grid)) if m[k] <= m[i] + se[i])

# ==== (5) 1回の推定(SCM または ASCM) ====
# D = 窓の最初を 0 にそろえた y の表。ASCM=True なら ridge 補正を加える。
def fit(D, treated, pool, pre, post, ascm=True):
    """D: rebased outcome frame. returns dict(gap_pre, gap_post, w, lam)"""
    # y = 処置国の変更前の系列、X = 比較国の変更前の系列。
    y = D.loc[pre, treated].values; X = D.loc[pre, pool].values
    # まず通常の SCM の重み w。
    w = scm_qp(y, X); lam = np.nan
    if ascm:
        # ASCM: λ を選び、重みを w ← w + (Xc'Xc + λI)^-1 Xc'(y − Xw) と補正する。補正後の重みは負にもなりうる。
        lam = ascm_lambda(y, X, w); Xc = _center(X)
        w = w + np.linalg.solve(Xc.T @ Xc + lam * np.eye(len(pool)), Xc.T @ (y - X @ w))
    # gap = 実際 − 合成。変更前の gap は当てはまりの誤差、変更後の gap が税率変更の影響の推定値。
    g_pre = y - X @ w; g_post = D.loc[post, treated].values - D.loc[post, pool].values @ w
    return dict(gap_pre=g_pre, gap_post=g_post, w=w, lam=lam)

# ==== (6) 推定結果の要約 ====
# 単位は 100 倍して「%ポイント」。
def summarize(f):
    gp, gq = f['gap_pre'], f['gap_post']; h = np.arange(len(gq))
    # RMSPE(二乗平均平方根予測誤差)を、変更前と変更後で計算する。
    pre = float(np.sqrt(np.mean(gp ** 2))); post = float(np.sqrt(np.mean(gq ** 2)))
    # ratio = 変更後 RMSPE / 変更前 RMSPE(プラセボ検定に使う比)。
    # mean_gap = 変更後 20 四半期の gap の平均。slope = gap の時間傾き(1年あたり、4倍)。gap_path = gap の経路。
    return dict(pre_rmspe=100 * pre, post_rmspe=100 * post, ratio=post / pre if pre > 0 else np.nan,
                mean_gap=100 * float(gq.mean()), slope=100 * 4 * float(np.polyfit(h, gq, 1)[0]), gap_path=100 * gq)

# ==== (7) 1つのエピソード全体 ====
# 比較国を決め、ASCM と SCM を推定し、プラセボ検定を行う。
def run_episode(Y, chg, treated, t0, pre_n=40, post_n=20, restricted=False, break_rule=True, placebo=True, estimators=('ascm', 'scm')):
    pre, post, don = donor_set(Y, chg, treated, t0, pre_n, post_n, restricted, break_rule)
    # 比較国が 3 つ未満なら、推定しない。
    if don is None or len(don) < 3: return None
    # 窓の最初の四半期を 0 にそろえる(国ごとの水準の差を消す)。
    D = Y - Y.loc[pre[0]]
    out = dict(treated=treated, t0=str(t0), pre_n=pre_n, donors=don, J=len(don))
    # 推定法(ASCM、SCM)ごとに実行する。
    for est in estimators:
        a = est == 'ascm'
        # 処置国の推定と要約。
        f = fit(D, treated, don, pre, post, a); s = summarize(f)
        # 重みが 0.0001 より大きい比較国だけを記録する。
        s['weights'] = {c: float(x) for c, x in zip(don, f['w']) if abs(x) > 1e-4}; s['lam'] = f['lam']
        pl = {}
        # プラセボ: 比較国の1つ1つを「仮の処置国」とみなし、残りの比較国(自分を除く)で同じ推定をやり直す。
        if placebo and len(don) >= 3:
            for j in don:
                pool = [c for c in don if c != j]
                pl[j] = summarize(fit(D, j, pool, pre, post, a))
        s['placebo'] = pl
        if pl:
            # 順位 = 比 ratio が処置国より大きいプラセボの数 + 1。
            # p値 = (処置国以上の ratio の数 + 1) / (国数 + 1)。
            n = len(pl) + 1
            s['rank_ratio'] = 1 + sum(v['ratio'] > s['ratio'] for v in pl.values())
            s['p_ratio'] = (1 + sum(v['ratio'] >= s['ratio'] for v in pl.values())) / n
        out[est] = s
    return out
