"""P6 stage 4 aggregation + permutation inference. usage: python aggregate_stage4.py OUTDIR EPISODES CORE MOTIVE [B]
Reads OUTDIR/res/*.pkl; writes OUTDIR/*.csv and OUTDIR/aggregate_results.json."""
import sys, os, glob, pickle, json
import numpy as np, pandas as pd
# 引数: OUT=出力先(run_stage4.py の結果が OUT/res にある)、EPI=エピソード候補、CORE=核エピソード、MOT=動機の分類表、B=順列検定の抽選回数(既定 10万)。
OUT, EPI, CORE, MOT = sys.argv[1:5]; B = int(sys.argv[5]) if len(sys.argv) > 5 else 100000
# 順列検定の乱数の種(再現のため固定)。
SEED = 20261015
# エピソード候補の表。E[エピソード名] で1行を引く(エピソード名 = 国コード + 四半期、例 JP2014Q2)。
epi = pd.read_csv(EPI, encoding='utf-8-sig'); epi['ep'] = epi.country + epi.quarter; E = epi.set_index('ep')
# 感度分析用: 英国1979 を Q3 の日付とした版を、同じ表に追加する。
E.loc['GB1979Q3'] = E.loc['GB1979Q2']   # sensitivity: UK paper's tax date
# 核エピソードの表(tier = core または感度)。
core = pd.read_csv(CORE, encoding='utf-8-sig').set_index('episode')
# 動機の分類表(結果を見ずに作ったもの)。
mot = pd.read_csv(MOT, encoding='utf-8-sig').set_index('episode')
# R[(エピソード, タグ)] = 推定結果。run_stage4.py が保存した pickle を全部読み込む。
R = {}
for f in glob.glob(f'{OUT}/res/*.pkl'):
    d = pickle.load(open(f, 'rb')); c, q, pn, rs, br, tag = d['task']
    if d['res'] is not None: R[(c + q, tag)] = d['res']
# 税率変更が価格に 100% 転嫁されたときの価格上昇率(%) = (新税率 − 旧税率) / (1 + 旧税率/100)。
def pi(ep):   # full pass-through price effect, percent
    r = E.loc[ep]; return (r.new_rate - r.old_rate) / (1 + r.old_rate / 100)
# 1エピソード・1推定法の結果を1行にまとめる。norm_gap = mean_gap / pi(価格効果で割ったギャップ)。
def row(ep, tag, est):
    r = R.get((ep, tag)); 
    if r is None: return None
    s = r[est]; return dict(ep=ep, tag=tag, est=est, J=r['J'], pre_rmspe=s['pre_rmspe'], ratio=s['ratio'], mean_gap=s['mean_gap'], slope=s['slope'],
        norm_gap=s['mean_gap'] / pi(ep), p_ratio=s.get('p_ratio', np.nan), rank_ratio=s.get('rank_ratio', np.nan), kind=E.loc[ep].kind, change_pp=E.loc[ep].change_pp,
        price_pct=pi(ep), lam=s['lam'])
# ---------- episode table
# 全エピソード × タグ × 推定法の表を作り、episode_results.csv に保存する。
rows = [row(ep, tag, est) for (ep, tag) in R for est in ('ascm', 'scm')]
T = pd.DataFrame([r for r in rows if r]); T['tier'] = T.ep.map(lambda e: core.tier.get(e, 'extended'))
T['own_other_post'] = T.ep.map(lambda e: E.loc[e].own_other_changes_post); T['flags'] = T.ep.map(lambda e: E.loc[e].flags)
T.sort_values(['tag', 'est', 'ep']).to_csv(f'{OUT}/episode_results.csv', index=False, encoding='utf-8-sig')
# ---------- aggregation helpers
# ここから集計(順列検定)。乱数の流れは固定されているので、同じ順序で実行すれば同じ値になる。
rng = np.random.default_rng(SEED)
# 集計に使う統計量(mean_gap / slope / norm_gap)を、エピソードごとに集める。
# obs = 処置国の観測値、pls = 参照集合(各プラセボの値 + 処置国本人の値)。w_inv = 逆数ウェイト用(1/変更前RMSPE)。
def stat_vec(eps, tag, est, what, sign=None):
    """what in mean_gap/slope/norm_gap; returns observed vector and placebo arrays"""
    obs, pls, w_inv, ok = [], [], [], []
    for e in eps:
        r = R.get((e, tag)); 
        if r is None: continue
        s = r[est]; sg = 1.0 if sign is None else sign[e]
        div = pi(e) if what == 'norm_gap' else 1.0
        key = 'mean_gap' if what == 'norm_gap' else what
        obs.append(sg * s[key] / div if what != 'norm_gap' else sg * s['mean_gap'] / div * (1 if sg == 1 else 1))
        pls.append(np.array([sg * v[key] / div for v in s['placebo'].values()] + [obs[-1]])); w_inv.append(1 / s['pre_rmspe']); ok.append(e)   # reference set = placebos + the treated unit
    return ok, np.array(obs), pls, np.array(w_inv)
