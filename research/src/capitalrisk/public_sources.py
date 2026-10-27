"""Keyless official source acquisition. Listing records are not financial events."""
import hashlib
import io
import re
import zipfile
from datetime import datetime,timezone
import pandas as pd
from .io import ROOT,download,audit,write_json


def html_text(raw):
    for encoding in ['utf-8-sig','cp949','euc-kr']:
        try: return raw.decode(encoding)
        except UnicodeDecodeError: pass
    raise ValueError('unsupported source encoding')


def acquire():
    rawdir=ROOT/'data/raw';rawdir.mkdir(parents=True,exist_ok=True)
    private=ROOT/'data/private';private.mkdir(parents=True,exist_ok=True)
    out=ROOT/'outputs';out.mkdir(exist_ok=True)
    summary={'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),
             'scope':'Downloaded records only; historical universe completeness NOT verified',
             'verified_financial_rows':0,'verified_capital_impairment_events':0,'sources':{}}
    urls={
        'kind_current':'https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13',
        'kind_delisting':'https://kind.krx.co.kr/investwarn/delcompany.do?method=searchDelCompanySub&fromDate=2015-01-01&toDate=2025-12-31&currentPageSize=3000&pageIndex=1',
        'dart_bulk_index':'https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/list.do',
    }
    tables={}
    for name,url in urls.items():
        try:
            raw=download(url,timeout=20);(rawdir/f'{name}.html').write_bytes(raw)
            summary['sources'][name]={'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
            if name!='dart_bulk_index':
                table=pd.read_html(io.StringIO(html_text(raw)),converters={'종목코드':str})[0]
                if name=='kind_delisting':
                    table.columns=['row_number','company_name','delisted_at','reason','remark']
                    table['delisted_at']=pd.to_datetime(table.delisted_at,errors='raise')
                    if not table.delisted_at.between('2015-01-01','2025-12-31').all():
                        raise ValueError('source did not respect requested date range')
                table.to_csv(private/f'{name}.csv',index=False)
                summary['sources'][name]['rows']=len(table);tables[name]=table
                audit('KIND',name,'downloaded_unverified_population',rows=len(table))
        except Exception as e:
            summary['sources'][name]={'url':url,'status':'error','reason':type(e).__name__}
            audit(name,'download','failed',type(e).__name__)
    # Follow the provider's advertised link, then verify payload type (HTTP 200 is not success).
    if (rawdir/'dart_bulk_index.html').exists():
        index=html_text((rawdir/'dart_bulk_index.html').read_bytes())
        matches=re.findall(r"'(2025_4Q_BS_[^']+\.zip)'",index)
        if matches:
            filename=matches[0]
            try:
                raw=download('https://opendart.fss.or.kr/cmm/downloadFnlttZip.do',{'fl_nm':filename},timeout=20)
                if not zipfile.is_zipfile(io.BytesIO(raw)):
                    raise ValueError('provider returned non-ZIP error page')
                (rawdir/filename).write_bytes(raw)
                summary['bulk_financial_status']='ZIP downloaded; vintage and account mapping still unverified'
                audit('OpenDART','bulk_download','downloaded',filename)
            except Exception as e:
                summary['bulk_financial_status']=str(e)
                audit('OpenDART','bulk_download','failed',str(e),filename=filename)
    if 'kind_delisting' in tables:
        table=tables['kind_delisting']
        summary['sources']['kind_delisting']['date_min']=str(table.delisted_at.min().date())
        summary['sources']['kind_delisting']['date_max']=str(table.delisted_at.max().date())
        counts=table.groupby(table.delisted_at.dt.year).size().rename('downloaded_delisting_records')
        counts.index.name='year';counts.to_csv(out/'kind_delisting_counts.csv')
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,ax=plt.subplots(figsize=(9,4))
        counts.plot.bar(ax=ax,color='#42678b',rot=0)
        ax.set(title='KIND downloaded delisting records (not capital impairment events)',ylabel='Returned records',xlabel='Year')
        fig.tight_layout();(out/'figures').mkdir(exist_ok=True)
        fig.savefig(out/'figures/collection_coverage.svg');plt.close(fig)
    write_json(out/'acquisition_summary.json',summary)
    print(__import__('json').dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': acquire()
