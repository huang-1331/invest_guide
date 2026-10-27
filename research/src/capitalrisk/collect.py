"""Collect financial accounts for an externally verified historical listing universe."""
import hashlib
import json
import re
import pandas as pd
from .io import ROOT, Dart, audit

# Restrict to nonfinancial, December-year-end ordinary-share issuers.
# No name-based guessing of ambiguous company-specific account extensions.
ACCOUNTS = {
    'assets': ('ifrs-full_Assets', 'BS'),
    'liabilities': ('ifrs-full_Liabilities', 'BS'),
    'equity': ('ifrs-full_Equity', 'BS'),
    'capital': ('ifrs-full_IssuedCapital', 'BS'),
    'current_assets': ('ifrs-full_CurrentAssets', 'BS'),
    'current_liabilities': ('ifrs-full_CurrentLiabilities', 'BS'),
    'retained_earnings': ('ifrs-full_RetainedEarnings', 'BS'),
    'revenue': ('ifrs-full_Revenue', 'IS'),
    'operating_income': ('dart_OperatingIncomeLoss', 'IS'),
    'net_income': ('ifrs-full_ProfitLoss', 'IS'),
    'ocf': ('ifrs-full_CashFlowsFromUsedInOperatingActivities', 'CF'),
    # EBIT is deliberately separate from operating profit; do not silently substitute.
    'ebit': ('ifrs-full_ProfitLossFromOperatingActivities', 'IS'),
}
REPORTS = {'11013': 1, '11012': 2, '11014': 3, '11011': 4}


def amount(value):
    if value in (None, '', '-'):
        return None
    try:
        x = float(str(value).replace(',', ''))
        return x if pd.notna(x) and abs(x) != float('inf') else None
    except ValueError:
        return None


def normalize(accounts, company, year, report, basis, filings):
    receipts = {a.get('rcept_no') for a in accounts}
    if len(receipts) != 1 or None in receipts:
        raise ValueError('ambiguous receipt')
    receipt = receipts.pop()
    matches = [f for f in filings if f.get('rcept_no') == receipt]
    if len(matches) != 1:
        raise ValueError('exact filing receipt/date unavailable')
    filed = pd.to_datetime(matches[0]['rcept_dt'], format='%Y%m%d')
    quarter = REPORTS[report]
    period = pd.Timestamp(year=int(year), month=quarter * 3, day=1) + pd.offsets.MonthEnd(0)
    row = dict(corp_code=company.corp_code, stock_code=company.stock_code,
               company_name=company.company_name, period_end=str(period.date()),
               filed_at=str(filed.date()), rcept_no=receipt, fs_div=basis, currency='KRW',
               unit='KRW', source='OpenDART', source_url='https://dart.fss.or.kr/dsaf001/main.do?rcpNo='+receipt,
               vintage_verified=True, fiscal_year_end=12, report_code=report,
               # Latest API snapshots can be delayed corrections, never backdated.
               vintage_policy='exact_returned_receipt_only', values_are_ytd=True)
    for name, (account_id, section) in ACCOUNTS.items():
        candidates = [a for a in accounts if a.get('account_id') == account_id and
                      a.get('sj_div') in ({'IS', 'CIS'} if section == 'IS' else {section})]
        # Prefer IS to CIS; duplicated same-section accounts remain missing.
        if section == 'IS' and any(a.get('sj_div') == 'IS' for a in candidates):
            candidates = [a for a in candidates if a.get('sj_div') == 'IS']
        if len(candidates) != 1 or candidates[0].get('currency') != 'KRW':
            row[name] = None
            audit('OpenDART', 'account', 'missing_or_ambiguous', name, corp_code=company.corp_code,
                  rcept_no=receipt, candidates=len(candidates))
        else:
            a = candidates[0]
            field = 'thstrm_amount'
            if section == 'IS' and quarter != 4:
                field = 'thstrm_add_amount'
            row[name] = amount(a.get(field))
    if period >= filed:
        raise ValueError('filing does not follow accounting period')
    return row


def load_universe(path):
    u = pd.read_csv(path, dtype={'corp_code':str, 'stock_code':str})
    required = ['corp_code','stock_code','company_name','listed_at','delisted_at',
                'history_source_url','history_verified','fiscal_year_end','sector_class',
                'followup_end','followup_verified','universe_complete']
    if set(required) - set(u):
        raise ValueError('missing universe columns: '+str(sorted(set(required)-set(u))))
    if u.empty:
        raise ValueError('historical universe is empty')
    if u.corp_code.duplicated().any():
        raise ValueError('duplicate issuer: consolidate listing spells manually; do not guess')
    for col in ['history_verified','followup_verified','universe_complete']:
        if not u[col].astype(str).str.lower().isin(['true','1']).all():
            raise ValueError(col+' must be independently verified for every issuer')
    if not u.corp_code.str.fullmatch(r'\d{8}').all():
        raise ValueError('invalid corp_code')
    if not u.history_source_url.str.match(r'https://(kind\.krx\.co\.kr|data\.krx\.co\.kr)/').all():
        raise ValueError('historical listing provenance must be official KRX/KIND')
    if not (u.fiscal_year_end == 12).all() or not u.sector_class.eq('nonfinancial').all():
        raise ValueError('initial protocol supports December nonfinancial issuers only')
    for c in ['listed_at', 'followup_end']:
        u[c] = pd.to_datetime(u[c], errors='raise')
    u['delisted_at'] = pd.to_datetime(u.delisted_at, errors='raise')
    return u


def collect(universe_path, config):
    u = load_universe(universe_path)
    dart, rows = Dart(), []
    for company in u.itertuples():
        try:
            filings = dart.filings(company.corp_code, str(config['start_year'])+'0101',
                                   str(config['end_year']+2)+'1231')
        except RuntimeError:
            continue
        for year in range(config['start_year'], config['end_year']+1):
            for report in REPORTS:
                try:
                    accounts = dart.statements(company.corp_code, year, report, config['basis'])
                    rows.append(normalize(accounts, company, year, report, config['basis'], filings))
                except (ValueError, RuntimeError) as e:
                    audit('OpenDART', 'normalize', 'excluded', str(e), corp_code=company.corp_code,
                          year=year, report=report)
    out = ROOT/'data/private/financials.csv'
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    return out