# 順列検定による集計。各エピソードの参照集合から1つずつランダムに選び、(ウェイト付き)平均を B 回作る。
# T0 = 観測された平均。p値(両側) = ランダム平均の絶対値が |T0| 以上になる割合(+1 の補正つき)。分位点も保存する。
def aggregate(eps, tag, est, what, sign=None, weights='equal'):
    ok, obs, pls, wi = stat_vec(eps, tag, est, what, sign)
    if len(ok) == 0: return None
    # ウェイト: 等ウェイト(既定)、または適合誤差の逆数ウェイト。
    w = np.ones(len(ok)) / len(ok) if weights == 'equal' else wi / wi.sum()
    # 観測された平均 T0。
    T0 = float((w * obs).sum())
    # 各エピソードについて、参照集合から B 回、1つずつ番号を抽選する。
    idx = [rng.integers(0, len(p), B) for p in pls]
    # B 個のランダム平均。
    perm = sum(w[i] * pls[i][idx[i]] for i in range(len(ok)))
    # 片側(T0 以下)と両側(絶対値が |T0| 以上)の数え上げ。
    n_le = int((perm <= T0).sum()); n_abs = int((np.abs(perm) >= abs(T0)).sum())
    sd = float(np.std(obs, ddof=1)) if len(obs) > 1 else np.nan
    # 結果: 推定値、ランダム平均の平均・標準偏差、p値、ランダム平均の分位点(2.5%・5%・95%・97.5%)。本文の95%範囲(Table 3)は 2.5% 点と 97.5% 点。
    return dict(n=len(ok), episodes=ok, estimate=T0, naive_se=sd / np.sqrt(len(ok)) if len(ok) > 1 else np.nan,
                perm_mean=float(perm.mean()), perm_sd=float(perm.std()), perm_p_onesided_le=(n_le + 1) / (B + 1), perm_p_two=(n_abs + 1) / (B + 1),
                perm_q025=float(np.quantile(perm,.025)), perm_q975=float(np.quantile(perm,.975)), perm_q05=float(np.quantile(perm, .05)), perm_q95=float(np.quantile(perm, .95)))
# 核エピソード(主標本)を、増税と減税に分ける。
CORE = [e for e in core.index if core.tier[e] == 'core']; SENS = [e for e in core.index if core.tier[e] != 'core']
inc = [e for e in CORE if E.loc[e].kind == 'increase']; cut = [e for e in CORE if E.loc[e].kind == 'cut']
# 減税は符号を反転して、増税と同じ向きにそろえる(プールした集計用)。
sign_flip = {e: (-1.0 if E.loc[e].kind == 'cut' else 1.0) for e in CORE}
# 集計結果の入れ物。
res = {}
# 核増税・核減税・符号をそろえたプールについて、推定法 × 統計量 × ウェイトごとに集計する。
for est in ('ascm', 'scm'):
    for what in ('mean_gap', 'slope', 'norm_gap'):
        res[f'core_increases|{est}|{what}|equal'] = aggregate(inc, 'main', est, what)
        res[f'core_increases|{est}|{what}|invrmspe'] = aggregate(inc, 'main', est, what, weights='invrmspe')
        res[f'core_cuts|{est}|{what}'] = aggregate(cut, 'main', est, what)
        res[f'core_pooled_signflip|{est}|{what}|equal'] = aggregate(CORE, 'main', est, what, sign=sign_flip)
# strata: motive class (assigned in D7 before any estimate) and period
# 動機の分類表の9列目から、a(税の振り替え)・b(赤字・債務)・c・a_b・? に直す。
def cls(e):
    v = str(mot.loc[e].iloc[8]) if e in mot.index else '?'
    return 'a_b' if v.startswith('a_b') else v[0] if v[0] in 'abc' else '?'
