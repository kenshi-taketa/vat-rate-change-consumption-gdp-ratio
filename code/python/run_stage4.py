"""P6 stage 4 driver. usage: python run_stage4.py RAW SPLICED VAT_CHANGES EPISODES CORE OUTDIR [nproc]
Runs every task once and stores one pickle per task in OUTDIR/res (resumable)."""
import sys, os, pickle, time
import numpy as np, pandas as pd
from multiprocessing import Pool
# p6est.py の関数を全部使う(データ読み込み、推定など)。
from p6est import *
# 引数: RAW=FRED の CSV フォルダ、SPL=日本のつなぎ系列、VAT=税率変更の一覧、EPI=エピソード候補、CORE=核エピソード、OUT=出力先。
RAW, SPL, VAT, EPI, CORE, OUT = sys.argv[1:7]; NP = int(sys.argv[7]) if len(sys.argv) > 7 else 2
# 結果は OUT/res に、1仕事1ファイル(pickle)で保存する。途中で止まっても続きから再開できる。
os.makedirs(f'{OUT}/res', exist_ok=True)
# データを読む。
Y = load_y(RAW, SPL); chg = load_changes(VAT)
# エピソード候補と核エピソードの表を読む。
epi = pd.read_csv(EPI, encoding='utf-8-sig'); core = pd.read_csv(CORE, encoding='utf-8-sig')
# 推定の対象: 「今推定できる (estimable_now = Y)」かつ「信頼度が LOW でない」エピソード。LOW の行は使わない。
ext = epi[(epi.estimable_now == 'Y') & (epi.confidence != 'LOW')].copy(); ext['ep'] = ext.country + ext.quarter
core_ids = list(core.episode); tier = dict(zip(core.episode, core.tier))
# 実行する仕事の一覧を作る。各仕事 = (国, 四半期, 変更前の長さ, restricted, データ断絶規則を使うか, タグ)。
def tasks():
    T = []
    # 主推定(タグ main): 対象の全エピソード、変更前 40 四半期。
    main = [(r.country, r.quarter, 40, False, True, 'main') for r in ext.itertuples()]
    # 核エピソードを先に実行する。
    core_first = [t for t in main if t[0] + t[1] in core_ids]; rest = [t for t in main if t[0] + t[1] not in core_ids]
    T += core_first + rest
    for r in ext.itertuples():
        e = r.country + r.quarter
        if e in core_ids:
            # 核エピソードの頑健性: 変更前を 60・80 四半期・全期間にした版(タグ pre60 など)。
            for pn in (60, 80, 'full'): T.append((r.country, r.quarter, pn, False, True, f'pre{pn}'))
            # restricted: 窓の最初から他の税率変更がない国だけを比較国にする版。
            T.append((r.country, r.quarter, 40, True, True, 'restricted'))
            # nobreakrule: データ断絶規則を使わない版(補遺C2)。
            T.append((r.country, r.quarter, 40, False, False, 'nobreakrule'))
    # 感度: 英国1979 の税の日付を Q3 にした版。
    T.append(('GB', '1979Q3', 40, False, True, 'main_GB1979Q3'))
    return T
# 1つの仕事を実行し、結果を pickle に保存する。保存済みなら飛ばす。
def work(t):
    c, q, pn, rs, br, tag = t; f = f'{OUT}/res/{c}{q}__{tag}.pkl'
    if os.path.exists(f): return f, 0.0, 'cached'
    t0 = pd.Period(q, 'Q'); s = time.time()
    # 'full' = 系列の最初から t0 の直前までの全期間。
    if pn == 'full':
        first = Y[c].first_valid_index(); pn = Y.index.get_loc(t0) - Y.index.get_loc(first)
    # 推定(p6est.py の run_episode)。変更後は 20 四半期。
    r = run_episode(Y, chg, c, t0, pn, 20, rs, br)
    pickle.dump(dict(task=t, res=r), open(f, 'wb'))
    return f, time.time() - s, 'none' if r is None else f"J={r['J']}"
if __name__ == '__main__':
    T = tasks(); print(len(T), 'tasks', flush=True)
    # NP 個のプロセスで並列に実行する。
    with Pool(NP) as p:
        for i, (f, dt, msg) in enumerate(p.imap_unordered(work, T)):
            print(i + 1, os.path.basename(f), round(dt, 1), msg, flush=True)
