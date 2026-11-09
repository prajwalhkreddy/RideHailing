"""Read-only March16 replay/export; no training or checkpoint writes."""
from pathlib import Path
import sys,importlib.util,json,hashlib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT))
S=Path(__file__).resolve().parent.parent;OUT=S/'professor_review';V=S.parent
spec=importlib.util.spec_from_file_location('existing_staged',S/'run_staged.py');st=importlib.util.module_from_spec(spec);spec.loader.exec_module(st)
import src.simulation.passenger_sensitive_v1 as runtime
CP=Path('models/pricing_dqn/passenger_sensitive_v1_seed42/staged_training_002/episode_025')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected=[p for p in CP.iterdir() if p.is_file()]+[S/'development_evaluation.csv',S/'development_request_actions_ep25.csv']
hashes={str(p):sha(p) for p in protected}
d=st.PassengerSensitiveDQN.load(CP);before=st.fingerprint(d)
view=st.EvaluationView(d);qrows=[];select=view.select_action
def observed_select(state,mask,**kw):
 qrows.append(view.online(np.asarray(state,dtype=np.float32)[None,:],training=False).numpy()[0].copy())
 return select(state,mask,**kw)
view.select_action=observed_select
x=st.PassengerSensitiveExperiment(provider=st.provider(424242),learner=view,seed=424242,start='2026-03-16',routing_checkpoint=st.ROUTE,validation_only=True)
captured={};dispatch=runtime.dispatch_requests
def observed_dispatch(requests,*args,**kw):
 result=dispatch(requests,*args,**kw)
 for r in requests:
  captured[r.request_id]=dict(assigned_vehicle_id=r.assigned_vehicle_id,driver_origin_grid_before_assignment=r.assigned_vehicle_origin_grid,source_trip_id=r.source_trip_id)
 return result
runtime.dispatch_requests=observed_dispatch
reports=[]
try:
 for i in range(4):
  assert pd.Timestamp('2026-03-16')<=x.timestamp<pd.Timestamp('2026-03-16 02:00')
  reports.append(x.run_slot(terminal=i==3,train_dqn=False,explore_pricing=False))
  assert st.fingerprint(d)==before
finally:runtime.dispatch_requests=dispatch
f=pd.DataFrame(x.request_audit);out=pd.DataFrame();dictionary=[]
def add(name,value,meaning,units='none',source='',kind='DETERMINISTIC_DERIVATION'):
 out[name]=value;dictionary.append(dict(column=name,meaning=meaning,units=units,source=source,classification=kind))
def direct(name,col,meaning,units='none'):
 add(name,f[col],meaning,units,'replayed request_audit.'+col,'DETERMINISTIC_REPLAY')
