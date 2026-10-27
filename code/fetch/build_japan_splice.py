r"""Build the spliced Japan series (consumption and GDP indices, 1980Q1 onward).
Written 2026-10-28. The calculation is the same as in the last part of stage2_remaining_checks_20261015.py
(lines that read RETRO and write panel_japan_spliced_20261015.csv); it needs only two FRED files.

Usage: python build_japan_splice.py RAW_DIR ESRI_CSV OUT_CSV
  RAW_DIR  = folder with NAEXKP02JPQ661S.csv (consumption) and NAEXKP01JPQ661S.csv (GDP) from FRED
  ESRI_CSV = inputs/japan_esri_retro_parsed_2780.csv  (ESRI 'simplified retrospective' series, values as published)
  OUT_CSV  = output file

Before 1994Q1 the ESRI values (private consumption total, GDP) are multiplied by one constant per series, chosen so that
they equal the OECD value in 1994Q1. From 1994Q1 the OECD (FRED) values are used."""
import csv, math, sys
RAW, RETRO, OUT = sys.argv[1].rstrip('/\\') + '/', sys.argv[2], sys.argv[3]
def load(f): return {d[:7]: float(v) for d, v in list(csv.reader(open(RAW + f + '.csv')))[1:] if v not in ('', '.')}
R = {}
for r in csv.DictReader(open(RETRO)):
    R[f"{r['year']}-{int(r['quarter']) * 3 - 2:02d}"] = (float(r['pce_total_retro']), float(r['gdp_retro']))
qc, qg = load('NAEXKP02JPQ661S'), load('NAEXKP01JPQ661S'); k0 = '1994-01'
fc, fg = qc[k0] / R[k0][0], qg[k0] / R[k0][1]
with open(OUT, 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['date', 'cons_idx', 'gdp_idx', 'source', 'y_lncons_minus_lngdp'])
    for k in sorted(R):
        if k < k0: w.writerow([k + '-01', f'{R[k][0] * fc:.10g}', f'{R[k][1] * fg:.10g}', 'ESRI_retro_scaled', f'{math.log(R[k][0] * fc / (R[k][1] * fg)):.10g}'])
    for k in sorted(qc):
        if k >= k0 and k in qg: w.writerow([k + '-01', f'{qc[k]:.10g}', f'{qg[k]:.10g}', 'FRED_Q661S', f'{math.log(qc[k] / qg[k]):.10g}'])
print('done')
