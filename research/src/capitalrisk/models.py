"""Five model families; preprocessing is fit on training data only."""
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .features import FEATURES, SEQUENCE_FEATURES


def dtw_distance(a,b,band=2):
    n,m=len(a),len(b)
    d=np.full((n+1,m+1),np.inf); d[0,0]=0
    for i in range(1,n+1):
        for j in range(max(1,i-band),min(m,i+band)+1):
            d[i,j]=np.linalg.norm(a[i-1]-b[j-1])+min(d[i-1,j],d[i,j-1],d[i-1,j-1])
    return d[n,m]/(n+m)


class DTWKNN:
    """Multivariate 8-quarter DTW, Sakoe-Chiba radius 2, k=5, distance voting."""
    def fit(self,frame,y):
        self.train=np.asarray(frame.sequence.to_list(),dtype=float)
        self.y=np.asarray(y)
        flat=self.train.reshape(-1,len(SEQUENCE_FEATURES))
        self.imputer=SimpleImputer(strategy='median',keep_empty_features=True).fit(flat)
        self.scale=StandardScaler().fit(self.imputer.transform(flat))
        self.train=self._transform(self.train)
        return self

    def _transform(self,x):
        return self.scale.transform(self.imputer.transform(x.reshape(-1,x.shape[-1]))).reshape(x.shape)

    def predict(self,frame):
        seq=self._transform(np.asarray(frame.sequence.to_list(),dtype=float))
        out=[]
        for x in seq:
            distances=np.array([dtw_distance(x,t) for t in self.train])
            indices=np.argsort(distances,kind='stable')[:min(5,len(distances))]
            weights=1/np.maximum(distances[indices],1e-6)
            out.append(np.average(self.y[indices],weights=weights))
        return np.asarray(out)


class Tabular:
    def __init__(self,columns,kind='logistic',seed=42):
        self.columns=columns
        if kind=='logistic':
            estimator=LogisticRegression(C=1,max_iter=3000,random_state=seed)
        else:
            from xgboost import XGBClassifier
            estimator=XGBClassifier(n_estimators=150,max_depth=2,learning_rate=.03,
                                    subsample=.8,colsample_bytree=.8,eval_metric='logloss',
                                    random_state=seed,n_jobs=1)
        self.pipe=make_pipeline(SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True),
                                StandardScaler(),estimator)

    def fit(self,frame,y):
        self.pipe.fit(frame[self.columns],y)
        return self

    def predict(self,frame):
        return self.pipe.predict_proba(frame[self.columns])[:,1]


class Altman:
    """Z'' (no +3.25 constant). Probability mapping learned on TRAIN only."""
    def fit(self,frame,y):
        self.mapping=LogisticRegression(C=1,max_iter=3000).fit(-frame[['altman_z']].to_numpy(),y)
        return self

    def predict(self,frame):
        return self.mapping.predict_proba(-frame[['altman_z']].to_numpy())[:,1]


class Cox:
    def __init__(self,horizon_days):
        self.days=horizon_days
        self.columns=['impairment','debt_assets','roa','current_ratio','ocf_assets','operating_margin']

    def fit(self,frame,y=None):
        from lifelines import CoxPHFitter
        # One last eligible training landmark per issuer for independent subjects.
        f=frame.sort_values('anchor').drop_duplicates('corp_code',keep='last')
        self.imputer=SimpleImputer(strategy='median',keep_empty_features=True).fit(f[self.columns])
        self.scale=StandardScaler().fit(self.imputer.transform(f[self.columns]))
        x=self._x(f)
        x['duration']=f.duration_days.to_numpy();x['event']=f.event_observed.to_numpy()
        if x.event.sum()<2:
            raise ValueError('Cox requires at least two training incident subjects')
        self.model=CoxPHFitter(penalizer=.1).fit(x,duration_col='duration',event_col='event')
        return self

    def _x(self,f):
        import pandas as pd
        return pd.DataFrame(self.scale.transform(self.imputer.transform(f[self.columns])),columns=self.columns)

    def predict(self,frame):
        return 1-self.model.predict_survival_function(self._x(frame),times=[self.days]).iloc[0].to_numpy()

    def risk(self,frame):
        return self.model.predict_partial_hazard(self._x(frame)).to_numpy()


def model_suite(horizon,seed):
    old=['log_current_liabilities_equity','roe'] if horizon==12 else ['equity_growth','log_current_ratio']
    return {
        'Altman_Zpp':Altman(),
        'Logistic_2013_approach':Tabular(old,seed=seed),
        'Logistic_temporal':Tabular(FEATURES,seed=seed),
        'Cox':Cox(horizon*365.25/12),
        'DTW_KNN':DTWKNN(),
        'XGBoost':Tabular(FEATURES,kind='xgboost',seed=seed),
    }
