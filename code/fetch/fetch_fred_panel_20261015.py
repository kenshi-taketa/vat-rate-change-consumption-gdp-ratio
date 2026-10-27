"""P6 stage 2: download the FRED quarterly index series (OECD MEI, 2015=100) and record provenance.

Run on the author's own PC (Windows: `py fetch_fred_panel_20261015.py`; Python 3.8+, standard library only).
No API key is needed: the public CSV endpoint https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES> is read.

Outputs (written next to this script):
  raw_fred_<YYYYMMDD>/<SERIES>.csv       the FRED file exactly as received (bytes unchanged)
  fred_download_log_<YYYYMMDD>.csv       one row per series: id, URL, retrieval time (UTC and local),
                                         HTTP status, response headers (Date, Last-Modified, ETag), file name,
                                         bytes, MD5, n_obs, first/last observation, PC name, Python version
  panel_levels_<YYYYMMDD>.csv            long panel from the Q661S pairs: country, date, cons_idx, gdp_idx, lcy
                                         (lcy = ln(cons_idx / gdp_idx); NOT rebased, NOT spliced for Japan)
  fetch_summary_<YYYYMMDD>.txt           counts of OK / failed series (read this first)

Series groups
  Q661S      NAEXKP02{CC}Q661S (private consumption), NAEXKP01{CC}Q661S (GDP): the panel used in the
             Japan/UK papers according to the UK README (to be confirmed by the comparison below).
  IFS_CHECK  NCPRSAXDC{CC}Q / NGDPRSAXDC{CC}Q (IMF IFS): listed in the Japan replication package README;
             downloaded only so that the two sources can be compared (use --no-ifs to skip).
"""
import argparse
import csv
import hashlib
import math
import os
import platform
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

COUNTRIES = ['AT', 'AU', 'BE', 'CA', 'CH', 'CL', 'CO', 'CZ', 'DE', 'DK', 'EE', 'ES', 'FI', 'FR',
             'GB', 'GR', 'HU', 'IE', 'IL', 'IS', 'IT', 'JP', 'KR', 'LT', 'LU', 'LV', 'MX', 'NL',
             'NO', 'NZ', 'PL', 'PT', 'SE', 'SI', 'SK', 'TR', 'US']
IFS_COUNTRIES = ['JP', 'DE', 'GB', 'CA', 'AU', 'US', 'KR', 'IT', 'FR', 'MX', 'TR']
URL = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id={}'
HEADERS_KEEP = ('Date', 'Last-Modified', 'ETag', 'Content-Length')


def fetch_bytes(series_id, tries=3, pause=2.0):
    """Return (status, body_bytes_or_None, headers_dict)."""
    req = urllib.request.Request(URL.format(series_id),
                                 headers={'User-Agent': 'Mozilla/5.0 (research data download)'})
    status = 'ERROR'
    for k in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
                hdr = {h: r.headers.get(h, '') for h in HEADERS_KEEP}
                return 'HTTP %s' % r.status, body, hdr
        except urllib.error.HTTPError as e:
            status = 'HTTP %s' % e.code
            if e.code in (404, 400):          # series does not exist: do not retry
                return status, None, {}
        except Exception as e:                # timeout, DNS, etc.
            status = 'ERROR %s' % type(e).__name__
        time.sleep(pause * (k + 1))
    return status, None, {}


def parse_obs(body):
    """Parse FRED CSV bytes -> list of (date_str, float). Skips '.' / blank values."""
    text = body.decode('utf-8', errors='replace').lstrip('﻿')
    rows = list(csv.reader(text.splitlines()))
    out = []
    for row in rows[1:]:
        if len(row) < 2:
            continue
        v = row[1].strip()
        if v in ('', '.'):
            continue
        try:
            out.append((row[0], float(v)))
        except ValueError:
            continue
    return out


def build_jobs(use_ifs):
    jobs = []
    for c in COUNTRIES:
        jobs.append((c, 'cons', 'Q661S', 'NAEXKP02%sQ661S' % c))
        jobs.append((c, 'gdp', 'Q661S', 'NAEXKP01%sQ661S' % c))
    if use_ifs:
        for c in IFS_COUNTRIES:
            jobs.append((c, 'cons', 'IFS_CHECK', 'NCPRSAXDC%sQ' % c))
            jobs.append((c, 'gdp', 'IFS_CHECK', 'NGDPRSAXDC%sQ' % c))
    return jobs


