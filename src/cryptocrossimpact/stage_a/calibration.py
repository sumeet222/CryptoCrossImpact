"""Development-only response evidence, one eta decision, and tail diagnostics."""
import json,time
from pathlib import Path
import numpy as np
import pandas as pd
from ..kernel.features import DevelopmentStore,feature_names,construct
from ..kernel.workflow import read_stats,save_stats
from ..evaluation.v2_inference import paired_interval
from .common import paths,save,digest,binding
from .features import response_design,NC,TAUS
from .fit import Fitter,predict,rows,total,estimate
from .state import multipliers


def evaluate(root,models,tail=False):
    root=Path(root);out,bulk=paths(root);store=DevelopmentStore(root);l=np.array(models[0]['liquidity_usdt']);ys=np.array(models[0]['target_scale']);context=None;ac={e:np.empty((0,2)) for e in [0,.5,1]};metrics=[];daily=[]
    threshold=json.loads((root/'reports/research/stage02_artifacts/regime_definition.json').read_text())['liquidity_threshold'];at=1+feature_names().index('activity_0_60');et=1+feature_names().index('activity_1_60')
    for month in pd.period_range('2024-01','2025-12',freq='M').astype(str):
        f=store.paired(month);offset=0 if context is None else len(context);frame=f if context is None else pd.concat([context,f],ignore_index=True)
        with np.load(bulk/'state_forecasts'/f'{month}.npz') as d:aa={0:np.ones((len(f),2)),.5:d['a0.5'].copy(),1:d['a1'].copy()}
        xs={};mask=None
        for eta in [0,.5,1]:
            a=np.vstack([ac[eta],aa[eta]]);x,y,good=response_design(frame,l,a,memory=120 if tail else 60);xs[eta]=x[offset:];y=y[offset:];good=good[offset:];ac[eta]=a[-1441:]
            if mask is not None:np.testing.assert_array_equal(good,mask)
            mask=good
        if month>='2025-07':
            predictions={f'S_fit_eta{eta}':predict(models[eta],xs[eta]) for eta in [0,.5,1]}
            if not tail:
                base=predictions['S_fit_eta0'];c=np.array(models[0]['matrices'])[0]
                for eta in [.5,1]:predictions[f'S_fixed_eta{eta}']=base+np.column_stack([np.sum((xs[eta][:,i,-2:]-xs[0][:,i,-2:])*c[i],axis=1) for i in range(2)])
            groups={'all':mask,month:mask,'weekend':mask&(f.time.dt.day_of_week>=5),'weekday':mask&(f.time.dt.day_of_week<5),'liquidity_low':mask&((xs[0][:,0,at]+xs[0][:,0,et])/2<threshold),'liquidity_high':mask&((xs[0][:,0,at]+xs[0][:,0,et])/2>=threshold)}
            days=f.time.dt.strftime('%Y-%m-%d').to_numpy()
            for name,pred in predictions.items():
                err=(y-pred)/ys;ae=np.abs(y-pred)/np.sqrt(l)
                for group,g in groups.items():
                    if not g.any():continue
                    for i,asset in enumerate(['BTCUSDT','ETHUSDT']):
                        target=y[g,i]/ys[i];e=err[g,i];metrics.append(dict(model=name,group=group,asset=asset,n=int(g.sum()),sse=float(e@e),sae_bps=float(ae[g,i].sum()),ysum=float(target.sum()),y2=float(target@target)))
                for day in np.unique(days):
                    g=mask&(days==day);daily.append(dict(model=name,day=day,n=int(g.sum()),sse=float(np.sum(err[g]**2)/2),sae_bps=float(np.sum(ae[g])/2)))
        context=frame.iloc[-1441:].copy()
    f=pd.DataFrame(metrics).groupby(['model','group','asset']).sum().reset_index();f['standardized_mse']=f.sse/f.n;f['mae_bps']=f.sae_bps/f.n;f['explanatory_r2']=1-f.sse/(f.y2-f.ysum**2/f.n)
    pooled=f.groupby(['model','group']).agg(n=('n','first'),standardized_mse=('standardized_mse','mean'),mae_bps=('mae_bps','mean'),explanatory_r2=('explanatory_r2','mean')).reset_index();pooled['asset']='pooled';f=pd.concat([f,pooled],ignore_index=True)
    prefix='tail120' if tail else 'response';f.to_csv(out/f'{prefix}_metrics.csv',index=False);d=pd.DataFrame(daily);d.to_csv(out/f'{prefix}_daily.csv',index=False)
    contrasts=[];days=pd.date_range('2025-07-01','2026-01-01',inclusive='left').strftime('%Y-%m-%d');a=d[d.model=='S_fit_eta0'].set_index('day').reindex(days)
    for name,g in d.groupby('model'):
        if name=='S_fit_eta0':continue
        b=g.set_index('day').reindex(days);np.testing.assert_array_equal(a.n,b.n);delta=a.sse-b.sse
        contrasts.append(dict(model=name,**paired_interval(days,delta.to_numpy(),a.n.to_numpy(),a.sse.to_numpy())))
    pd.DataFrame(contrasts).to_csv(out/f'{prefix}_contrasts.csv',index=False)
    return f


