"""2つの CSV(基準と再実行)の数値を比べる。usage: python compare_csv.py 基準.csv 再実行.csv キー列1[,キー列2...]
キー列(例 ep,est,q)で行を並べ、数値の列ごとに差の最大値を表示する。"""
import sys, numpy as np, pandas as pd
A, B, K = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
a = pd.read_csv(A, encoding='utf-8-sig').set_index(K).sort_index(); b = pd.read_csv(B, encoding='utf-8-sig').set_index(K).sort_index()
print('行数', len(a), len(b), '| 行の名前が同じ:', a.index.equals(b.index))
worst = 0.0
for c in a.select_dtypes('number').columns:
    if c not in b.columns: print(' ', c, '再実行にない列'); continue
    d = np.nanmax(np.abs(a[c].values - b[c].values)) if a.index.equals(b.index) else np.nan
    worst = max(worst, d if d == d else 0); print(f'  {c:16s} 最大の差 {d:.2e}')
for c in a.columns:
    if a[c].dtype == bool and c in b.columns and a.index.equals(b.index): print(f'  {c:16s} (真偽) 異なる行の数', int((a[c] != b[c]).sum()))
print('判定:', '一致' if worst < 1e-8 else '差あり(上を確認)')
