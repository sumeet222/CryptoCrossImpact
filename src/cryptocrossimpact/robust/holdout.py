"""Gated six-archive acquisition, source QC and frozen July–September replay."""
import json
from pathlib import Path
import resource
import shutil
import time
import zipfile
import numpy as np
import pandas as pd
import requests
import yaml

from ..data.storage import sha256,utcnow
from ..data.schema import parse_zip,validate_identity,summarize
from .canonical import canonicalize
from .common import paths,save,config,digest,binding,START,END
from .protocol import validate_ready,PretestHold
from .data import Store,make_episode,utc
from .workflow import replay_episode,model_bundle


def get_file(url,path):
    """Bounded official public download; no provider restriction workaround."""
    path=Path(path)
    response=requests.get(url,stream=True,timeout=60)
    if response.status_code!=200:raise PretestHold(f'Official source inaccessible HTTP{response.status_code}: {url}')
    size=0;temporary=path.with_suffix(path.suffix+'.part')
    with temporary.open('wb') as f:
        for chunk in response.iter_content(1024*1024):
            size+=len(chunk)
            if size>1_000_000_000:raise PretestHold('Archive exceeds frozen size guard')
            f.write(chunk)
    temporary.replace(path)
    return size


def acquire(root):
    root=Path(root);out,bulk=paths(root);ready=validate_ready(root)
    initial=sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
    if initial+6_000_000_000>30_000_000_000:raise PretestHold('Storage ceiling preflight HOLD')
    if shutil.disk_usage(root).free<2_000_000_000:raise PretestHold('Insufficient disk headroom')
    raw=root/'data/raw/extension_x2x3';raw.mkdir(parents=True,exist_ok=True)
    manifest_path=out/'new_source_manifest.json';manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else dict(
        venue='Binance',market='futures/um',interval='1m',price_type='last traded price',partitions={},terms='CC BY-NC-SA4.0 noncommercial',
        terms_url='https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md')
    qa=[];core=yaml.safe_load((root/'configs/core.yaml').read_text())
    for month in ['2026-07','2026-08','2026-09']:
        for symbol in ['BTCUSDT','ETHUSDT']:
            key=f'{symbol}/{month}';name=f'{symbol}-1m-{month}.zip'
            url=f'https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/1m/{name}'
            validate_identity(url,symbol,month)
            if key in manifest['partitions']:
                if sha256(root/manifest['partitions'][key]['canonical_path'])!=manifest['partitions'][key]['canonical_sha256']:raise PretestHold('New canonical changed')
                continue
            archive=raw/name;check=raw/(name+'.CHECKSUM')
            if not check.exists():get_file(url+'.CHECKSUM',check)
            expected=check.read_text().split()[0]
            if len(expected)!=64 or any(c not in '0123456789abcdefABCDEF' for c in expected):raise PretestHold('Invalid official checksum')
            if not archive.exists():get_file(url,archive)
            if sha256(archive)!=expected.lower():raise PretestHold('Official SHA256 mismatch')
            receipt=out/'first_source_value_open.json'
            if not receipt.exists():save(receipt,dict(utc=utcnow(),purpose='SOURCE_QC_ONLY_AFTER_FREEZE',ready_lock=ready['lock_sha256'],source=url,
                note='Acquisition/schema/QC sees source values only after freeze; economic policy reads remain bounded and prefix-authorized.'))
            frame=parse_zip(archive,symbol,month,url)
            previous_month=(pd.Period(month,freq='M')-1).strftime('%Y-%m');previous_path=root/f'data/canonical/{symbol}/{previous_month}.parquet'
            previous=None
            if previous_path.exists():
                end=pd.Timestamp(month+'-01',tz='UTC');prev=pd.read_parquet(previous_path,columns=['symbol','open_time','close','valid_bar'],filters=[('bar_open_utc','>=',end-pd.Timedelta(minutes=1)),('bar_open_utc','<',end)])
                if len(prev)==1:previous=prev.iloc[0].to_dict()
            df=canonicalize(frame,symbol,month,core,previous);summary=summarize(df,month)
            if summary['missing_minutes'] or summary['invalid_bars']:raise PretestHold('New source violates complete/QC source gate; no date replacement')
            canonical=root/f'data/canonical/{symbol}/{month}.parquet';canonical.parent.mkdir(exist_ok=True)
            if canonical.exists():raise PretestHold('Unregistered pre-existing holdout partition; refuse overwrite')
            temp=canonical.with_suffix('.parquet.part');df.to_parquet(temp,index=False,compression='zstd');temp.replace(canonical)
            manifest['partitions'][key]=dict(url=url,venue='Binance',market='futures/um',symbol=symbol,quote_units='USDT',clock='UTC integer ms open; available=open+60000',
                source_sha256=expected.lower(),checksum_sha256=sha256(check),canonical_path=str(canonical.relative_to(root)),canonical_sha256=sha256(canonical),rows=len(df),
                start=summary['first_open_utc'],end=summary['last_open_utc'],source_bytes=archive.stat().st_size,canonical_bytes=canonical.stat().st_size,
                schema='Stage1 twelve futures fields and unchanged quality math; new holdout split label only',QC=summary)
            save(manifest_path,manifest);qa.append(dict(partition=key,**summary));print('Acquired/QC',key,len(df),flush=True)
        a,b=[pd.read_parquet(root/f'data/canonical/{s}/{month}.parquet',columns=['open_time']) for s in ['BTCUSDT','ETHUSDT']]
        if not np.array_equal(a.open_time,b.open_time):raise PretestHold('Holdout pair calendar mismatch')
    save(out/'new_source_qc.json',dict(status='PASS',partitions=6,rows=sum(x['rows'] for x in manifest['partitions'].values()),
        source_manifest_sha256=sha256(manifest_path),initial_storage_bytes=initial,details=qa,ready_lock=ready['lock_sha256']))
    return manifest