add('request_sequence',np.arange(1,len(f)+1),'1-based export order of actual chronological requests; not a source ID',source='enumeration of request_audit order')
for a,b,m,u in [('request_id','Request_ID','Runtime request identifier','identifier'),('request_timestamp','timestamp','Runtime decision timestamp','local datetime'),('slot_index','slot','One-based main slot','index'),('origin_grid_id','Origin_Grid_ID','Request origin grid','identifier'),('destination_grid_id','Destination_Grid_ID','Request destination grid','identifier'),('L_gg_prime_km','L_gg_km','Actual request OD distance','km'),('epsilon_c','epsilon_c','Sampled positive passenger sensitivity magnitude','dimensionless'),('P_base','P_base_USD','Frozen global price reference','USD'),('L_base_km','L_base_km','Frozen global distance reference','km'),('P_raw_c','P_raw_c','Raw equation output, before platform minimum protection','USD'),('P_platform_min','P_platform_min','0.85 * P_base','USD'),('P_platform_max','P_platform_max','1.15 * P_base','USD'),('P_accept_c','P_accept_c','max(P_platform_min, P_raw_c)','USD'),('selected_action_index','selected_action_index','Zero-based chosen action','index'),('selected_price_factor','selected_factor','Chosen pricing multiplier','dimensionless'),('P_offer','P_offer_USD','selected_price_factor * P_base','USD'),('feasible_action_count','feasible_action_count','Number of feasible factors','count'),('assigned','assignment_status','Successful dispatch assignment','boolean'),('reward','reward','P_offer if assigned, otherwise zero','USD')]:direct(a,b,m,u)
add('slot_start',pd.Timestamp('2026-03-16')+pd.to_timedelta((out.slot_index-1)*30,unit='min'),'Start from actual slot index','datetime','fixture start + (slot_index-1)*30 minutes')
add('slot_end',pd.to_datetime(out.slot_start)+pd.Timedelta(minutes=30),'Exclusive slot end','datetime','slot_start + 30 minutes')
add('epsilon_support_lower',.017809913104763053,'Inclusive frozen positive-support lower bound','dimensionless','restricted_calibration_support.json')
add('epsilon_support_upper',27.324599740032788,'Inclusive frozen positive-support upper bound','dimensionless','restricted_calibration_support.json')
add('epsilon_sampling_method','TRUNCATED_EMPIRICAL_RESAMPLING','Empirical row resampling with replacement','category','restricted_calibration_support.json')
labels=['0_85','0_90','0_95','1_00','1_05','1_10','1_15'];masks=np.stack([f['mask_'+l.replace('_','')].to_numpy(bool) for l in labels],axis=1)
for i,l in enumerate(labels):direct('feasible_'+l,'mask_'+l.replace('_',''),'Candidate fare <= P_accept_c','boolean')
add('forced_request',out.feasible_action_count.eq(1),'Exactly one feasible action','boolean','feasible_action_count == 1')
add('choice_request',out.feasible_action_count.ge(2),'At least two feasible actions','boolean','feasible_action_count >= 2')
add('highest_feasible_factor',np.max(np.where(masks,st.ACTIONS,-np.inf),axis=1),'Largest feasible multiplier',source='maximum action with true mask')
add('lowest_feasible_factor',np.min(np.where(masks,st.ACTIONS,np.inf),axis=1),'Smallest feasible multiplier',source='minimum action with true mask')
add('greedy_selected',True,'Greedy selection; exploration disabled','boolean','replay explore_pricing=False')
add('offer_generated',f.P_offer_USD.notna(),'An offer was generated','boolean','P_offer_USD not null')
add('passenger_feasible',out.P_offer.le(out.P_accept_c),'Offer meets passenger effective threshold','boolean','P_offer <= P_accept_c, exact runtime comparison')
add('passenger_accepted',f.passenger_status.eq('ACCEPTED'),'Runtime passenger acceptance, distinct from matching','boolean','request_audit.passenger_status')
add('passenger_rejected',out.offer_generated & ~out.passenger_accepted,'Offered but not accepted','boolean','offer_generated AND NOT passenger_accepted')
add('passenger_rejection_reason','NOT_APPLICABLE','No passenger rejections in this fixture',source='all passenger_status == ACCEPTED verified')
add('no_feasible_action',out.feasible_action_count.eq(0),'Empty feasible mask','boolean','feasible_action_count == 0')
add('accepted_unmatched',out.passenger_accepted & ~out.assigned,'Passenger accepted but dispatch did not assign','boolean','passenger_accepted AND NOT assigned')
add('no_price_eligible_driver',f.pricing_outcome.eq('OFFERED_ACCEPTED_NO_PRICE_ELIGIBLE_DRIVER'),'Runtime no-price-eligible-driver outcome','boolean','request_audit.pricing_outcome; not passenger rejection')
add('other_unmatched',out.accepted_unmatched & ~out.no_price_eligible_driver,'Other accepted-unmatched outcome','boolean','accepted_unmatched AND NOT no_price_eligible_driver')
add('unmatched_reason',np.where(out.assigned,'NOT_APPLICABLE',np.where(out.no_price_eligible_driver,'NO_PRICE_ELIGIBLE_DRIVER','OTHER')),'Dispatch outcome reason',source='runtime pricing_outcome')
for key in ['assigned_vehicle_id','driver_origin_grid_before_assignment','source_trip_id']:
 add(key,pd.array([captured[r][key] for r in f.Request_ID],dtype='Int64'),key.replace('_',' '),'identifier','RequestState.'+key,'DETERMINISTIC_REPLAY')