def run(outdir, stamp, use_ifs=True, fetcher=fetch_bytes, sleep=0.4, verbose=True):
    raw_dir = os.path.join(outdir, 'raw_fred_%s' % stamp)
    os.makedirs(raw_dir, exist_ok=True)
    pc = socket.gethostname()
    pyv = platform.python_version()
    plat = platform.platform()
    jobs = build_jobs(use_ifs)
    log_path = os.path.join(outdir, 'fred_download_log_%s.csv' % stamp)
    data = {}      # (group, country, kind) -> {date: value}
    n_ok = n_fail = 0
    with open(log_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['group', 'country', 'kind', 'series_id', 'url', 'retrieved_utc', 'retrieved_local',
                    'status', 'hdr_date', 'hdr_last_modified', 'hdr_etag', 'file', 'bytes', 'md5',
                    'n_obs', 'first_obs', 'last_obs', 'pc', 'python', 'platform'])
        for i, (c, kind, group, sid) in enumerate(jobs, 1):
            t_utc = datetime.now(timezone.utc)
            status, body, hdr = fetcher(sid)
            t_loc = t_utc.astimezone()
            fname = md5 = ''
            nbytes = n = 0
            first = last = ''
            if body is not None:
                fname = '%s.csv' % sid
                with open(os.path.join(raw_dir, fname), 'wb') as g:
                    g.write(body)
                md5 = hashlib.md5(body).hexdigest()
                nbytes = len(body)
                obs = parse_obs(body)
                n = len(obs)
                if n:
                    first, last = obs[0][0], obs[-1][0]
                    data[(group, c, kind)] = dict(obs)
                    status = 'OK'
                else:
                    status = 'NO DATA'
            ok = status == 'OK'
            n_ok += ok
            n_fail += (not ok)
            w.writerow([group, c, kind, sid, URL.format(sid), t_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        t_loc.strftime('%Y-%m-%dT%H:%M:%S%z'), status, hdr.get('Date', ''),
                        hdr.get('Last-Modified', ''), hdr.get('ETag', ''), fname, nbytes, md5, n,
                        first, last, pc, pyv, plat])
            f.flush()
            if verbose:
                print('%3d/%d %-18s %-9s %s %s n=%d' % (i, len(jobs), sid, status, first, last, n))
            time.sleep(sleep)

    # long panel from the Q661S pairs (levels as downloaded; lcy not rebased, Japan not spliced)
    panel_path = os.path.join(outdir, 'panel_levels_%s.csv' % stamp)
    n_rows = 0
    with open(panel_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['country', 'date', 'cons_idx', 'gdp_idx', 'lcy'])
        for c in COUNTRIES:
            cons = data.get(('Q661S', c, 'cons'))
            gdp = data.get(('Q661S', c, 'gdp'))
            if not cons or not gdp:
                continue
            for d in sorted(set(cons) & set(gdp)):
                a, b = cons[d], gdp[d]
                if a > 0 and b > 0:
                    w.writerow([c, d, repr(a), repr(b), repr(math.log(a / b))])
                    n_rows += 1

    summ_path = os.path.join(outdir, 'fetch_summary_%s.txt' % stamp)
    with open(summ_path, 'w', encoding='utf-8') as f:
        f.write('series OK: %d, not OK: %d (of %d)\nPC: %s\nPython: %s\nplatform: %s\npanel rows: %d\n'
                % (n_ok, n_fail, len(jobs), pc, pyv, plat, n_rows))
        f.write('not OK:\n')
        for (c, kind, group, sid) in jobs:
            if (group, c, kind) not in data:
                f.write('  %s\n' % sid)
    return dict(ok=n_ok, fail=n_fail, panel_rows=n_rows, log=log_path, panel=panel_path, summary=summ_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-ifs', action='store_true', help='skip the IMF IFS comparison series')
    ap.add_argument('--stamp', default=None, help='date stamp YYYYMMDD (default: today, local time)')
    a = ap.parse_args()
    stamp = a.stamp or datetime.now().strftime('%Y%m%d')
    outdir = os.path.dirname(os.path.abspath(__file__))
    res = run(outdir, stamp, use_ifs=not a.no_ifs)
    print('\nOK %d / not OK %d; panel rows %d' % (res['ok'], res['fail'], res['panel_rows']))
    print('log:', res['log'])
    print('summary:', res['summary'])


if __name__ == '__main__':
    sys.exit(main())
