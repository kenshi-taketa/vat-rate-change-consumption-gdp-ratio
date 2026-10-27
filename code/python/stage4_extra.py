"""P6 stage 4 extras: extended-sample tables, extra spec-curve cells, permutation draws, figures. usage: python stage4_extra.py OUTDIR EPISODES CORE MOTIVE"""
import sys, re, json, numpy as np, pandas as pd
OUT, EPI, CORE, MOT = sys.argv[1:5]
# aggregate_stage4.py の前半(関数の定義まで)をそのまま実行して、R・E・aggregate・stat_vec などを使えるようにする。
# 同じ乱数の流れで続きを計算するので、Table 3 の値は再現される。
src = open('aggregate_stage4.py', encoding='utf-8').read(); head = src[:src.index('res = {}')]
sys.argv = ['x', OUT, EPI, CORE, MOT, '100000']; exec(head)      # defines R, E, core, aggregate, stat_vec, pi, inc, cut, CORE, B, rng
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
# ユーロ危機の3件(ハンガリー2012Q1、オランダ2012Q4、スロベニア2013Q3)。
EURO = {'HU2012Q1', 'NL2012Q4', 'SI2013Q3'}
# 拡張標本の全エピソード(英国1979のQ3版は除く)。
ext = sorted({e for (e, t) in R if t == 'main' and e not in ('GB1979Q3',)})
# ある条件 sel を満たす拡張標本のエピソードを集めて、ASCM(または SCM)で集計し、推定値・p値・ランダム平均の分位点を返す。
def grp(sel, est='ascm'):
    out = {}
    for what in ('mean_gap', 'norm_gap'):
        a = aggregate([e for e in ext if sel(e)], 'main', est, what)
        out[what] = None if a is None else dict(n=a['n'], estimate=round(a['estimate'], 3), p2=round(a['perm_p_two'], 3), q025=round(a['perm_q025'], 2), q975=round(a['perm_q975'], 2), q05=round(a['perm_q05'], 2), q95=round(a['perm_q95'], 2))
    return out
# 短い関数: 種類(増税/減税)、他の税率変更がないか(clean)、変更幅、年。
K = lambda e: E.loc[e].kind; clean = lambda e: E.loc[e].own_other_changes_post == 0; ch = lambda e: abs(E.loc[e].change_pp); yr = lambda e: int(e[2:6])
# 拡張標本の分け方: 他の税率変更がない増税(信頼度別、変更幅別、時期別)、他の変更を伴う増税、減税。
groups = {
 'increase_clean_all': lambda e: K(e) == 'increase' and clean(e),
 'increase_clean_HIGH': lambda e: K(e) == 'increase' and clean(e) and E.loc[e].confidence == 'HIGH',
 'increase_clean_MEDIUM': lambda e: K(e) == 'increase' and clean(e) and E.loc[e].confidence == 'MEDIUM',
 'increase_clean_size<2': lambda e: K(e) == 'increase' and clean(e) and ch(e) < 2,
 'increase_clean_size2-<3': lambda e: K(e) == 'increase' and clean(e) and 2 <= ch(e) < 3,
 'increase_clean_size>=3': lambda e: K(e) == 'increase' and clean(e) and ch(e) >= 3,
 'increase_clean_pre2000': lambda e: K(e) == 'increase' and clean(e) and yr(e) < 2000,
 'increase_clean_2000-09': lambda e: K(e) == 'increase' and clean(e) and 2000 <= yr(e) < 2010,
 'increase_clean_2010-13': lambda e: K(e) == 'increase' and clean(e) and 2010 <= yr(e) <= 2013,
 'increase_clean_2014+': lambda e: K(e) == 'increase' and clean(e) and yr(e) >= 2014,
 'increase_clean_ex_2010-13': lambda e: K(e) == 'increase' and clean(e) and not (2010 <= yr(e) <= 2013),
 'increase_with_other_changes': lambda e: K(e) == 'increase' and not clean(e),
 'cut_clean': lambda e: K(e) == 'cut' and clean(e), 'cut_with_other_changes': lambda e: K(e) == 'cut' and not clean(e), 'cut_all': lambda e: K(e) == 'cut'}
# 分け方ごと・推定法ごとに集計して extended_group_tables.csv に保存する。
rows = []
for g, f in groups.items():
    for est in ('ascm', 'scm'):
        r = grp(f, est)
        for what, v in r.items():
            if v: rows.append(dict(group=g, est=est, outcome=what, **v))
