r"""P6 stage 2 remainder (2026-10-15). Standard library only. Run: py stage2_remaining_checks_20261015.py
Run in the P6 folder (needs raw_fred_20261015\, fred_download_log_20261015.csv, and the path to the Japan paper's
retro_2780_parsed_full.csv given as argv[1] or the default below).
Outputs: stage2_md5_check_20261015.txt, stage2_series_checks_20261015.csv, panel_japan_spliced_20261015.csv
1) md5/bytes of every raw file vs the download log. 2) structure checks of the 34 Q661S pairs (gaps, 2015 mean, largest
quarterly jump of ln C - ln Y). 3) Japan splice: ESRI retro (private consumption total, GDP) scaled by a constant factor at 1994Q1."""
import csv, hashlib, math, os, sys
RAW = 'raw_fred_20261015/'
RETRO = sys.argv[1] if len(sys.argv) > 1 else r'..\消費増税の下方屈折効果_日本応用\extended_preperiod_1980\data_prep\retro_2780_parsed_full.csv'
def load(f): return {d[:7]: float(v) for d, v in list(csv.reader(open(RAW + f + '.csv')))[1:] if v not in ('', '.')}
log = list(csv.DictReader(open('fred_download_log_20261015.csv', encoding='utf-8-sig')))
ok = bad = 0; lines = []
for x in log:
    if x['status'] != 'OK': continue
    b = open(RAW + x['file'], 'rb').read()
    if hashlib.md5(b).hexdigest() == x['md5'] and len(b) == int(x['bytes']): ok += 1
    else: bad += 1; lines.append('MISMATCH ' + x['file'])
lines.insert(0, f'md5+bytes match: {ok}, mismatch: {bad}')
open('stage2_md5_check_20261015.txt', 'w').write('\n'.join(lines) + '\n')
def gaps(ds): return sum(1 for a, b in zip(ds, ds[1:]) if (int(b[:4]) * 12 + int(b[5:7])) - (int(a[:4]) * 12 + int(a[5:7])) != 3)
ccs = sorted({f[8:10] for f in os.listdir(RAW) if f.startswith('NAEXKP02')})
with open('stage2_series_checks_20261015.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['country', 'first', 'last', 'nC', 'nG', 'same_dates', 'gaps', 'mean2015_C', 'mean2015_G', 'max_jump_pp', 'jump_at'])
    for cc in ccs:
        c = load(f'NAEXKP02{cc}Q661S'); g = load(f'NAEXKP01{cc}Q661S'); dc = sorted(c)
        y = [(d, math.log(c[d]) - math.log(g[d])) for d in dc if d in g]
        mx = max((abs(y[i][1] - y[i - 1][1]), y[i][0]) for i in range(1, len(y)))
        m = lambda s: sum(v for d, v in s.items() if d.startswith('2015')) / 4
        w.writerow([cc, dc[0], dc[-1], len(c), len(g), dc == sorted(g), gaps(dc), round(m(c), 2), round(m(g), 2), round(mx[0] * 100, 2), mx[1]])
R = {}
for r in csv.DictReader(open(RETRO)):
    R[f"{r['year']}-{int(r['quarter']) * 3 - 2:02d}"] = (float(r['pce_total_retro']), float(r['gdp_retro']))
qc, qg = load('NAEXKP02JPQ661S'), load('NAEXKP01JPQ661S'); k0 = '1994-01'
fc, fg = qc[k0] / R[k0][0], qg[k0] / R[k0][1]
with open('panel_japan_spliced_20261015.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['date', 'cons_idx', 'gdp_idx', 'source', 'y_lncons_minus_lngdp'])
    for k in sorted(R):
        if k < k0: w.writerow([k + '-01', f'{R[k][0] * fc:.10g}', f'{R[k][1] * fg:.10g}', 'ESRI_retro_scaled', f'{math.log(R[k][0] * fc / (R[k][1] * fg)):.10g}'])
    for k in sorted(qc):
        if k >= k0 and k in qg: w.writerow([k + '-01', f'{qc[k]:.10g}', f'{qg[k]:.10g}', 'FRED_Q661S', f'{math.log(qc[k] / qg[k]):.10g}'])
print('done')
