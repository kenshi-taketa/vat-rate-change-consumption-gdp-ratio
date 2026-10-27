"""再実行の結果が、保存してある基準の結果と一致するかを確かめる。
usage: python compare_rerun.py 基準のOUTフォルダ 再実行のOUTフォルダ
比べるもの: (1) episode_results.csv の数値の列、(2) aggregate_results.json の数値。
決まった計算(推定値、RMSPE、重みなど)は 1e-8 より小さい差なら「一致」。
乱数を使う計算(順列検定: perm_ で始まる項目)は、抽選の順序で値がわずかに動くので、別に集計し、差が 0.03 以内なら「許容」とする。"""
import sys, json, numpy as np, pandas as pd
A, B = sys.argv[1:3]
# (1) エピソード別の結果: キー(ep, tag, est)で並べて、数値の列ごとに差の最大値を出す
key = ['ep', 'tag', 'est']
a = pd.read_csv(f'{A}/episode_results.csv', encoding='utf-8-sig').set_index(key).sort_index()
b = pd.read_csv(f'{B}/episode_results.csv', encoding='utf-8-sig').set_index(key).sort_index()
print('episode_results: 行数', len(a), len(b), '| 行の名前が同じ:', a.index.equals(b.index))
worst = 0.0
for c in a.select_dtypes('number').columns:
    d = float(np.nanmax(np.abs(a[c].values - b[c].values))) if a.index.equals(b.index) else np.nan
    worst = max(worst, d); print(f'  {c:12s} 最大の差 {d:.2e}')
# (2) 集計結果(JSON): 入れ子の中の数値を全部たどって比べる
def walk(x, y, path=''):
    if isinstance(x, dict):
        for k in x: yield from walk(x[k], y.get(k) if isinstance(y, dict) else None, f'{path}/{k}')
    elif isinstance(x, (int, float)) and isinstance(y, (int, float)):
        yield path, abs(x - y)
ja, jb = json.load(open(f'{A}/aggregate_results.json')), json.load(open(f'{B}/aggregate_results.json'))
diffs = [(p, d) for p, d in walk(ja, jb) if d == d]
det = [(p, d) for p, d in diffs if '/perm_' not in p]; mc = [(p, d) for p, d in diffs if '/perm_' in p]
md = max((d for _, d in det), default=0.0); mm = max((d for _, d in mc), default=0.0)
print('aggregate_results: 決まった計算', len(det), '個 最大の差', f'{md:.2e}', '| 乱数を使う計算', len(mc), '個 最大の差', f'{mm:.2e}')
bad = [p for p, d in mc if d >= 0.03]
if bad: print('  乱数を使う計算で 0.03 以上の差:', bad[:5])
print('判定:', '一致(乱数を使う計算は許容の範囲)' if max(worst, md) < 1e-8 and mm < 0.03 else '差あり(上の列・場所を確認)')