def calibrate(root):
    root=Path(root);out,bulk=paths(root);start=time.perf_counter();fitter=Fitter(root)
    models={eta:fitter.fit('2024-01-01','2025-07-01',eta,[60],f'initial_eta{eta}') for eta in [0,.5,1]}
    old=json.loads((root/'reports/research/stage02_artifacts/model_B.json').read_text());m=models[0]
    np.testing.assert_allclose(m['matrices'],old['matrices'],rtol=1e-7,atol=1e-8);np.testing.assert_allclose(m['training_mse'],old['standardized_training_mse'],rtol=1e-9,atol=1e-10)
    if m['training_rows']!=old['training_rows']:raise ValueError('Stage2 sample mismatch')
    metrics=evaluate(root,models);pool=metrics[(metrics.asset=='pooled')&(metrics.group=='all')].set_index('model');mse={e:float(pool.loc[f'S_fit_eta{e}','standardized_mse']) for e in [0,.5,1]}
    np.testing.assert_allclose(mse[0],old['validation_mse_pooled'],rtol=1e-8,atol=1e-10)
    best=min(mse.values());candidate=min(e for e in mse if mse[e]<=best/(1-.001));gain=1-mse[candidate]/mse[0];selected=candidate if candidate and gain>=.005 else 0
    selection=dict(status='FROZEN_RESPONSE_SELECTION',selected_eta=selected,candidate_within_tie=candidate,relative_gain=1-mse[selected]/mse[0],candidate_gain=gain,mse=mse,rule='Smallest eta within0.1% of minimum; promote nonzero only with>=0.5% gain and valid PSD/timing/state checks',new_October_values_opened=False,baseline_training_rows=m['training_rows'],eta0_max_matrix_error=float(np.max(np.abs(np.array(m['matrices'])-old['matrices']))),eta0_validation_MSE_error=mse[0]-old['validation_mse_pooled'],utc=__import__('cryptocrossimpact.data.storage',fromlist=['utcnow']).utcnow(),code=binding(root),feature_manifest_sha256=__import__('cryptocrossimpact.data.storage',fromlist=['sha256']).sha256(out/'feature_manifest.json'))
    path=out/'eta_selection.json'
    if path.exists():
        prior=json.loads(path.read_text())
        if prior['mse']!={str(k):v for k,v in mse.items()} or prior['selected_eta']!=selected:raise ValueError('Scientific selection changed')
        return prior
    save(path,selection);save(out/'calibration_run.json',dict(seconds=time.perf_counter()-start,source_reads=fitter.store.read_log))
    return selection


def tail_check(root):
    root=Path(root);out,bulk=paths(root)
    if (out/'tail120_metrics.csv').exists():return
    f=Fitter(root);l=f.l;store=DevelopmentStore(root);context=None;ac={e:np.empty((0,2)) for e in [0,.5,1]};records={e:{} for e in [0,.5,1]}
    for month in pd.period_range('2024-01','2025-06',freq='M').astype(str):
        frame=store.paired(month);offset=0 if context is None else len(context);all_=frame if context is None else pd.concat([context,frame],ignore_index=True)
        with np.load(bulk/'state_forecasts'/f'{month}.npz') as d:aa={0:np.ones((len(frame),2)),.5:d['a0.5'].copy(),1:d['a1'].copy()}
        for eta in [0,.5,1]:
            a=np.vstack([ac[eta],aa[eta]]);x,y,good=response_design(all_,l,a,memory=120);x=x[offset:];y=y[offset:];good=good[offset:];records[eta][month]=rows(x[good],y[good]);ac[eta]=a[-1441:]
        context=all_.iloc[-1441:].copy()
    models={eta:estimate(total(records[eta],'2024-01','2025-07'),[60],l,eta) for eta in [0,.5,1]}
    for eta,m in models.items():save(out/'models'/f'tail120_eta{eta}.json',m)
    evaluate(root,models,True)
