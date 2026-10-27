"""Point-in-time snapshots, first observed events and censor-aware labels."""
import hashlib
import numpy as np
import pandas as pd
from .collect import ACCOUNTS

BASE_FEATURES = ['impairment','debt_assets','roa','current_ratio','ocf_assets',
                 'operating_margin','loss_streak','altman_z','equity_growth',
                 'log_current_ratio','log_current_liabilities_equity','roe']
SEQUENCE_FEATURES = ['impairment','debt_assets','roa','current_ratio','ocf_assets','operating_margin']
FEATURES = BASE_FEATURES + [f'{x}_{kind}{lag}' for x in SEQUENCE_FEATURES
                            for lag in [4,8] for kind in ['delta','growth']]


def ratio(a,b):
    return a/b if pd.notna(a) and pd.notna(b) and b > 0 else np.nan


def validate_financials(frame, basis):
    f = frame.copy()
    required = {'corp_code','period_end','filed_at','rcept_no','fs_div','currency','unit',
                'source_url','source','vintage_verified','fiscal_year_end','values_are_ytd', *ACCOUNTS}
    if required - set(f):
        raise ValueError('missing financial columns: '+str(sorted(required-set(f))))
    if f.empty:
        raise ValueError('no verified financial rows')
    for c in ['period_end','filed_at']:
        f[c] = pd.to_datetime(f[c], errors='raise')
    if not f.vintage_verified.astype(str).str.lower().isin(['true','1']).all():
        raise ValueError('unverified historical vintage')
    if not f.values_are_ytd.astype(str).str.lower().isin(['true','1']).all():
        raise ValueError('flow columns must be fiscal YTD')
    if not f.fs_div.eq(basis).all() or not f.currency.eq('KRW').all() or not f.unit.eq('KRW').all():
        raise ValueError('mixed statement basis/currency/unit')
    if not f.fiscal_year_end.eq(12).all() or not (f.filed_at > f.period_end).all():
        raise ValueError('invalid fiscal period or disclosure date')
    if not f.source.eq('OpenDART').all() or not f.source_url.str.startswith('https://dart.fss.or.kr/').all():
        raise ValueError('unverified source')
    keys = ['corp_code','period_end','filed_at']
    if f.duplicated(keys, keep=False).any():
        raise ValueError('ambiguous same-day duplicate disclosures; resolve explicitly')
    for c in ACCOUNTS:
        f[c] = pd.to_numeric(f[c], errors='raise').replace([np.inf,-np.inf],np.nan)
    valid = f[['assets','liabilities','equity']].notna().all(axis=1)
    inconsistent = (f.assets-f.liabilities-f.equity).abs() > np.maximum(1, f.assets.abs()*0.001)
    if (valid & inconsistent).any():
        raise ValueError('balance sheet identity mismatch')
    f['quarter'] = f.period_end.dt.to_period('Q')
    if not (f.period_end.dt.is_quarter_end).all():
        raise ValueError('non-quarter-end accounting period')
    return f.sort_values(['corp_code','filed_at','period_end'])


