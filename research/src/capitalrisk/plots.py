"""Figures are generated only from supplied verified observations."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import RocCurveDisplay,PrecisionRecallDisplay
from sklearn.calibration import CalibrationDisplay
from .features import SEQUENCE_FEATURES


def save(fig,path):
    fig.tight_layout();fig.savefig(path,dpi=160);plt.close(fig)


def exploratory(f,landmarks,events,out):
    out.mkdir(parents=True,exist_ok=True)
    if landmarks.empty:
        return []
    created=[]
    last=landmarks.sort_values('anchor').groupby('corp_code').tail(1)
    available=events[events.incident].corp_code.tolist()
    selected=last[last.corp_code.isin(available)].head(20)
    if len(selected):
        values=selected[SEQUENCE_FEATURES].to_numpy(float)
        med=np.nanmedian(values,axis=0);std=np.nanstd(values,axis=0)
        values=(values-med)/np.where(std>0,std,1)
        fig,ax=plt.subplots(figsize=(9,max(4,len(selected)*.3)))
        im=ax.imshow(values,aspect='auto',cmap='RdBu_r');fig.colorbar(im,ax=ax,label='column standardized')
        ax.set_yticks(range(len(selected)),selected.corp_code);ax.set_xticks(range(6),SEQUENCE_FEATURES,rotation=30,ha='right')
        ax.set_title(f'{len(selected)} observed event issuers (up to 20)')
        save(fig,out/'01_company_heatmap.png');created.append('01_company_heatmap.png')
        fig,ax=plt.subplots(figsize=(9,5))
        for e in events[events.incident].itertuples():
            g=f[(f.corp_code==e.corp_code)&(f.period_end<e.event_period)&
                (f.period_end>=e.event_period-np.timedelta64(730,'D'))].sort_values('filed_at').drop_duplicates('period_end')
            ax.plot((g.period_end-e.event_period).dt.days/30.4375,g.equity/g.assets.where(g.assets>0),alpha=.5,label=e.corp_code)
        ax.set(xlabel='Months before first observed event',ylabel='Equity / assets',title='Observed pre-event balance sheets; descriptive only')
        save(fig,out/'02_pre_event_24m.png');created.append('02_pre_event_24m.png')
    fig,axes=plt.subplots(2,3,figsize=(12,7))
    for ax,c in zip(axes.flat,SEQUENCE_FEATURES):
        groups=[landmarks.loc[landmarks.y_12==v,c].dropna() for v in [0,1]]
        ax.boxplot(groups,tick_labels=['No event in 12m','Event in 12m'],showfliers=False);ax.set_title(c)
    save(fig,out/'03_ratio_boxplots.png');created.append('03_ratio_boxplots.png')
    fig,ax=plt.subplots(figsize=(7,6));corr=landmarks[SEQUENCE_FEATURES].corr()
    im=ax.imshow(corr,vmin=-1,vmax=1,cmap='RdBu_r');fig.colorbar(im,ax=ax)
    ax.set_xticks(range(6),SEQUENCE_FEATURES,rotation=40,ha='right');ax.set_yticks(range(6),SEQUENCE_FEATURES)
    save(fig,out/'04_correlations.png');created.append('04_correlations.png')
    from lifelines import KaplanMeierFitter
    subjects=landmarks.sort_values('anchor').drop_duplicates('corp_code')
    fig,ax=plt.subplots(figsize=(7,5))
    KaplanMeierFitter().fit(subjects.duration_days,subjects.event_observed,label='first eligible landmark').plot_survival_function(ax=ax)
    ax.set(xlabel='Days from first eligible disclosure',ylabel='Event-free survival')
    save(fig,out/'05_kaplan_meier.png');created.append('05_kaplan_meier.png')
    landmarks[SEQUENCE_FEATURES+['y_12','y_24']].describe().to_csv(out.parent/'descriptive_statistics.csv')
    landmarks.groupby('y_12')[SEQUENCE_FEATURES].agg(['count','mean','median','std']).to_csv(out.parent/'group_statistics.csv')
    return created


def performance(predictions,results,out,horizon):
    fig,axes=plt.subplots(1,3,figsize=(17,5))
    for model,g in predictions.groupby('model'):
        if g.y.nunique()==2:
            RocCurveDisplay.from_predictions(g.y,g.probability,name=model,ax=axes[0])
            PrecisionRecallDisplay.from_predictions(g.y,g.probability,name=model,ax=axes[1])
        CalibrationDisplay.from_predictions(g.y,g.probability,n_bins=5,name=model,ax=axes[2])
    fig.suptitle(f'{horizon} months — identical held-out rows')
    save(fig,out/f'06_roc_pr_calibration_{horizon}.png')
    r=results.set_index('model')[['roc_auc','pr_auc','f1','brier']]
    ax=r.plot.bar(figsize=(11,5),rot=25);ax.set_title(f'{horizon} months; lower Brier is better')
    save(ax.figure,out/f'07_model_comparison_{horizon}.png')


def shap_plot(model,test,out,horizon):
    import shap
    x=model.pipe[:-1].transform(test[model.columns])
    # Match imputer indicators to actual transformed columns.
    columns=model.pipe[0].get_feature_names_out(model.columns)
    explainer=shap.TreeExplainer(model.pipe[-1])
    values=explainer.shap_values(x)
    shap.summary_plot(values,x,feature_names=columns,show=False)
    save(plt.gcf(),out/f'08_shap_{horizon}.png')
