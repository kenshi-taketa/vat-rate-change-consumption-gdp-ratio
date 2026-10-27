"""P7: FREDの四半期系列(実質民間消費・実質GDP、指数 2015=100)の始期・終期を一覧にする(第2弾)。

使い方(Windows、Python 3 が入っていればよい。追加のパッケージは不要):
    py fetch_fred_starts_idx.py
同じフォルダに fred_series_starts_idx.csv ができる。FRED の公開CSV
(https://fred.stlouisfed.org/graph/fredgraph.csv?id=系列コード)を読むだけで、APIキーは不要。
実行はご自身のPCで行う。結果ファイルは、そのままClaudeに渡せる。

系列の種類:
  PCE_IDX = NAEXKP02{国}Q661S  (OECD MEI、実質民間最終消費、季節調整済み、指数 2015=100)
  GDP_IDX = NAEXKP01{国}Q661S  (OECD MEI、実質GDP、季節調整済み、指数 2015=100)
英国論文のパネルは、この指数系列(Q661S)を使っていると考えられる。
"""
import csv
import os
import sys
import time
import urllib.request
import urllib.error

COUNTRIES = ['AT', 'AU', 'BE', 'CA', 'CH', 'CL', 'CO', 'CZ', 'DE', 'DK', 'EE', 'ES', 'FI', 'FR',
             'GB', 'GR', 'HU', 'IE', 'IL', 'IS', 'IT', 'JP', 'KR', 'LT', 'LU', 'LV', 'MX', 'NL',
             'NO', 'NZ', 'PL', 'PT', 'SE', 'SI', 'SK', 'TR', 'US']
EU = {'AT', 'BE', 'CZ', 'DE', 'DK', 'EE', 'ES', 'FI', 'FR', 'GR', 'HU', 'IE', 'IT', 'LT', 'LU', 'LV',
      'NL', 'PL', 'PT', 'SE', 'SI', 'SK'}

URL = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id={}'


def fetch(series_id):
    req = urllib.request.Request(URL.format(series_id), headers={'User-Agent': 'Mozilla/5.0 (research data check)'})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            text = r.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return ('HTTP %s' % e.code, None, None, 0)
    except Exception as e:  # network error, timeout, etc.
        return ('ERROR %s' % type(e).__name__, None, None, 0)
    rows = list(csv.reader(text.splitlines()))
    if len(rows) < 2:
        return ('EMPTY', None, None, 0)
    first = last = None
    n = 0
    for row in rows[1:]:
        if len(row) < 2:
            continue
        v = row[1].strip()
        if v in ('', '.'):
            continue
        try:
            float(v)
        except ValueError:
            continue
        n += 1
        if first is None:
            first = row[0]
        last = row[0]
    return ('OK' if n else 'NO DATA', first, last, n)


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fred_series_starts_idx.csv')
    jobs = []
    for c in COUNTRIES:
        jobs.append((c, 'PCE_IDX', 'NAEXKP02%sQ661S' % c))
        jobs.append((c, 'GDP_IDX', 'NAEXKP01%sQ661S' % c))
    with open(out, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['country', 'kind', 'series_id', 'status', 'first_obs', 'last_obs', 'n_obs'])
        for i, (c, kind, sid) in enumerate(jobs, 1):
            status, first, last, n = fetch(sid)
            w.writerow([c, kind, sid, status, first or '', last or '', n])
            f.flush()
            print('%3d/%d %-18s %-8s %s %s %s' % (i, len(jobs), sid, status, first or '', last or '', n))
            time.sleep(0.3)
    print('\n書き出し:', out)


if __name__ == '__main__':
    sys.exit(main())
