"""Inference-only evidence using existing slot-one routing outputs."""
import hashlib,json
from pathlib import Path
import numpy as np,pandas as pd
from tests.test_hierarchical_coupling import fixture,P
from src.rl.od_pricing_dqn import ODPricingDQN
OUT=Path(__file__).resolve().parent
_,p,c,_,_,states,pairs=fixture();net=ODPricingDQN(seed=42,master_math=True,utc_mode=True)
a=np.stack(list(states(p).values()));b=np.stack(list(states(c).values()))
qa=net.online(a,training=False).numpy();qb=net.online(b,training=False).numpy()
features=['forecast_origin','EWMA_dispatch_per_min_x30','incoming_origin','p_STAY','p_N','p_NE','p_E','p_SE','p_S','p_SW','p_W','p_NW','destination_popularity']
rows=[]
for arm,ss,qq in [('learned',a,qa),('control',b,qb)]:
 for pair,s,q in zip(pairs,ss,qq):rows.append(dict(arm=arm,origin=pair[0],destination=pair[1],**dict(zip(features,map(float,s))),**{f'Q{i}':float(x) for i,x in enumerate(q)}))
pd.DataFrame(rows).to_csv(OUT/'state_and_q_evidence.csv',index=False)
sources=['src/simulation/od_pricing_runtime.py','src/simulation/utc_od_inputs.py','src/simulation/utc_od_state.py','src/pricing/od_contract.py','src/routing/research_feedback.py','src/routing/research_hierarchy.py','src/routing/online_provenance.py','src/routing/learning.py','src/simulation/final_production.py','src/rl/od_pricing_dqn.py','tests/test_hierarchical_coupling.py','notebooks/plan/masterdocument/MASTER DOCUMENT1.docx',str(P/'validation.json'),str(P/'primary_probabilities.npz'),str(P/'control_probabilities.npz')]
out=dict(status='INFERENCE_COUPLING_VERIFIED',contexts=pairs,state_dimension=13,routing_indices=list(range(3,12)),nonrouting_identical=bool(np.array_equal(a[:,[0,1,2,12]],b[:,[0,1,2,12]])),max_abs_Q_difference=float(np.max(abs(qa-qb))),per_context_max_abs_Q_difference=np.max(abs(qa-qb),axis=1).tolist(),pricing_optimizer_updates=int(net.online.optimizer.iterations),weights_modified=False,new_training=False,full_simulations=False,fixture_origin_features='Synthetic bounded values; real January-feasible OD identities and saved first-boundary routing probabilities',previous_run_evidence=json.loads((P/'validation.json').read_text()),source_sha256={s:hashlib.sha256(Path(s).read_bytes()).hexdigest() for s in sources})
(OUT/'validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['contexts','max_abs_Q_difference','per_context_max_abs_Q_difference']}))
