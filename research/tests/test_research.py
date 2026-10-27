"""Synthetic unit fixtures only. These are never reported as empirical results."""
import json
import numpy as np
import pandas as pd
import pytest
from capitalrisk.features import (validate_financials,series_at,first_events,build_landmarks,
                                  company_partition,split,FEATURES,SEQUENCE_FEATURES)
from capitalrisk.models import model_suite,dtw_distance
from capitalrisk.evaluate import metrics,cluster_bootstrap,survival_metrics
from capitalrisk.collect import normalize,ACCOUNTS


def fixture():
    rows=[]
    for i,q in enumerate(pd.period_range('2015Q1','2025Q4',freq='Q')):
        period=q.end_time.normalize()
        row=dict(corp_code='TEST_ONLY',period_end=period,filed_at=period+pd.Timedelta(days=45),
                 rcept_no=str(i),fs_div='OFS',currency='KRW',unit='KRW',source='OpenDART',
                 source_url='https://dart.fss.or.kr/test-only',vintage_verified=True,
                 fiscal_year_end=12,values_are_ytd=True)
        row.update({x:10. for x in ACCOUNTS})
        row.update(assets=100.,liabilities=60.,equity=40.,capital=50.,current_assets=40.,
                   current_liabilities=20.,net_income=2.*q.quarter,revenue=20.*q.quarter,
                   operating_income=4.*q.quarter,ocf=3.*q.quarter,ebit=5.*q.quarter)
        rows.append(row)
    return validate_financials(pd.DataFrame(rows),'OFS')


def test_future_revision_not_visible():
    f=fixture();revision=f.iloc[[0]].copy();revision['filed_at']=pd.Timestamp('2025-01-01');revision['equity']=30
    g=pd.concat([f,revision])
    early=series_at(g,pd.Timestamp('2016-05-01'))
    late=series_at(g,pd.Timestamp('2025-05-01'))
    assert early.iloc[0].equity==40 and late.iloc[0].equity==30


def test_ytd_quarter_ttm():
    s=series_at(fixture(),pd.Timestamp('2025-12-31'))
    assert s.net_income_q.dropna().eq(2).all()
    assert s.net_income_ttm.dropna().eq(8).all()
    assert np.isclose(s.iloc[-1].altman_z,6.56*.2+3.26*.1+6.72*.2+1.05*40/60)


def test_gaps_not_shifted_as_quarters():
    f=fixture();f=f[f.quarter!=pd.Period('2018Q1')]
    s=series_at(f,pd.Timestamp('2020-01-01'))
    assert pd.isna(s.loc['2018Q1','equity'])
    assert pd.isna(s.loc['2018Q2','net_income_q'])


def test_zero_equity_event_and_left_censoring():
    f=fixture();f.loc[f.quarter==pd.Period('2020Q4'),'equity']=0
    e=first_events(f).iloc[0]
    assert e.incident and e.event_period==pd.Timestamp('2020-12-31')
    f.loc[f.index[0],'equity']=-1
    assert first_events(f).iloc[0].left_censored


def test_no_post_event_landmarks_or_unknown_negative():
    f=fixture();f.loc[f.quarter==pd.Period('2020Q4'),'equity']=0
    universe=pd.DataFrame([dict(corp_code='TEST_ONLY',listed_at=pd.Timestamp('2010-01-01'),
                                delisted_at=pd.NaT,followup_end=pd.Timestamp('2025-12-31'))])
    cfg=dict(horizons=[12,24],sequence_quarters=8,max_statement_age_days=185)
    d,e,_=build_landmarks(f,universe,cfg)
    assert (d.anchor<pd.Timestamp('2020-12-31')).all()
    assert (d.available_at<=d.anchor).all()
    assert (d.loc[d.y_12==1,'event_period']>d.loc[d.y_12==1,'anchor']).all()
    # With no event and short follow-up, future labels remain censored.
    f=fixture();universe['followup_end']=pd.Timestamp('2025-12-31')
    d,_,_=build_landmarks(f,universe,cfg)
    assert pd.isna(d.iloc[-1].y_24)
    negatives=d[d.y_12==0]
    assert (negatives.label_available_12>=negatives.anchor+pd.DateOffset(months=12)).all()


def test_invalid_basis_and_balance_rejected():
    f=fixture();f['fs_div']='CFS'
    with pytest.raises(ValueError,match='mixed'): validate_financials(f,'OFS')
    f=fixture();f.loc[0,'assets']=999
    with pytest.raises(ValueError,match='identity'): validate_financials(f,'OFS')


def test_same_day_duplicates_rejected():
    f=fixture()
    with pytest.raises(ValueError,match='duplicate'): validate_financials(pd.concat([f,f.iloc[[0]]]),'OFS')


def test_partition_and_label_embargo():
    corps={p:next('TEST'+str(i) for i in range(100) if company_partition('TEST'+str(i))==p)
           for p in ['train','validation','test']}
    d=pd.DataFrame([dict(corp_code=corps[p],partition=p,anchor=pd.Timestamp(a),y_12=y,
                         label_available_12=pd.Timestamp(l)) for p,a,y,l in [
        ('train','2018-01-01',0,'2019-02-01'),('train','2018-02-01',1,'2022-01-01'),
        ('validation','2021-01-01',1,'2022-01-01'),('test','2024-01-01',0,'2025-02-01')]])
    cfg=dict(train_end='2018-12-31',validation_start='2021-01-01',validation_end='2021-12-31',
             test_start='2024-01-01',test_end='2025-12-31')
    tr,va,te=split(d,cfg,12)
    assert len(tr)==len(va)==len(te)==1
    assert not set(tr.corp_code)&set(te.corp_code)