def series_at(g, anchor):
    # Resolve revisions independently for each prediction date.
    s = g[g.filed_at <= anchor].sort_values(['filed_at','period_end']).drop_duplicates('quarter',keep='last')
    s = s.set_index('quarter').sort_index()
    if s.empty:
        return s
    s = s.reindex(pd.period_range(s.index.min(),s.index.max(),freq='Q'))
    for flow in ['net_income','operating_income','revenue','ocf','ebit']:
        ytd = s[flow]
        q = ytd-ytd.shift(1)
        q.loc[q.index.quarter == 1] = ytd.loc[ytd.index.quarter == 1]
        s[flow+'_q'] = q
        s[flow+'_ttm'] = q.rolling(4,min_periods=4).sum()
    a = s.assets.where(s.assets > 0)
    s['impairment'] = (s.capital-s.equity)/s.capital.where(s.capital>0)
    s['debt_assets'] = s.liabilities.where(s.liabilities>=0)/a
    s['roa'] = s.net_income_ttm/a
    s['current_ratio'] = s.current_assets/s.current_liabilities.where(s.current_liabilities>0)
    s['ocf_assets'] = s.ocf_ttm/a
    s['operating_margin'] = s.operating_income_ttm/s.revenue_ttm.where(s.revenue_ttm>0)
    s['roe'] = s.net_income_ttm/s.equity.where(s.equity>0)
    s['equity_growth'] = (s.equity-s.equity.shift(4))/s.equity.shift(4).abs().where(s.equity.shift(4)!=0)
    s['log_current_ratio'] = np.log(s.current_ratio.where(s.current_ratio>0))
    cl = s.current_liabilities/s.equity.where(s.equity>0)
    s['log_current_liabilities_equity'] = np.log(cl.where(cl>0))
    s['altman_z'] = (6.56*(s.current_assets-s.current_liabilities)/a + 3.26*s.retained_earnings/a
                     + 6.72*s.ebit_ttm/a + 1.05*s.equity/s.liabilities.where(s.liabilities>0))
    streak, values = 0, []
    for v in s.net_income_q:
        streak = streak+1 if pd.notna(v) and v<0 else 0
        values.append(streak if pd.notna(v) else np.nan)
    s['loss_streak'] = values
    for col in SEQUENCE_FEATURES:
        for lag in [4,8]:
            prev = s[col].shift(lag)
            s[f'{col}_delta{lag}'] = s[col]-prev
            s[f'{col}_growth{lag}'] = (s[col]-prev)/prev.abs().where(prev!=0)
    return s.replace([np.inf,-np.inf],np.nan)


def first_events(f):
    rows=[]
    for corp,g in f.groupby('corp_code'):
        # Initial nonpositive equity is left censored, not an incident event.
        initial = g.sort_values(['period_end','filed_at']).iloc[0]
        negative = g[g.equity<=0].sort_values(['period_end','filed_at'])
        event = negative.iloc[0] if len(negative) else None
        incident = (initial.equity>0 and event is not None and
                    initial.period_end < event.period_end and initial.filed_at < event.filed_at)
        rows.append(dict(corp_code=corp, left_censored=not(initial.equity>0),
                         event_period=event.period_end if event is not None else pd.NaT,
                         event_disclosed=event.filed_at if event is not None else pd.NaT,
                         incident=incident))
    return pd.DataFrame(rows)


def company_partition(corp):
    bucket = int(hashlib.sha256(str(corp).encode()).hexdigest()[:8],16)%10
    return 'train' if bucket<6 else ('validation' if bucket<8 else 'test')


