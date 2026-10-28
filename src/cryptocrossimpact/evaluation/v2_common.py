"""Shared v2 provenance/serialization; no outcome data I/O."""
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

from ..data.storage import sha256,utcnow,write_json

SCOPE="modeled_execution_shortfall_excluding_funding"


def locations(root):
    root=Path(root);out=root/"reports/research/stage05_v2_artifacts";bulk=root/"results/stage05_exfunding_v2"
    out.mkdir(parents=True,exist_ok=True);bulk.mkdir(parents=True,exist_ok=True)
    return out,bulk


def config(root):
    root=Path(root)
    return yaml.safe_load((root/"configs/stage05_evaluation_v2.yaml").read_text())


def policy_config(root):
    return yaml.safe_load((Path(root)/"configs/stage04_policies.yaml").read_text())


def clean(value):
    if isinstance(value,np.ndarray):return clean(value.tolist())
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,dict):return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [clean(v) for v in value]
    return value


def digest(value):
    return hashlib.sha256(json.dumps(clean(value),sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def save(path,value):write_json(path,clean(value))


def numerical_sources(root):
    root=Path(root)
    return sorted(p for p in (root/"src/cryptocrossimpact").rglob("*.py") if p.name!="v2_report.py")+[root/"scripts/stage05_v2.py",root/"configs/stage05_evaluation_v2.yaml"]
