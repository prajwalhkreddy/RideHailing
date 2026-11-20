"""Jan-Feb empirical estimator; no March fitted pool/count reuse."""
import json,hashlib
from pathlib import Path
import numpy as np
from src.pricing.binned_sampler import BinnedSensitivity
from src.pricing.slot_v3 import load_contract
from src.simulation.information_cutoff import validate_artifact
VERSION='JAN_FEB_REQUEST_WEIGHTED_BINNED_SENSITIVITY_V1'

class ProspectiveBinnedSensitivity(BinnedSensitivity):
 VERSION=VERSION
 FAMILY='REQUEST_COUNT_WEIGHTED_EMPIRICAL_BIN_RESAMPLE'
 def __init__(self,path,seed=42):
  self.calibration_path=str(Path(path).resolve());raw=Path(path).read_bytes();self.calibration_hash=hashlib.sha256(raw).hexdigest();c=json.loads(raw);self.calibration=c
  if c.get('version')!=VERSION or c.get('calibration_period')!='2026-01-01 <= pickup_timestamp < 2026-03-01':raise ValueError('Prospective calibration period mismatch')
  validate_artifact(c['population_provenance'],'2026-03-01T00:00:00-05:00')
  population=json.loads(Path(c['population_provenance']['path']).read_text())
  if population['N']!=c['source_N'] or population['filters']!='2026-01-01 <= pickup_timestamp < 2026-03-01':raise ValueError('Population provenance mismatch')
  self.contract=load_contract().copy()
  if (c['P_base'],c['L_base'])!=(self.contract['P_base'],self.contract['L_base']):raise ValueError('Reference assumption changed')
  self.grouping=c['grouping'];self.mapping={(r['raw_weather_code'],r['T_group']):r for r in self.grouping['mapping']};self.counts=c['support_counts'];self.rng=np.random.default_rng(seed);self.audit=[]
  for sid,p in c['conditions'].items():
   a=np.asarray(p['values'],float);n=np.asarray(p['request_counts'],float);w=np.asarray(p['probabilities'],float)
   if not len(a) or a.shape!=n.shape or n.shape!=w.shape or not np.isfinite(a).all() or (a<=0).any() or not np.isfinite(n).all() or (n<0).any() or (n!=np.floor(n)).any() or n.sum()<=0:raise ValueError('Invalid weighted pool')
   if not np.isfinite(w).all() or (w<0).any() or not np.allclose(w,n/n.sum(),rtol=0,atol=1e-15):raise ValueError('Invalid probabilities')
   if p['represented_requests']!=int(n.sum()) or p['source_requests']!=p['represented_requests']+p['excluded_bin_requests'] or self.counts[sid]!=p['represented_requests']:raise ValueError('Pool count mismatch')
   if p['lower']!=a.min() or p['upper']!=a.max():raise ValueError('Invalid empirical support')
  if any(n<0 or int(n)!=n or (sid not in c['conditions'] and n!=0) for sid,n in self.counts.items()):raise ValueError('Invalid fallback counts')
  if c['conditions']['GLOBAL']['source_requests']!=c['source_N']:raise ValueError('Population mismatch')
 def sample_pool(self,pool):return float(self.rng.choice(pool['values'],p=pool['probabilities']))
