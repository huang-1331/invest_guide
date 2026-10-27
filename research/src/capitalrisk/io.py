"""Bounded, credential-safe public data access and audit trail."""
import csv
import hashlib
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def audit(source, operation, status, detail='', **metadata):
    path = ROOT / 'outputs/collection_audit.csv'
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ['time_utc', 'source', 'operation', 'status', 'detail', 'metadata']
    with path.open('a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(dict(time_utc=datetime.now(timezone.utc).isoformat(), source=source,
                             operation=operation, status=status, detail=detail,
                             metadata=json.dumps(metadata, ensure_ascii=False)))


def download(url, params=None, timeout=12):
    # Never log the request URL: DART credentials are query parameters.
    request = Request(url + ('?' + urlencode(params) if params else ''),
                      headers={'User-Agent': 'capitalrisk-research/0.1'})
    try:
        with urlopen(request, timeout=timeout) as r:
            return r.read()
    except Exception as e:
        raise RuntimeError(type(e).__name__) from None


class Dart:
    def __init__(self):
        self.key = os.environ.get('OPENDART_API_KEY')
        if not self.key:
            audit('OpenDART', 'authentication', 'blocked', 'OPENDART_API_KEY not set')
            raise RuntimeError('OPENDART_API_KEY not set')

    def get(self, endpoint, **params):
        try:
            raw = download('https://opendart.fss.or.kr/api/' + endpoint,
                           dict(params, crtfc_key=self.key))
            if endpoint.endswith('.json'):
                obj = json.loads(raw)
                status = obj.get('status')
                if status != '000':
                    audit('OpenDART', endpoint, 'api_' + str(status), **params)
                    raise RuntimeError('DART status ' + str(status))
            else:
                obj = raw
            # Local raw cache is excluded from Git. Request parameters have no key.
            tag = hashlib.sha256(json.dumps([endpoint, params], sort_keys=True).encode()).hexdigest()
            path = ROOT / 'data/raw' / (tag + '.bin')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            audit('OpenDART', endpoint, 'ok', sha256=hashlib.sha256(raw).hexdigest(), **params)
            return obj
        except RuntimeError as e:
            audit('OpenDART', endpoint, 'error', str(e), **params)
            raise

    def filings(self, corp_code, start, end):
        rows, page = [], 1
        while True:
            obj = self.get('list.json', corp_code=corp_code, bgn_de=start, end_de=end,
                           pblntf_ty='A', last_reprt_at='N', page_count=100, page_no=page)
            rows.extend(obj['list'])
            if page >= int(obj.get('total_page', 1)):
                return rows
            page += 1

    def statements(self, corp_code, year, report, basis):
        return self.get('fnlttSinglAcntAll.json', corp_code=corp_code, bsns_year=year,
                        reprt_code=report, fs_div=basis)['list']


def probe():
    targets = {
        'OpenDART': 'https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json',
        'KIND_listing': 'https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13',
        'KIND_delisting': 'https://kind.krx.co.kr/investwarn/delcompany.do?method=searchDelCompanyMain',
        'KRX': 'https://data.krx.co.kr/comm/finder/finder_datastkisu.jsp',
    }
    for name, url in targets.items():
        try:
            raw = download(url, timeout=6)
            path = ROOT / 'data/raw' / (name + '.bin')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            audit(name, 'network_probe', 'reachable', bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        except RuntimeError as e:
            audit(name, 'network_probe', 'blocked', str(e))
    if not os.getenv('OPENDART_API_KEY'):
        audit('OpenDART', 'authentication', 'blocked', 'OPENDART_API_KEY not set; no credential reused')
