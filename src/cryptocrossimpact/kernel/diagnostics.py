"""G2-only synthetic recovery, estimator uncertainty and confounding checks."""
import json

import numpy as np
import pandas as pd

from ..data.storage import write_json
from .features import DevelopmentStore,batches,feature_names,flow_basis,ASSETS,FIREWALL
from .fit import Stats,normalize,transforms,estimate,loss,normalized_rows,finite_grid_check,level_kernel,validate_components
from .workflow import config,locations,load_prepared,total,winners,prepare


def synthetic_recovery(root):
    out,_=locations(root);rng=np.random.default_rng(20261027);rows=[]
    for taus,cross in [([5],0.),([5],-.3),([5,30],.25)]:
        n=8000;f=rng.normal(size=(n,2));f[:,1]+=.4*f[:,0]
        nuisance=rng.normal(size=(n,24));nuisance[:,0]+=.5*f[:,0]
        truth=np.array([[[1,cross],[cross,.8]],[[.3,.1],[.1,.5]]])[:len(taus)]
        # Independent convolution generates the target, not the fitted basis helper.
        actual=np.zeros((n,2))
        for k,tau in enumerate(taus):
            weights=np.r_[1.,np.diff(np.exp(-np.arange(61)/tau))]
            z=np.column_stack([np.convolve(f[:,j],weights,mode="full")[:n] for j in range(2)])
            actual+=z@truth[k].T
        y=actual+nuisance[:,:2]@np.array([[.1,.2],[-.2,.1]])+rng.normal(size=(n,2))*.0001
        z=flow_basis(f,taus,60)
        x=np.column_stack([np.ones(n),nuisance,z.reshape(n,-1)])[60:];y=y[60:]
        raw=Stats.rows(x,y);normal=transforms(raw)
        m=estimate(normalize(raw,normal),normal,taus,taus,"B",0)
        error=float(np.max(np.abs(np.array(m["matrices"])-truth)))
        if error>.002:raise ValueError("Known-kernel recovery exceeded noise tolerance")
        rows.append(dict(taus=taus,cross=cross,truth=truth.tolist(),estimated=m["matrices"],max_absolute_coefficient_error=error,
                         valid_negative_cross=cross<0,nuisance_correlated_flow=True,status="PASS",finite_grid=finite_grid_check(m)))
    write_json(out/"synthetic_recovery.json",dict(status="PASS",seed=20261027,cases=rows))