add('selected_driver_price_eligible',pd.array([True if a else None for a in out.assigned],dtype='boolean'),'Runtime assigned dispatch satisfied driver price eligibility; null without assignment','boolean','request_audit.driver_price_eligible for assigned requests')
add('transition_created',False,'No learner replay transition written during read-only development','boolean','EvaluationView.store is a no-op')
add('transition_audited',f.transition_created,'Request transition tracked in ephemeral linker audit, not learner replay','boolean','request_audit.transition_created')
states=np.stack(f.state_13d);names=['J_hat','J_disp_prev','I','prob_STAY','prob_N','prob_NE','prob_E','prob_SE','prob_S','prob_SW','prob_W','prob_NW','destination_popularity']
for i,n in enumerate(names):add('state_'+n,states[:,i],'Exact DQN input component '+str(i),'model-state units','request_audit.state_13d['+str(i)+']','DETERMINISTIC_REPLAY')
q=np.stack(qrows)
for i,l in enumerate(labels):add('Q_'+l,q[:,i],'Raw unmasked online-network Q for this action','discounted USD','online(state, training=False)['+str(i)+']','DETERMINISTIC_REPLAY')
add('selected_Q',q[np.arange(len(q)),out.selected_action_index.to_numpy(int)],'Raw Q of chosen feasible action','discounted USD','Q[selected_action_index]')
add('request_outcome',np.where(out.assigned,'PASSENGER_ACCEPTED_ASSIGNED','PASSENGER_ACCEPTED_UNMATCHED_NO_PRICE_ELIGIBLE_DRIVER'),'Mutually exclusive final passenger/dispatch outcome',source='verified runtime assignment/pricing_outcome')
add('passenger_acceptance_margin_usd',out.P_accept_c-out.P_offer,'Effective threshold minus offer','USD','P_accept_c - P_offer')
add('passenger_acceptance_margin_pct_of_P_base',100*out.passenger_acceptance_margin_usd/out.P_base,'Margin as percent of base','percent','100 * margin / P_base')
add('at_acceptance_boundary',out.P_offer.eq(out.P_accept_c),'Exact equality; runtime has no feasibility tolerance','boolean','P_offer == P_accept_c')
add('raw_preference_category',np.select([out.P_raw_c.le(0),out.P_raw_c.lt(out.P_platform_min),out.P_raw_c.le(out.P_platform_max)],['RAW_NONPOSITIVE','RAW_POSITIVE_BELOW_PLATFORM_MIN','RAW_WITHIN_PLATFORM_RANGE'],default='RAW_ABOVE_PLATFORM_MAX'),'Exclusive raw-preference category; ordered tests <=0, <minimum, <=maximum, otherwise above',source='P_raw_c and platform boundaries')
expected={'offer_generated':2838,'passenger_accepted':2838,'passenger_rejected':0,'assigned':2786,'accepted_unmatched':52,'no_price_eligible_driver':52,'other_unmatched':0,'no_feasible_action':0,'forced_request':1559,'choice_request':1279}
assert len(out)==2838 and out.request_sequence.nunique()==2838 and out.request_id.nunique()==2838
for k,n in expected.items():assert int(out[k].sum())==n,(k,out[k].sum())
assert out.passenger_feasible.all() and masks[np.arange(len(out)),out.selected_action_index.to_numpy(int)].all()
assert np.array_equal(out.reward,np.where(out.assigned,out.P_offer,0))
assert np.array_equal(out.passenger_accepted,out.assigned | out.accepted_unmatched)
assert np.array_equal(out.offer_generated,out.passenger_accepted | out.passenger_rejected)
persisted=pd.read_csv(S/'development_request_actions_ep25.csv')
for a,b in [('Request_ID','request_id'),('selected_action_index','selected_action_index'),('selected_factor','selected_price_factor'),('feasible_action_count','feasible_action_count')]:assert np.array_equal(persisted[a],out[b]),a
agg=pd.read_csv(S/'development_evaluation.csv');agg=agg[agg.episode==25].iloc[0]
for actual,wanted in [(out.reward.sum(),agg.revenue),(out.P_offer.mean(),agg.mean_offer),(out.assigned.mean(),agg.assignment_rate)]:assert np.isclose(actual,wanted,rtol=1e-12,atol=1e-10),(actual,wanted)
assert st.fingerprint(d)==before
assert all(sha(Path(p))==h for p,h in hashes.items())
name='episode25_march16_request_level_acceptance';out.to_csv(OUT/(name+'.csv'),index=False)
summary=[dict(metric='requests',N=len(out),percentage=100.)]+[dict(metric=k,N=int(out[k].sum()),percentage=float(out[k].mean()*100)) for k in expected]
pd.DataFrame(summary).to_csv(OUT/(name+'_summary.csv'),index=False)
unavailable={'origin_zone_id / destination_zone_id':'Runtime request record exposes grid IDs, not distinct zone identifiers.','empirical epsilon source-row/index':'Provider returns sampled value, not sampled index.','assigned_driver_id':'Runtime exposes assigned_vehicle_id; no independent driver identity is inferred.','price_eligible_driver_count':'Legacy dispatch does not persist an exhaustive price-eligible count.','driver_price_preference':'Not stored in request audit; omitted rather than assuming vehicle ID is a profile key.','vehicle_destination_grid':'Not separately captured at assignment; request destination retained.'}
md='# Episode25 March16 request-level acceptance data dictionary\n\nSource: deterministic read-only replay of the authoritative Episode25 checkpoint, March16 00:00–02:00, seed424242 and greedy policy. Only IDs/actions/counts were originally persisted, so complete records required replay. All persisted request actions and order match exactly; aggregate revenue/outcomes reconcile. No training or learner replay writes.\n\nP_raw_c is the raw equation output; P_accept_c=max(platform minimum,P_raw_c); P_offer is the selected fare. Passenger acceptance does not imply driver matching. All 52 unmatched requests are passenger-accepted.\n\nRuntime formula: P_raw_c=P_base+(P_base/epsilon_c)*((L_gg_prime_km-L_base_km)/L_base_km). Exact runtime comparisons are used for feasibility/boundaries, without an invented tolerance.\n\n`transition_created` refers to learner replay writes (false); `transition_audited` refers to the in-memory next-request linker used for evaluation (true). Request sequence is an export ordinal, not an invented source identifier. Raw Q values are unmasked; feasibility columns must be read alongside them. Blank optional assignment identifiers mean no assignment.\n\n| Column | Meaning / formula | Units | Source | Provenance |\n| --- | --- | --- | --- | --- |\n'
for r in dictionary:md+='| '+' | '.join(str(r[k]).replace('|','/') for k in ['column','meaning','units','source','classification'])+' |\n'
md+='\n## Unavailable requested fields\n\n'+'\n'.join('- **'+k+'**: '+z for k,z in unavailable.items())+'\n'
(OUT/(name+'_DATA_DICTIONARY.md')).write_text(md)
validation=dict(status='PASS',rows=len(out),columns=len(out.columns),source='DETERMINISTIC_REPLAY',counts=expected,total_assigned_revenue=float(out.reward.sum()),authoritative_revenue=float(agg.revenue),mean_offer=float(out.P_offer.mean()),assignment_rate=float(out.assigned.mean()),persisted_request_order_actions_match=True,learner_fingerprint_before=before,learner_fingerprint_after=st.fingerprint(d),source_hashes=hashes,source_files_unchanged=True,training_performed=False,protected_period_untouched=True,unavailable=unavailable,slot_reports=reports)
(OUT/'export_validation.json').write_text(json.dumps(validation,indent=2,default=str)+'\n')
print(json.dumps({k:validation[k] for k in ['status','rows','columns','total_assigned_revenue','learner_fingerprint_before','learner_fingerprint_after']}))