# 層別: 動機の別、時期の別(1975-99 / 2000-09 / 2010-)に、核エピソードを分けて集計する。
strata = {}
for lab, f in (('motive', cls), ('period', lambda e: '1975-99' if int(e[2:6]) < 2000 else '2000-09' if int(e[2:6]) < 2010 else '2010-')):
    for g in sorted({f(e) for e in CORE}):
        eps = [e for e in CORE if f(e) == g]
        for what in ('mean_gap', 'norm_gap'):
            a_ = aggregate(eps, 'main', 'ascm', what, sign=sign_flip)
            strata[f'{lab}={g}|{what}'] = dict(n=a_['n'], episodes=a_['episodes'], estimate=a_['estimate'], perm_p_two=a_['perm_p_two'], perm_q05=a_['perm_q05'], perm_q95=a_['perm_q95'])
res['strata_core_signflip_ascm'] = strata
# leave-one-out (ASCM mean gap, core increases)
# 1件ずつ除く、1か国ずつ除く、2010〜13年の群を除く、で平均ギャップがどう動くか。
loo = {}
for e in inc:
    loo['drop ' + e] = aggregate([x for x in inc if x != e], 'main', 'ascm', 'mean_gap')['estimate']
for c in sorted({e[:2] for e in inc}):
    loo['drop country ' + c] = aggregate([x for x in inc if x[:2] != c], 'main', 'ascm', 'mean_gap')['estimate']
yrs = lambda e: int(e[2:6]); loo['drop 2010-13 cluster'] = aggregate([x for x in inc if not (2010 <= yrs(x) <= 2013)], 'main', 'ascm', 'mean_gap')['estimate']
res['leave_one_out_core_increases_ascm_mean_gap'] = loo
# cluster-robust SE of the equal-weight mean (country clusters; calendar-period clusters)
# 同じ国・同じ時期の群でまとめたクラスター頑健標準誤差(等ウェイト平均)。
def clus(eps, key):
    ok, obs, _, _ = stat_vec(eps, 'main', 'ascm', 'mean_gap'); m = obs.mean(); g = pd.Series(obs - m, index=ok).groupby(key).sum()
    return float(np.sqrt((g ** 2).sum()) / len(ok)), len(g)
res['cluster_se_core_increases'] = {'country': clus(inc, lambda e: e[:2]), 'period(2010-13 vs other)': clus(inc, lambda e: 'c1013' if 2010 <= int(e[2:6]) <= 2013 else e)}
# specification curve: aggregate over core increases for every available tag
# 仕様曲線: 保存してあるすべてのタグ(変更前の長さ、restricted、nobreakrule 等)で、核増税の平均ギャップを集計する。
sc = []
for tag in sorted({t for (_, t) in R}):
    for est in ('ascm', 'scm'):
        a = aggregate([x for x in inc], tag, est, 'mean_gap')
        if a: sc.append(dict(tag=tag, est=est, n=a['n'], estimate=a['estimate'], perm_p=a['perm_p_onesided_le']))
pd.DataFrame(sc).to_csv(f'{OUT}/spec_curve_core_increases.csv', index=False, encoding='utf-8-sig')
# extended sample
# 拡張標本の集計(増税・減税、他の税率変更がないものだけ/すべて)。
ext_all = [e for (e, t) in R if t == 'main']
for lab, sel in (('ext_increases_clean', lambda e: E.loc[e].kind == 'increase' and E.loc[e].own_other_changes_post == 0),
                 ('ext_increases_all', lambda e: E.loc[e].kind == 'increase'),
                 ('ext_cuts_clean', lambda e: E.loc[e].kind == 'cut' and E.loc[e].own_other_changes_post == 0),
                 ('ext_cuts_all', lambda e: E.loc[e].kind == 'cut')):
    eps = [e for e in ext_all if sel(e)]
    for what in ('mean_gap', 'slope', 'norm_gap'):
        res[f'{lab}|ascm|{what}|equal'] = aggregate(eps, 'main', 'ascm', what)
# 集計結果を JSON に保存する。
json.dump(res, open(f'{OUT}/aggregate_results.json', 'w'), indent=1, default=float)
# event-time paths
# イベント時間の平均経路(変更後 20 四半期の gap の平均)を保存する。
paths = {}
for lab, eps in (('core_increases', inc), ('core_cuts', cut)):
    P = np.array([R[(e, 'main')]['ascm']['gap_path'] for e in eps if (e, 'main') in R]); paths[lab] = P.mean(0)
pd.DataFrame(paths).rename_axis('h').to_csv(f'{OUT}/event_time_paths_ascm.csv', encoding='utf-8-sig')
print(json.dumps({k: (v if not isinstance(v, dict) or 'estimate' not in v else {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items() if kk != 'episodes'}) for k, v in res.items() if k.startswith('core')}, indent=1, default=float)[:6000])