pd.DataFrame(rows).to_csv(f'{OUT}/extended_group_tables.csv', index=False, encoding='utf-8-sig')
# extra spec cells (core increases)
# 核増税の追加の仕様: 全11件、ユーロ危機3件を除く、日本2014を除く、両方を除く、英国1979をQ3にした版。Table 3 の下の行はここから出る。
sc = []
# 英国1979のQ3版の結果を、同じ名前で使えるようにする。
R[('GB1979Q3', 'main')] = R[('GB1979Q3', 'main_GB1979Q3')]
for lab, eps in (('all 11', inc), ('drop euro-crisis HU/NL/SI', [e for e in inc if e not in EURO]), ('drop JP2014', [e for e in inc if e != 'JP2014Q2']), ('drop JP2014+euro', [e for e in inc if e not in EURO | {'JP2014Q2'}]), ('GB1979Q3 in place of Q2', [('GB1979Q3' if e == 'GB1979Q2' else e) for e in inc])):
    for est in ('ascm', 'scm'):
        a = aggregate(eps, 'main', est, 'mean_gap')
        sc.append(dict(cell=lab, est=est, n=a['n'], estimate=round(a['estimate'], 3), perm_p_two=round(a['perm_p_two'], 3), q025=round(a['perm_q025'], 2), q975=round(a['perm_q975'], 2), q05=round(a['perm_q05'], 2), q95=round(a['perm_q95'], 2)))
pd.DataFrame(sc).drop_duplicates().to_csv(f'{OUT}/spec_extra_core_increases.csv', index=False, encoding='utf-8-sig')
# permutation draws (headline): core increases, ASCM, mean gap, equal weights
# 図3(左)の元になる、核増税11件の10万個のランダム平均を、保存用に作り直す(npz ファイル)。
ok, obs, pls, wi = stat_vec(inc, 'main', 'ascm', 'mean_gap'); w = np.ones(len(ok)) / len(ok)
rg = np.random.default_rng(20261015); perm = sum(w[i] * pls[i][rg.integers(0, len(pls[i]), 100000)] for i in range(len(ok)))
np.savez_compressed(f'{OUT}/perm_draws_core_increases_ascm_meangap.npz', draws=perm, episodes=np.array(ok), observed=float((w * obs).sum()))
# figures
# ここから図(4枚の元)。図の描画のみで、数値の結果は変えない。
Pth = {e: np.array(R[(e, 'main')]['ascm']['gap_path']) for e in CORE if (e, 'main') in R}
fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
for e in inc:
    ax[0].plot(range(20), Pth[e], lw=1, color='#9aa5b1', label=None)
ax[0].plot(range(20), np.mean([Pth[e] for e in inc], 0), lw=2.5, color='#c0392b', label='mean of 11 increases'); ax[0].plot(range(20), Pth['JP2014Q2'], lw=1.8, color='#1f4e79', label='JP2014'); ax[0].axhline(0, c='k', lw=.6)
ax[0].set_title('ASCM gap path (pp), core increases'); ax[0].set_xlabel('quarters since tax date'); ax[0].legend(frameon=False)
est_ = {e: R[(e, 'main')]['ascm']['mean_gap'] for e in CORE}; order = sorted(est_, key=est_.get)
for k, e in enumerate(order):
    pl = [v['mean_gap'] for v in R[(e, 'main')]['ascm']['placebo'].values()]
    ax[1].plot([np.quantile(pl, .05), np.quantile(pl, .95)], [k, k], c='#c9d1d9', lw=5, solid_capstyle='butt'); ax[1].plot(est_[e], k, 'o', c='#c0392b' if K(e) == 'increase' else '#1f4e79')
ax[1].set_yticks(range(len(order))); ax[1].set_yticklabels(order, fontsize=8); ax[1].axvline(0, c='k', lw=.6); ax[1].set_title('mean gap (pp) vs placebo 5-95% band\n(red=increase, blue=cut)')
ax[2].hist(perm, bins=80, color='#c9d1d9'); ax[2].axvline(float((w * obs).sum()), c='#c0392b'); ax[2].set_title('permutation distribution of the 11-episode mean gap\nobserved in red'); ax[2].set_xlabel('pp')
for a in ax: a.spines[['top', 'right']].set_visible(False)
plt.tight_layout(); plt.savefig(f'{OUT}/fig_stage4_core.png', dpi=150)
print(pd.read_csv(f'{OUT}/extended_group_tables.csv').query("outcome=='norm_gap' and est=='ascm'").to_string()); print(pd.read_csv(f'{OUT}/spec_extra_core_increases.csv').to_string())
