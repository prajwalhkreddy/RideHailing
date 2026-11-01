import json
from pathlib import Path
import pandas as pd
O=Path('results/analysis/2026-10-30_routing_effectiveness_diagnosis')
rows=[
('P_i_min / price preference','REPOSITION','C','Driver-specific p_min enters U1; not in features','operational_interface.py:decide/u1'),
('waiting preference W_max_minutes','REPOSITION','C','Driver-specific w_max enters U2; not in features','operational_interface.py:decide/u2'),
('mu and sigma','REPOSITION','A','Candidate-specific first27 feature values; U1 public inputs','final_state.py:STATE_FEATURE_ORDER'),
('F_hat','REPOSITION','A','Candidate-specific first27 values; U2 public input','final_state.py:STATE_FEATURE_ORDER'),
('H_hat all142 grids','EV_CHARGING_NEXT_HOP','A','Features27:169; U3 public input','final_state.py:STATE_FEATURE_ORDER'),
('U1 complete value','REPOSITION','C','Not derivable without P_min despite represented mu/sigma','operational_interface.py:u1'),
('U2 complete value','REPOSITION','C','Not derivable without W_max despite represented F_hat','operational_interface.py:u2'),
('U3 complete value / H_i_max','EV_CHARGING_NEXT_HOP','C','H_i_max profile input absent; baseline10 constant known externally, not encoded','operational_interface.py:u3'),
('battery / energy_kwh','both','C','Vehicle-specific energy controls branch and feasibility; absent','operational_interface.py:decide'),
('E_min / minimum_energy_kwh','both','D','Externally configured trigger compared against privateenergy; absent','operational_interface.py:decide'),
('current position / Grid_ID','both','D','Implicit candidate-relative layout; no explicitgridID, not uniquely recoverable from repeated public values','operational_interface.py:encode'),
('topological candidate mask','both','B','Separate9D mask plus placeholders; NOT a169D feature; topology mask does not encode energy feasibility','operational_interface.py:encode/candidates'),
('energy candidate feasibility','both','C','Energy consumption and station reserve check depend on vehicleenergy absent from state','operational_interface.py:preserves_station_reachability/decide'),
('charging requirement / decision type','both','C','Branch energy>minimum; neither branchindicator norenergyencoded','operational_interface.py:decide'),
('station locations and reachability','EV_CHARGING_NEXT_HOP','D','External stationmap, shortestpaths andenergy; H_hat alone insufficient','operational_interface.py:paths/decide'),
('energy_per_km','both','D','External frozen consumption parameter used for feasibility','operational_interface.py:decide'),
('movementdistance and cost','both','D','External topologydistance, actionlengths and cost_per_km; fixedmodel constants, not features','operational_interface.py:cost/candidates/paths'),
('sigma_floor and wait_floor_minutes','both','D','External fixed numerical safeguards','operational_interface.py:u1/u3'),
('tie-breaking action and station ID','both','D','Deterministic score/action/station ordering; stationIDexternal','operational_interface.py:decide'),
('idle eligibility','both','C','Vehicle idle flag is a precondition, not encoded','operational_interface.py:decide')]
pd.DataFrame(rows,columns=['input','decision_type','classification','evidence','source']).to_csv(O/'routing_state_label_information_map.csv',index=False)
contract={'IMPLEMENTATION_MISMATCH':'NO','scope':'Central versus completed offline plain-FedAvg trainer; operational online learner schedule is not used by this offline training script.','same':{'features':'same validated float32 X169, no new normalization','masks':'same boolean M9 and -1e9 invalid logits in identical compiled_step','labels':'same int32 Y0..8','architecture':'169->64ReLU->32ReLU->9logits','initialization':'build_routing_policy_model seed42 deterministic common weights; reconstruction only, no update','loss':'identical mean masked sparse categorical crossentropy fromlogits','learning_rate':.001,'batch_size':32,'dtype':'float32 training, float64 analytical probability summation'},'intentional_differences':{'central':'one chronological epoch; continuous Adam state; ceil(2656632/32)=83020 optimizersteps','fedavg':'five rounds; eachclient receives common global weights; Adam variables explicitly reset to fresh initial state for everyclient/round; one chronological localepoch; ceil(client_N/32) steps; final partialbatch used','order':'central chronological allclients; clientexamples stable chronological withinclient; no shuffling','small_clients':'positivecount participates including finalpartialbatch; zeros excluded; no local subsampling','aggregation':'samplecount-weighted final weights; all tensors previously independently verified; weighting is by observations not optimizersteps'},'sources':['scripts/train_final_behavioral_routing.py:compiled_step/main','src/routing/learning.py:build_routing_policy_model','src/routing/federated.py:aggregate_policy_updates'],'limitation':'No rerun training. No accidental inconsistency found; intentional optimizer reset/local ordering can cause statistical optimization drift.'}
(O/'central_fedavg_contract_comparison.json').write_text(json.dumps(contract,indent=2)+'\n')