def test_dtw_and_metrics():
    a=np.zeros((8,6));b=np.ones((8,6))
    assert dtw_distance(a,a)==0 and dtw_distance(a,b)>0
    m=metrics([0,0,1,1],[.1,.7,.8,.9])
    assert m['fp']==1 and m['false_alarm_rate']==.5
    ci=cluster_bootstrap(np.array([0,0,1,1]),np.array([.1,.7,.8,.9]),np.array(['A','A','B','B']),.5,
                         baseline=np.array([.1,.7,.8,.9]),repetitions=20)
    assert ci['brier']['low']==ci['brier']['high']==0


def model_frame(n,seed):
    rng=np.random.default_rng(seed)
    x=rng.normal(size=(n,len(FEATURES)))
    f=pd.DataFrame(x,columns=FEATURES)
    f['corp_code']=['SYNTHETIC_TEST_'+str(i) for i in range(n)]
    f['anchor']=pd.Timestamp('2010-01-01')
    f['sequence']=[rng.normal(size=(8,len(SEQUENCE_FEATURES))).tolist() for _ in range(n)]
    f['duration_days']=rng.integers(800,2000,size=n)
    f['event_observed']=(f.roa<0).astype(int)
    return f,(f.roa+f.impairment<0).astype(int)


@pytest.mark.parametrize('horizon',[12,24])
def test_all_models_execute_on_synthetic_fixtures(horizon):
    tr,y=model_frame(60,1);te,_=model_frame(12,2)
    for name,model in model_suite(horizon,42).items():
        model.fit(tr,y)
        p=model.predict(te)
        assert p.shape==(12,) and np.isfinite(p).all() and ((p>=0)&(p<=1)).all(),name


def test_no_missing_api_key_reused(monkeypatch):
    from capitalrisk.io import Dart
    monkeypatch.delenv('OPENDART_API_KEY',raising=False)
    monkeypatch.setattr('capitalrisk.io.audit',lambda *a,**k:None)
    with pytest.raises(RuntimeError,match='not set'): Dart()


def test_normalizer_exact_receipt_required():
    from types import SimpleNamespace
    with pytest.raises(ValueError,match='receipt'):
        normalize([{'rcept_no':'20250101000001'}],SimpleNamespace(),2024,'11011','OFS',[])


def test_blocked_run_records_no_fabricated_metrics(tmp_path,monkeypatch):
    import capitalrisk.pipeline as pipeline
    monkeypatch.setattr(pipeline,'ROOT',tmp_path)
    result=pipeline.run(tmp_path/'missing_financials.csv',tmp_path/'missing_universe.csv',{'basis':'OFS'})
    assert result['status']=='blocked' and result['models_evaluated']==0
    assert not list(tmp_path.rglob('metrics_*.csv'))


def test_end_to_end_runner_synthetic_only(tmp_path,monkeypatch):
    import capitalrisk.pipeline as pipeline
    tr,ytr=model_frame(60,11);va,yva=model_frame(20,12);te,yte=model_frame(20,13)
    for frame,y,p,anchor in [(tr,ytr,'train','2017-01-01'),(va,yva,'validation','2021-01-01'),(te,yte,'test','2024-01-01')]:
        frame['corp_code']=p+frame.corp_code
        frame['anchor']=pd.Timestamp(anchor);frame['partition']=p;frame['y_12']=y;frame['y_24']=y
        frame['label_available_at']=pd.Timestamp(anchor)+pd.to_timedelta(frame.duration_days+45,unit='D')
        frame['label_available_12']=pd.Timestamp(anchor)+pd.Timedelta(days=366)
    universe=pd.DataFrame({'corp_code':pd.concat([tr,va,te]).corp_code})
    fake_financials=pd.concat([fixture().assign(corp_code=corp) for corp in universe.corp_code],ignore_index=True)
    monkeypatch.setattr(pipeline,'ROOT',tmp_path)
    monkeypatch.setattr(pipeline,'load_universe',lambda p:universe)
    monkeypatch.setattr(pipeline,'validate_financials',lambda *a:fake_financials)
    events=pd.DataFrame({'corp_code':universe.corp_code,'incident':False})
    monkeypatch.setattr(pipeline,'build_landmarks',lambda *a:(pd.concat([tr,va,te]),events,pd.DataFrame()))
    monkeypatch.setattr(pipeline,'split',lambda *a:(tr.copy(),va.copy(),te.copy()))
    monkeypatch.setattr(pipeline,'audit',lambda *a,**k:None)
    (tmp_path/'input.csv').write_text('corp_code\nSYNTHETIC_ONLY\n')
    config=dict(basis='OFS',horizons=[12],minimum_event_companies=20,seed=42,
                bootstrap_repetitions=3,validation_start='2021-01-01')
    result=pipeline.run(tmp_path/'input.csv',tmp_path/'universe.csv',config)
    assert result['models_evaluated']==6,result
    assert len(list(tmp_path.rglob('metrics_12.csv')))==1
    assert len(list(tmp_path.rglob('08_shap_12.png')))==1,result


def test_recovery_not_relabelled_as_never_failed():
    from capitalrisk.features import financial_states
    f=fixture();f.loc[f.quarter==pd.Period('2020Q4'),'equity']=0
    states=financial_states(f)
    assert states.loc[states.quarter==pd.Period('2020Q4'),'state'].iloc[0]=='complete_impairment'
    assert states.loc[states.quarter==pd.Period('2021Q1'),'state'].iloc[0]=='recovered_positive_equity'
