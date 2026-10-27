"""Held-out metrics, company-cluster bootstrap and paired baseline differences."""
import numpy as np
from sklearn.metrics import (accuracy_score,precision_score,recall_score,f1_score,roc_auc_score,
                            average_precision_score,brier_score_loss,confusion_matrix)


def metrics(y,p,threshold=.5):
    y=np.asarray(y,int);p=np.asarray(p,float)
    pred=p>=threshold
    tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    return dict(accuracy=accuracy_score(y,pred),precision=precision_score(y,pred,zero_division=0),
                recall=recall_score(y,pred,zero_division=0),f1=f1_score(y,pred,zero_division=0),
                roc_auc=roc_auc_score(y,p) if len(np.unique(y))==2 else np.nan,
                pr_auc=average_precision_score(y,p) if len(np.unique(y))==2 else np.nan,
                brier=brier_score_loss(y,p),false_alarm_rate=fp/(tn+fp) if tn+fp else np.nan,
                tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp),n=len(y),events=int(sum(y)))


def choose_threshold(y,p):
    # Validation-only threshold selection, used unchanged on test.
    candidates=np.unique(np.r_[0,.5,1,p])
    return float(max(candidates,key=lambda t:(f1_score(y,p>=t,zero_division=0),t)))


def cluster_bootstrap(y,p,companies,threshold,baseline=None,baseline_threshold=.5,repetitions=1000,seed=42):
    rng=np.random.default_rng(seed);companies=np.asarray(companies);unique=np.unique(companies)
    draws=[]
    for _ in range(repetitions):
        sampled=rng.choice(unique,len(unique),replace=True)
        indices=np.concatenate([np.flatnonzero(companies==c) for c in sampled])
        m=metrics(np.asarray(y)[indices],np.asarray(p)[indices],threshold)
        if baseline is not None:
            b=metrics(np.asarray(y)[indices],np.asarray(baseline)[indices],baseline_threshold)
            m={k:m[k]-b[k] for k in ['accuracy','precision','recall','f1','roc_auc','pr_auc','brier','false_alarm_rate']}
        draws.append(m)
    result={}
    for key in ['accuracy','precision','recall','f1','roc_auc','pr_auc','brier','false_alarm_rate']:
        v=np.array([x[key] for x in draws],float);v=v[np.isfinite(v)]
        result[key]={'low':float(np.quantile(v,.025)) if len(v) else None,
                     'high':float(np.quantile(v,.975)) if len(v) else None,'valid_draws':len(v)}
    return result


def survival_metrics(train,test,risk,horizon_days):
    from sksurv.metrics import concordance_index_censored,cumulative_dynamic_auc
    from sksurv.util import Surv
    # One held-out landmark per issuer; caller provides the same selection for risk.
    ytr=Surv.from_arrays(train.event_observed.astype(bool),train.duration_days.astype(float))
    yte=Surv.from_arrays(test.event_observed.astype(bool),test.duration_days.astype(float))
    result={}
    try:
        result['c_index']=float(concordance_index_censored(yte['event'],yte['time'],risk)[0])
    except ValueError as e:
        result['c_index']=None;result['c_index_unavailable_reason']=str(e)
    try:
        auc,_=cumulative_dynamic_auc(ytr,yte,risk,[horizon_days])
        result['time_dependent_auc']=float(auc[0])
    except ValueError as e:
        result['time_dependent_auc']=None;result['time_auc_unavailable_reason']=str(e)
    return result