def build_landmarks(f, universe, config):
    events = first_events(f)
    rows, excluded = [], []
    meta = universe.set_index('corp_code')
    for corp,g in f.groupby('corp_code'):
        if corp not in meta.index:
            raise ValueError('financial issuer absent from historical universe')
        u = meta.loc[corp]
        e = events.set_index('corp_code').loc[corp]
        if e.left_censored:
            excluded.append(dict(corp_code=corp,reason='left_censored_or_missing_initial_equity'))
            continue
        for anchor in sorted(g.filed_at.unique()):
            anchor = pd.Timestamp(anchor)
            s = series_at(g,anchor)
            r = s.iloc[-1]
            if pd.isna(r.equity) or r.equity<=0:
                continue
            # Financial onset is the period end, not the later disclosure.
            if pd.notna(e.event_period) and anchor>=e.event_period:
                continue
            if anchor<u.listed_at or (pd.notna(u.delisted_at) and anchor>=u.delisted_at):
                continue
            if (anchor-r.period_end).days>config['max_statement_age_days']:
                excluded.append(dict(corp_code=corp,reason='stale_statement',anchor=str(anchor.date())))
                continue
            if len(s)<8 or s.tail(8).equity.isna().any():
                continue
            row = dict(corp_code=corp,anchor=anchor,period_end=r.period_end,
                       available_at=s.filed_at.max(),partition=company_partition(corp),
                       event_period=e.event_period,delisted_at=u.delisted_at,
                       followup_end=u.followup_end, **{c:r[c] for c in FEATURES})
            followup = min(u.followup_end, u.delisted_at) if pd.notna(u.delisted_at) else u.followup_end
            event = e.event_period
            # Missing intervening quarters censor the endpoint at last continuous observation.
            original = g.sort_values('filed_at').drop_duplicates('quarter',keep='first').set_index('quarter')
            coverage = r.period_end
            for q in pd.period_range(r.period_end.to_period('Q')+1, followup.to_period('Q'),freq='Q'):
                if q not in original.index or pd.isna(original.loc[q,'equity']):
                    break
                coverage = q.end_time.normalize()
            followup = min(followup,coverage)
            event_seen = pd.notna(event) and anchor<event<=followup
            row['duration_days'] = ((event if event_seen else followup)-anchor).days
            row['event_observed'] = int(event_seen)
            row['label_available_at'] = (e.event_disclosed if event_seen else
                                         g.loc[g.period_end<=followup,'filed_at'].max())
            for h in config['horizons']:
                end = anchor+pd.DateOffset(months=h)
                hit = event_seen and event<=end
                observed = hit or followup>=end
                row[f'y_{h}'] = int(hit) if observed else np.nan
                # Delisting is an independent endpoint, not used as insolvency proxy.
                row[f'delisted_{h}'] = (int(anchor<u.delisted_at<=end) if pd.notna(u.delisted_at)
                                       else (0 if u.followup_end>=end else np.nan))
                relevant = g[g.period_end>=end].sort_values(['period_end','filed_at'])
                confirmation = relevant.iloc[0].filed_at if len(relevant) else pd.NaT
                row[f'label_available_{h}'] = (e.event_disclosed if hit else
                    confirmation if observed else pd.NaT)
            seq = s.tail(config['sequence_quarters'])[SEQUENCE_FEATURES].to_numpy(float)
            row['sequence'] = seq.tolist()
            if row['duration_days']>0:
                rows.append(row)
    return pd.DataFrame(rows), events, pd.DataFrame(excluded,columns=['corp_code','reason','anchor'])


def split(frame, config, horizon):
    """Disjoint issuer hash cohorts and nonoverlapping time windows with outcome embargo."""
    if frame.empty:
        raise ValueError('no pre-event landmarks with eight quarters and follow-up')
    d = frame.dropna(subset=[f'y_{horizon}']).copy()
    train_end, val_start, val_end, test_start, test_end = map(pd.Timestamp,
        [config['train_end'],config['validation_start'],config['validation_end'],config['test_start'],config['test_end']])
    if not train_end<val_start<=val_end<test_start<=test_end:
        raise ValueError('invalid chronological split')
    tr = d[(d.partition=='train') & (d.anchor<=train_end) & (d[f'label_available_{horizon}']<val_start)]
    va = d[(d.partition=='validation') & d.anchor.between(val_start,val_end) &
           (d[f'label_available_{horizon}']<test_start)]
    te = d[(d.partition=='test') & d.anchor.between(test_start,test_end)]
    for left,right in [(tr,va),(tr,te),(va,te)]:
        assert not set(left.corp_code)&set(right.corp_code)
    return tr,va,te


def financial_states(f):
    """Descriptive states; never used as a post-event prediction feature."""
    d=f.sort_values(['corp_code','period_end','filed_at']).drop_duplicates(['corp_code','period_end'],keep='first').copy()
    d['state']='unavailable'
    valid=d.equity.notna() & d.capital.gt(0)
    d.loc[valid & d.equity.ge(d.capital),'state']='normal'
    d.loc[valid & d.equity.gt(0) & d.equity.lt(d.capital),'state']='partial_impairment'
    d.loc[d.equity.le(0),'state']='complete_impairment'
    prior=d.groupby('corp_code').equity.transform(lambda s:s.le(0).cummax().shift(fill_value=False))
    d.loc[prior & d.equity.gt(0),'state']='recovered_positive_equity'
    return d
