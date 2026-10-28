#!/usr/bin/env python3
"""Finite disjoint development batch; same frozen replay, max ONE extra worker.

Run only while the serial driver is before index500. This batch owns indices
600..735; it must finish before the serial driver reaches600. No source/model
changes or cross-process policy state. Completed receipts resume identically.
"""
from pathlib import Path
import sys,time,resource,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from cryptocrossimpact.stage_a.execution import fitted_models,replay
from cryptocrossimpact.robust.workflow import development_episodes
from cryptocrossimpact.stage_a.common import paths,save,binding
from cryptocrossimpact.data.storage import sha256,utcnow
root=Path(__file__).resolve().parents[1];out,bulk=paths(root);selection=json.loads((out/'eta_selection.json').read_text())['selected_eta']
folder=bulk/'development';episodes=development_episodes(root)[600:];start=time.perf_counter();last=None
save(out/'bounded_worker_start.json',dict(utc=utcnow(),first_index=600,end_exclusive=736,episodes=len(episodes),maximum_extra_workers=1,wrapper_sha256=sha256(Path(__file__)),code=binding(root)))
for j,e in enumerate(episodes):
    month=e.t0.strftime('%Y-%m')
    if month!=last:models={eta:fitted_models(root,month,eta) for eta in [.5,1]};last=month
    replay(root,e,models,selection,folder)
    if (j+1)%10==0:print('StageA bounded final batch',j+1,'/136',round((time.perf_counter()-start)/60,2),'min',flush=True)
save(out/'bounded_worker_complete.json',dict(status='PASS',utc=utcnow(),episodes=len(episodes),first_index=600,end_exclusive=736,seconds=time.perf_counter()-start,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**2,wrapper_sha256=sha256(Path(__file__)),code=binding(root)))