def holdout(root):
    root=Path(root);out,bulk=paths(root)
    # This gate precedes HTTP access, new file stat/hash, and value I/O.
    ready=validate_ready(root)
    if (out/'holdout_gate_audit.json').exists() and json.loads((out/'holdout_gate_audit.json').read_text())['status']=='COMPLETE':
        return [json.loads(p.read_text()) for p in sorted((bulk/'holdout').glob('*.json')) if '_decisions' not in p.name and '_prefix_' not in p.name]
    try:acquire(root)
    except (PretestHold,requests.RequestException) as exc:
        save(out/'holdout_gate_audit.json',dict(status='OOS_HOLD',utc=utcnow(),reason=str(exc),outcome_values_opened=(out/'first_source_value_open.json').exists(),pretest='READY'))
        raise
    selection=json.loads((out/'development_selection.json').read_text());lam=selection['display_lambda']
    specs=[('N','nominal',0),('D','nominal_diagonal',0),('G','robust',0),('L','nominal',lam),('GL','robust',lam),('GL-D','robust_diagonal',lam)]
    store=Store(root);scorer=Store(root);folder=bulk/'holdout';results=[];statuses=[];start=time.perf_counter()
    for month in ['2026-07','2026-08','2026-09']:
        origin=pd.Timestamp(month+'-01',tz='UTC');end=origin+pd.offsets.MonthBegin(1);b,ws=model_bundle(root,month,origin)
        for t in pd.date_range(origin,end,freq='6h',inclusive='left'):
            e=make_episode(store.history(t),t,root)
            r=replay_episode(root,e,b,ws,store,scorer,folder,specs);results.append(r);statuses.append(dict(episode_id=e.episode_id,status='SCORED'))
            if len(results)%10==0:print(f'X2X3 holdout {len(results)}/368 {(time.perf_counter()-start)/60:.2f}min',flush=True)
        save(out/f'closed_{month}.json',dict(month=month,complete=sum(r['episode_id'].startswith(origin.strftime('%Y%m')) for r in results),
            nominal=(end-origin).days*4,status='CLOSED',utc=utcnow()))
        if month!='2026-09':
            from .fit import Fitter
            fitter=Fitter(root,Store(root));fitter.observe_month(month)
    for key,filename in [('scores','holdout_scores'),('liquidity','holdout_overload'),('diagnostics','holdout_solver_diagnostics'),('scenario_qa','holdout_liquidity_scenario_qa')]:
        pd.DataFrame([v for r in results for v in r[key]]).to_csv(out/f'{filename}.csv',index=False)
    pd.DataFrame(statuses).to_csv(out/'holdout_episode_status.csv',index=False)
    save(out/'holdout_gate_audit.json',dict(status='COMPLETE',utc=utcnow(),episodes=len(results),pretest='READY',
        ready_sha256=__import__('cryptocrossimpact.data.storage',fromlist=['sha256']).sha256(out/'PRETEST_READY_X2X3.json'),
        first_source_receipt='first_source_value_open.json',seconds=time.perf_counter()-start,
        peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**2,source_reads=store.read_log+scorer.read_log))
    return results
