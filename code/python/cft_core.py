"""P6 stage 4: Cattaneo-Feng-Titiunik prediction intervals (scpi_pkg), same settings as the UK paper s4_cft.py (simplex, 2.5%/side, sims=500, seed 20261010, e_method all).
usage: python cft_core.py RAW SPL VAT CORE OUT"""
import sys, warnings, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from p6est import *
from scpi_pkg.scdata import scdata
from scpi_pkg.scpi import scpi
# 引数: RAW=FRED の CSV フォルダ、SPL=日本のつなぎ系列、VAT=税率変更の一覧、CORE=核エピソード、OUT=出力先。
RAW, SPL, VAT, CORE, OUT = sys.argv[1:6]
Y = load_y(RAW, SPL); chg = load_changes(VAT); core = pd.read_csv(CORE, encoding='utf-8-sig'); core = core[core.tier == 'core']
# 乱数の種(固定)。
np.random.seed(20261010); rows = []
# 核エピソードごとに scpi パッケージ(Cattaneo-Feng-Titiunik の予測区間)を実行する。
for e in core.episode:
    c, t0 = e[:2], pd.Period(e[2:], 'Q'); pre, post, don = donor_set(Y, chg, c, t0, 40, 20)
    D = (Y - Y.loc[pre[0]]).loc[list(pre) + list(post), [c] + don]; tmap = {d: i for i, d in enumerate(D.index)}
    # scpi が求める縦長の形(id・time・y)に直す。
    long = D.reset_index(names='date').melt(id_vars='date', var_name='id', value_name='y'); long['time'] = long['date'].map(tmap)
    row = dict(episode=e, T0=len(pre), T1=len(post), J=len(don))
    try:
        # scpi 用のデータ。比較国は simplex 制約(重みは 0 以上で合計 1)の SCM。
        dd = scdata(long[['id', 'time', 'y']], id_var='id', time_var='time', outcome_var='y', period_pre=np.arange(len(pre)), period_post=np.arange(len(pre), len(pre) + len(post)),
                    unit_tr=c, unit_co=don, constant=False, cointegrated_data=False, verbose=False)
        # 予測区間: 重みの推定の不確実性と、比較国で説明できない部分の不確実性を、シミュレーション 500 回で計算する(片側 2.5%)。
        res = scpi(dd, w_constr={'name': 'simplex'}, sims=500, cores=1, verbose=False, e_method='all', u_alpha=0.025, e_alpha=0.025, u_order=1, e_order=1, u_lags=0, e_lags=0)
        # mean_gap_pp = 後 20 四半期の gap の平均(%ポイント)。
        y = D.loc[post, c].values; row['mean_gap_pp'] = round(float(np.mean(y - res.Y_post_fit.values.ravel())) * 100, 2)
        # 3種類の区間(gaussian・ls・qreg)について、gap の区間が 0 を含まない四半期の数などを数える。
        for m, a in [('gaussian', 'CI_all_gaussian'), ('ls', 'CI_all_ls'), ('qreg', 'CI_all_qreg')]:
            ci = getattr(res, a); lo = y - ci['Upper'].values; hi = y - ci['Lower'].values
            row[m + '_n_excl0'] = int(np.sum((lo > 0) | (hi < 0))); row[m + '_n_neg'] = int(np.sum(hi < 0)); row[m + '_n_pos'] = int(np.sum(lo > 0))
            row[m + '_mean_lo_pp'] = round(lo.mean() * 100, 1); row[m + '_mean_hi_pp'] = round(hi.mean() * 100, 1)
    except Exception as ex: row['error'] = repr(ex)[:200]
    rows.append(row); print(row, flush=True)
pd.DataFrame(rows).to_csv(f'{OUT}/cft_core.csv', index=False)
