"""Command line research runner; blocked data produces status, never fake metrics."""
import argparse
import importlib.metadata
import json
import platform
import traceback
from pathlib import Path
import numpy as np
import pandas as pd
from .io import ROOT,write_json,audit,probe
from .collect import collect,load_universe
from .features import validate_financials,build_landmarks,split,FEATURES,financial_states


def clean(obj):
    if isinstance(obj,dict): return {k:clean(v) for k,v in obj.items()}
    if isinstance(obj,list): return [clean(v) for v in obj]
    if isinstance(obj,(np.integer,)): return int(obj)
    if isinstance(obj,(float,np.floating)): return float(obj) if np.isfinite(obj) else None
    return obj


def run(financials,universe_path,config):
    out=ROOT/'outputs';out.mkdir(exist_ok=True)
    config_hash=__import__('hashlib').sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    status={'status':'blocked','actual_financial_rows':0,'incident_companies':0,'models_evaluated':0,
            'config_sha256':config_hash,'python':platform.python_version(),'limitations':[],
            'scope':'verified historical universe; no resampling of validation/test'}
    # Fresh output folder per run prevents stale results from being mistaken for current results.
    run_dir=out/('run_'+pd.Timestamp.now(tz='UTC').strftime('%Y%m%dT%H%M%S%fZ'))
    run_dir.mkdir()
    status['run_directory']=run_dir.name
    try:
        universe=load_universe(universe_path)
        f=validate_financials(pd.read_csv(financials,dtype={'corp_code':str,'stock_code':str,'rcept_no':str}),config['basis'])
        if set(universe.corp_code)-set(f.corp_code):
            raise ValueError('universe issuers missing financials; natural market prevalence cannot be certified')
        status['actual_financial_rows']=len(f)
        landmarks,events,excluded=build_landmarks(f,universe,config)
        status['incident_companies']=int(events.incident.sum())
        status['landmarks']=len(landmarks)
        private=ROOT/'data/private';private.mkdir(exist_ok=True,parents=True)
        landmarks.drop(columns=['sequence'],errors='ignore').to_csv(private/'landmarks.csv',index=False)
        events.to_csv(private/'events.csv',index=False);excluded.to_csv(run_dir/'exclusions.csv',index=False)
        states=financial_states(f)
        states.to_csv(private/'financial_states.csv',index=False)
        states.groupby('state').size().rename('rows').to_csv(run_dir/'state_counts.csv')
        f.select_dtypes(include='number').isna().mean().rename('missing_fraction').to_csv(run_dir/'missingness.csv')
        if status['incident_companies']<config['minimum_event_companies']:
            status['limitations'].append('Fewer than 20 incident companies: exploratory pilot only')
        from .plots import exploratory,performance,shap_plot
        from .models import model_suite
        from .evaluate import metrics,choose_threshold,cluster_bootstrap,survival_metrics
        figures=run_dir/'figures'
        status['figures']=exploratory(f,landmarks,events,figures)
        all_metrics=[]
        for h in config['horizons']:
            tr,va,te=split(landmarks,config,h)
            split_report={name:{'rows':len(x),'companies':x.corp_code.nunique(),'events':int(x[f'y_{h}'].sum()),
                          'event_prevalence':float(x[f'y_{h}'].mean()) if len(x) else None}
                          for name,x in [('train',tr),('validation',va),('test',te)]}
            write_json(run_dir/f'split_{h}.json',split_report)
            # Fixed Altman and old-style logit receive no arbitrary zero replacements.
            old=['log_current_liabilities_equity','roe'] if h==12 else ['equity_growth','log_current_ratio']
            common=['altman_z']+old
            before={name:len(x) for name,x in [('train',tr),('validation',va),('test',te)]}
            tr,va,te=[x.dropna(subset=common).copy() for x in [tr,va,te]]
            write_json(run_dir/f'common_coverage_{h}.json',{'before':before,'after':dict(zip(before,map(len,[tr,va,te]))),
                       'limitation':'Common complete-case subset may alter natural market event prevalence; market-level validation pending'})
            # Do not claim market prevalence when outcome-related missingness changes the cohort.
            if any(len(x)!=before[k] for k,x in [('train',tr),('validation',va),('test',te)]):
                status['limitations'].append(f'{h}m common model cohort excludes missing baseline inputs; population prevalence not preserved')
            if len(te)!=before['test']:
                status['limitations'].append(f'{h}m comparison blocked: baseline missingness would alter test prevalence')
                continue
            if any(len(x)==0 or x[f'y_{h}'].nunique()<2 for x in [tr,va,te]):
                status['limitations'].append(f'{h}m: each split needs observed positive and negative outcomes')
                continue
            # Administrative survival censoring at training closure avoids future outcomes.
            survival_train=tr.copy()
            closure=pd.Timestamp(config['validation_start'])-pd.Timedelta(days=1)
            maxduration=(closure-survival_train.anchor).dt.days
            future=(survival_train.label_available_at>closure)|(survival_train.duration_days>maxduration)
            survival_train.loc[future,'event_observed']=0
            survival_train['duration_days']=np.minimum(survival_train.duration_days,maxduration)
            # Censor at the latest publicly confirmed period, not an undisclosed event.
            for idx in survival_train.index[future]:
                row=survival_train.loc[idx]
                known=f[(f.corp_code==row.corp_code)&(f.filed_at<=closure)&f.equity.notna()]
                confirmed=known.period_end.max() if len(known) else row.anchor
                survival_train.loc[idx,'duration_days']=min(survival_train.loc[idx,'duration_days'],max(0,(confirmed-row.anchor).days))
            survival_train=survival_train[survival_train.duration_days>0]
            models=model_suite(h,config['seed']);predictions=[];summaries=[];intervals={};fitted={}
            for name,model in models.items():
                try:
                    model.fit(survival_train if name=='Cox' else tr,tr[f'y_{h}'].astype(int))
                    raw_val,raw_test=model.predict(va),model.predict(te)
                    threshold=choose_threshold(va[f'y_{h}'],raw_val)
                    m=dict(model=name,horizon=h,threshold=threshold,**metrics(te[f'y_{h}'],raw_test,threshold))
                    # A separate Platt mapper is fitted on validation only; test is untouched.
                    from sklearn.linear_model import LogisticRegression
                    transform=lambda p:np.log(np.clip(p,1e-6,1-1e-6)/(1-np.clip(p,1e-6,1-1e-6))).reshape(-1,1)
                    calibrator=LogisticRegression(C=1).fit(transform(raw_val),va[f'y_{h}'].astype(int))
                    calibrated=calibrator.predict_proba(transform(raw_test))[:,1]
                    m['brier_calibrated']=metrics(te[f'y_{h}'],calibrated)['brier']
                    if name=='Altman_Zpp':
                        m['fixed_cutoff_f1']=metrics(te[f'y_{h}'],(te.altman_z<1.10).astype(float))['f1']
                    pred=te[['corp_code','anchor']].copy();pred['y']=te[f'y_{h}'].astype(int)
                    pred['probability']=raw_test;pred['calibrated_probability']=calibrated;pred['model']=name
                    pred['predicted']=(raw_test>=threshold).astype(int)
                    predictions.append(pred);summaries.append(m);fitted[name]=model
                    intervals[name]=cluster_bootstrap(te[f'y_{h}'],raw_test,te.corp_code,threshold,
                        repetitions=config['bootstrap_repetitions'],seed=config['seed'])
                    if name=='Cox':
                        subjects=te.sort_values('anchor').drop_duplicates('corp_code')
                        train_subjects=survival_train.sort_values('anchor').drop_duplicates('corp_code',keep='last')
                        write_json(run_dir/f'survival_{h}.json',clean(survival_metrics(train_subjects,subjects,
                                   model.risk(subjects),h*365.25/12)))
                except Exception as e:
                    audit('model',name,'failed',type(e).__name__+': '+str(e)[:250],horizon=h)
                    status['limitations'].append(f'{h}m {name}: {type(e).__name__}: {str(e)[:120]}')
            if not predictions:
                continue
            pred=pd.concat(predictions);results=pd.DataFrame(summaries)
            pred.to_csv(private/f'predictions_{h}.csv',index=False)
            results.to_csv(run_dir/f'metrics_{h}.csv',index=False)
            baseline=next((p for p in predictions if p.model.iloc[0]=='Altman_Zpp'),None)
            if baseline is not None:
                base_summary=next(m for m in summaries if m['model']=='Altman_Zpp')
                diffs=[]
                for p,m in zip(predictions,summaries):
                    diffs.append(dict(model=m['model'],horizon=h,**{k:m[k]-base_summary[k]
                        for k in ['accuracy','precision','recall','f1','roc_auc','pr_auc','brier','false_alarm_rate']}))
                    intervals[m['model']]['paired_difference_vs_altman']=cluster_bootstrap(p.y,p.probability,p.corp_code,
                        m['threshold'],baseline.probability.to_numpy(),base_summary['threshold'],
                        repetitions=config['bootstrap_repetitions'],seed=config['seed'])
                pd.DataFrame(diffs).to_csv(run_dir/f'difference_vs_altman_{h}.csv',index=False)
            write_json(run_dir/f'confidence_intervals_{h}.json',clean(intervals))
            performance(pred,results,figures,h)
            if 'XGBoost' in fitted:
                try: shap_plot(fitted['XGBoost'],te,figures,h)
                except Exception as e: status['limitations'].append('SHAP unavailable: '+type(e).__name__)
            all_metrics.extend(summaries)
        status['models_evaluated']=len(all_metrics)
        status['status']='pilot_completed' if all_metrics else 'data_available_evaluation_blocked'
    except (OSError,ValueError,KeyError) as e:
        status['limitations'].append(type(e).__name__+': '+str(e))
    write_json(run_dir/'status.json',clean(status));write_json(out/'status.json',clean(status))
    return status


def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['probe','collect','run'])
    p.add_argument('--config',default=str(ROOT/'config.json'))
    p.add_argument('--universe',default=str(ROOT/'data/private/universe.csv'))
    p.add_argument('--financials',default=str(ROOT/'data/private/financials.csv'))
    args=p.parse_args();cfg=json.loads(Path(args.config).read_text())
    if args.command=='probe': probe()
    elif args.command=='collect': collect(args.universe,cfg)
    else: print(json.dumps(run(args.financials,args.universe,cfg),ensure_ascii=False,indent=2))

if __name__=='__main__': main()