def bootstrap(root):
    cfg=config(root);out,_=locations(root);models=winners(root);b=models["B"]
    _,days,f=load_prepared(root)
    days={k:v for k,v in days.items() if k<"2025-07-01"}
    keys=list(days);d=len(keys);rng=np.random.default_rng(cfg["seed"]);records=[]
    base_cross=float(np.array(b["matrices"])[:,0,1].sum())
    for replicate in range(cfg["bootstrap_replicates"]):
        starts=rng.integers(0,d-cfg["bootstrap_block_days"]+1,size=(d+6)//7)
        positions=np.concatenate([np.arange(i,i+7) for i in starts])[:d]
        weights=np.bincount(positions,minlength=d)
        raw=Stats.zeros(len(next(iter(days.values())).xy))
        for i,weight in enumerate(weights):
            if weight:raw.add(days[keys[i]],int(weight))
        m=estimate(normalize(raw,f["normalization"]),f["normalization"],b["taus_minutes"],cfg["decays_minutes"],"B",b["ridge"])
        c=np.array(m["matrices"])
        record=dict(replicate=replicate,status=m["status"],rows=raw.n,instantaneous_cross=float(c[:,0,1].sum()),
            sign_reversal=bool(np.sign(c[:,0,1].sum())!=np.sign(base_cross)),
            psd_binding_components=sum(int(v["psd_binding"]) for v in m["component_diagnostics"]))
        for k,mat in enumerate(c):
            for i,j in [(0,0),(0,1),(1,1)]:record[f"C{k}_{i}{j}"]=float(mat[i,j])
        records.append(record)
        if (replicate+1)%10==0:print(f"Bootstrap {replicate+1}/50",flush=True)
    frame=pd.DataFrame(records);frame.to_csv(out/"bootstrap.csv",index=False)
    ci=np.quantile(frame.instantaneous_cross,[.025,.5,.975])
    write_json(out/"bootstrap_summary.json",dict(status="PASS",replicates=len(records),block_days=7,
        instantaneous_cross_95pct_interval=[float(ci[0]),float(ci[2])],median=float(ci[1]),
        sign_reversals=int(frame.sign_reversal.sum()),binding_fraction=float((frame.psd_binding_components>0).mean()),
        normalization="Fixed original training L/centering/scales and selected family/penalty; conditional preprocessing uncertainty",
        boundary_rule="Features computed on original contiguous observations before block selection; no new adjacency or recomputation across resampled blocks"))


def shifted_cross_stats(x,y,mask,base,taus,all_taus,shift):
    """Only opposite-asset columns move; own flow, outcomes and controls stay put.

    x and y use fixed original training scales. shift is a circular row offset
    on the FULL regular calendar, before structural eligibility filtering.
    """
    nc=1+len(feature_names());g=np.stack([base.gram.copy(),base.gram.copy()]);h=base.xy.copy()
    unshifted=x[mask]
    for i in range(2):
        opposite=1-i
        cc=[nc+2*all_taus.index(tau)+opposite for tau in taus]
        shifted=np.roll(x[:,cc],shift,axis=0)[mask]
        cross=unshifted.T@shifted
        g[i,:,cc]=cross.T  # advanced indexing puts cc dimension first
        g[i,cc,:]=cross.T
        g[i][np.ix_(cc,cc)]=shifted.T@shifted
        h[cc,i]=shifted.T@y[mask,i]
    return Stats(base.n,g,h,base.yy.copy())


def permutation(root):
    cfg=config(root);out,_=locations(root);b=winners(root)["B"]
    _,_,features=load_prepared(root);store=DevelopmentStore(root)
    xs,ys,valids=[],[],[]
    for _,_,x,y,valid in batches(store,np.array(features["liquidity_usdt"]),cfg["decays_minutes"],end="2025-06"):
        xs.append(normalized_rows(x,features["normalization"]));ys.append(y/np.array(features["normalization"]["target_scale"]));valids.append(valid)
    x=np.concatenate(xs);y=np.concatenate(ys);mask=np.concatenate(valids);del xs,ys,valids
    nc=1+len(feature_names());flow_ok=np.isfinite(x[:,nc:]).all(axis=1)
    for shift in cfg["placebo_shift_days"]:mask &= np.roll(flow_ok,shift*1440)
    base=Stats.rows(x[mask],y[mask])
    reference_b=estimate(base,features["normalization"],b["taus_minutes"],cfg["decays_minutes"],"B",b["ridge"])
    reference_a=estimate(base,features["normalization"],b["taus_minutes"],cfg["decays_minutes"],"A",b["ridge"])
    mse_a=float(np.mean(reference_a["standardized_training_mse"]))
    observed_gain=(mse_a-np.mean(reference_b["standardized_training_mse"]))/mse_a
    observed_cross=float(np.array(reference_b["matrices"])[:,0,1].sum())
    records=[]
    for shift in cfg["placebo_shift_days"]:
        statistics=shifted_cross_stats(x,y,mask,base,b["taus_minutes"],cfg["decays_minutes"],shift*1440)
        m=estimate(statistics,features["normalization"],b["taus_minutes"],cfg["decays_minutes"],"B",b["ridge"])
        c=np.array(m["matrices"])
        records.append(dict(shift_days=shift,rows=int(mask.sum()),status=m["status"],instantaneous_cross=float(c[:,0,1].sum()),
                            training_mse=float(np.mean(m["standardized_training_mse"])),
                            relative_training_gain_vs_matched_A=float((mse_a-np.mean(m["standardized_training_mse"]))/mse_a)))
        if len(records)%10==0:print(f"Cross-only whole-day placebo {len(records)}/50",flush=True)
    frame=pd.DataFrame(records);frame.to_csv(out/"placebo.csv",index=False)
    write_json(out/"placebo_summary.json",dict(status="PASS",replicates=len(records),rows=int(mask.sum()),
        primary_training_rows=features["coverage"][0]["eligible"]+sum(r["eligible"] for r in features["coverage"][1:] if r["split"]=="train"),
        observed_same_mask_training_gain=float(observed_gain),observed_instantaneous_cross=observed_cross,
        null_gain_range=[float(frame.relative_training_gain_vs_matched_A.min()),float(frame.relative_training_gain_vs_matched_A.max())],
        null_cross_range=[float(frame.instantaneous_cross.min()),float(frame.instantaneous_cross.max())],
        empirical_diagnostic_tail_fraction=float((1+(frame.relative_training_gain_vs_matched_A>=observed_gain).sum())/(len(frame)+1)),
        own_flow_alignment_preserved=True,cross_flow_only=True,
        common_null_mask="Original valid targets/controls and finite shifted cross bases for all 50 offsets; fixed before null comparisons",
        caution="In-training falsification, not causal identification or final-test significance; periodic effects and endogeneity remain"))


def rescale_raw(stats,old_l,new_l):
    """Congruent unit conversion of sufficient statistics for a new past window."""
    nc=1+len(feature_names());d=np.ones(len(stats.xy));ratio=np.sqrt(np.asarray(old_l)/np.asarray(new_l))
    d[nc:]=np.tile(ratio,(len(d)-nc)//2)
    yratio=1/ratio
    return Stats(stats.n,stats.gram*d[:,None]*d[None,:],stats.xy*d[:,None]*yratio[None,:],stats.yy*yratio**2)


def refit_historical(root,cutoff,window_days=365,model="B"):
    """Reusable past-window API, guarded to development cutoffs in this stage.

    Stage 5 must explicitly authorize extending the I/O firewall. This API is
    never invoked for 2026 refits here. Features retain original past context.
    """
    finish=pd.Timestamp(cutoff,tz="UTC");start=finish-pd.Timedelta(days=window_days)
    if finish>FIREWALL or start<pd.Timestamp("2024-01-01",tz="UTC"):
        raise ValueError("Historical refit lacks complete history or crosses Stage 2 firewall")
    cfg=config(root);_,daily,f=load_prepared(root);base=winners(root)[model]
    raw=total(daily,lambda k:str(start.date())<=k<str(finish.date()))
    store=DevelopmentStore(root);l=store.liquidity(str(start.date()),str(finish.date()))
    converted=rescale_raw(raw,f["liquidity_usdt"],l);normal=transforms(converted)
    fit=estimate(normalize(converted,normal),normal,base["taus_minutes"],cfg["decays_minutes"],model,base["ridge"])
    fit.update(liquidity_usdt=l.tolist(),training_start=str(start),training_end_exclusive=str(finish),asset_order=ASSETS,memory_minutes=60)
    return fit


def stability(root):
    cfg=config(root);out,_=locations(root);models=winners(root);b=models["B"]
    monthly,days,f=load_prepared(root);lref=np.array(f["liquidity_usdt"]);records=[]
    for label,start,end in [("train_half1","2024-01-01","2024-10-01"),("train_half2","2024-10-01","2025-07-01")]:
        raw=total(days,lambda k:start<=k<end);store=DevelopmentStore(root);l=store.liquidity(start,end)
        converted=rescale_raw(raw,lref,l);normal=transforms(converted)
        m=estimate(normalize(converted,normal),normal,b["taus_minutes"],cfg["decays_minutes"],"B",b["ridge"])
        m.update(liquidity_usdt=l.tolist(),training_start=start,training_end_exclusive=end)
        write_json(out/f"model_{label}.json",m)
        for k,c in enumerate(np.array(m["matrices"])):
            convert=np.sqrt(lref/l);cref=c*convert[:,None]*convert[None,:]
            records.append(dict(window=label,component=k,tau=b["taus_minutes"][k],C00_reference=cref[0,0],C01_reference=cref[0,1],C11_reference=cref[1,1],
                                cross_ratio=c[0,1]/np.sqrt(c[0,0]*c[1,1]),min_eigenvalue=float(np.linalg.eigvalsh(c).min())))
    # Six authorized development-only rolling fits, ending before validation months.
    for month in pd.period_range("2025-07","2025-12",freq="M").astype(str):
        m=refit_historical(root,month+"-01")
        write_json(out/f"model_development_refit_{month}.json",m)
        for k,c in enumerate(np.array(m["matrices"])):
            convert=np.sqrt(lref/np.array(m["liquidity_usdt"]));cref=c*convert[:,None]*convert[None,:]
            records.append(dict(window=month,component=k,tau=b["taus_minutes"][k],C00_reference=cref[0,0],C01_reference=cref[0,1],C11_reference=cref[1,1],
                cross_ratio=c[0,1]/np.sqrt(c[0,0]*c[1,1]),min_eigenvalue=float(np.linalg.eigvalsh(c).min())))
    pd.DataFrame(records).to_csv(out/"time_stability.csv",index=False)
    # Fixed, predeclared source-QC sensitivity; primary sample stays intact.
    start=cfg["diagnostics"]["anomaly_sensitivity_exclude_start"];end=cfg["diagnostics"]["anomaly_sensitivity_exclude_end_exclusive"]
    raw=total(days,lambda k:k<"2025-07-01" and not start<=k<end)
    val=normalize(total(monthly,lambda k:k>="2025-07"),f["normalization"])
    sensitivity=[]
    for name in ("A","B"):
        base=models[name]
        for omit,tag in [(False,"source_flag_interval_mask"),(True,"no_return_controls")]:
            current=normalize(raw if not omit else total(monthly,lambda k:k<"2025-07"),f["normalization"])
            m=estimate(current,f["normalization"],base["taus_minutes"],cfg["decays_minutes"],name,base["ridge"],omit_return_controls=omit)
            vm=loss(val.subset(m["indices"]),np.array(m["theta_standardized"]))
            sensitivity.append(dict(mode=tag,model=name,training_rows=current.n,validation_rows=val.n,validation_mse_btc=float(vm[0]),validation_mse_eth=float(vm[1]),
                validation_mse_pooled=float(vm.mean()),instantaneous_cross=float(np.array(m["matrices"])[:,0,1].sum())))
    pd.DataFrame(sensitivity).to_csv(out/"restricted_sensitivity.csv",index=False)


def mode_diagnostics(root):
    cfg=config(root);out,_=locations(root);models=winners(root);rows=[]
    specs=[("lag_only",60,"_lag_only"),("lead_placebo",60,"_lead_placebo"),("primary",30,"_h30"),("primary",120,"_h120")]
    for mode,memory,suffix in specs:
        monthly,_,normal,l=prepare(root,memory=memory,mode=mode,suffix=suffix)
        train=normalize(total(monthly,lambda k:k<"2025-07"),normal);val=normalize(total(monthly,lambda k:k>="2025-07"),normal)
        for name in ("N0","U","A","B"):
            base=models[name]
            m=estimate(train,normal,base["taus_minutes"],cfg["decays_minutes"],name,base["ridge"])
            vm=loss(val.subset(m["indices"]),np.array(m["theta_standardized"]))
            rows.append(dict(mode=mode,H=memory,model=name,training_rows=train.n,validation_rows=val.n,
                validation_mse_btc=float(vm[0]),validation_mse_eth=float(vm[1]),validation_mse_pooled=float(vm.mean()),
                instantaneous_cross=float(np.array(m["matrices"])[:,0,1].sum()) if m["matrices"] else 0.))
        pd.DataFrame(rows).to_csv(out/"mode_diagnostics.csv",index=False)
    b=models["B"];g=level_kernel(b,[0,60]);liquidity=np.array(b["liquidity_usdt"])
    boundary_sum=np.zeros(2);n=0;store=DevelopmentStore(root)
    # The hypothetical missing boundary coefficient in a differenced truncated
    # level kernel is -G(H)f[t-H-1], absent by design from the primary regression.
    for month,frame,_,y,valid in batches(store,liquidity,cfg["decays_minutes"]):
        if month>="2025-07":break
        q=np.column_stack([frame[f"signed_taker_quote_flow_{j}"] for j in range(2)])/np.sqrt(liquidity)
        # Use intra-month rows only for this diagnostic, avoiding invented context.
        use=valid.copy();use[:61]=False
        displacement=np.zeros_like(q);displacement[61:]=q[:-61]@g[1].T
        boundary_sum+=np.sum((displacement[use]/np.array(b["normalization"]["target_scale"]))**2,axis=0);n+=int(use.sum())
    write_json(out/"tail_diagnostic.json",dict(level_fraction_at_H=float(np.linalg.norm(g[1])/np.linalg.norm(g[0])),
        hypothetical_Hplus1_boundary_rms_over_target_sd=np.sqrt(boundary_sum/n).tolist(),
        rows=n,primary_boundary_term_included=False,primary_H=60,decay_on_grid_upper_bound=max(b["taus_minutes"])==max(cfg["decays_minutes"]),
        caution="Tail difference is a model-truncation diagnostic, not an observed missing-impact estimate; H=30/120 never replaces the primary H=60 result"))


def run_diagnostics(root):
    synthetic_recovery(root)
    bootstrap(root)
    permutation(root)
    stability(root)
    mode_diagnostics(root)
    out,_=locations(root)
    write_json(out/"diagnostic_completion.json",dict(status="PASS",synthetic=True,bootstrap=50,cross_only_permutations=50,
        training_halves=2,development_monthly_refits=6,lag_only=True,lead_falsification=True,memory_sensitivities=[30,120],
        source_flag_sensitivity=True,no_return_control_sensitivity=True,
        optional_forward_prediction="NOT RUN; prioritized mandatory G2 estimation/falsification; no alpha or policy claim"))
