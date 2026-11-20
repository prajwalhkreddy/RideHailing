"""Bounded forward/autodiff only. No optimizer application or saved model edits."""
import os
os.environ.setdefault('TF_DETERMINISTIC_OPS','1')
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import numpy as np,pandas as pd,tensorflow as tf
from src.demand.final_cnn import MaskedMSE
from src.demand.persistence_weather import build_persistence,contract
O=Path(__file__).resolve().parent;M=ROOT/'models/cnn/causal_persistence_120min_2026_seed42_v1/best.keras'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before=sha(M);tf.keras.utils.set_random_seed(42);tf.config.experimental.enable_op_determinism()
base=ROOT/'data/processed/spatial_3km_jan_mar_2026'
d=pd.read_parquet(base/'demand_master_jan_mar_2026.parquet',filters=[('TimeSlot','>=',pd.Timestamp('2026-01-01')),('TimeSlot','<',pd.Timestamp('2026-01-08'))])
w=pd.read_parquet(base/'weather_jan_mar_2026.parquet',filters=[('Datetime','<',pd.Timestamp('2026-01-08'))]);g=pd.read_parquet(ROOT/'data/processed/grid_lookup.parquet',columns=['GridID','Row','Column']).sort_values('GridID')
x,y,s,_=build_persistence(d,g,w,contract(120))
sel=(s.target_start.dt.day==7)&(s.target_start.dt.hour%3==0)&(s.target_start.dt.minute==0)
assert sel.sum()==8 and s.loc[sel,'eligible'].all() and (s.loc[sel,'split']=='train').all()
x=x[sel];y=y[sel];s.loc[sel].to_csv(O/'batch_timing.csv',index=False)
model=tf.keras.models.load_model(M);original=[a.copy() for a in model.get_weights()];iterations=int(model.optimizer.iterations)
mask=np.asarray(model.get_layer('valid_grid_mask').mask_values,bool);assert mask.sum()==142
last=model.get_layer('conv_3');assert last.get_config()['activation']=='relu'
features=tf.keras.Model(model.input,last.input)
valid=np.broadcast_to(mask[None,None],y.shape);target=tf.constant(y)
with tf.GradientTape(persistent=True) as tape:
 hidden=features(tf.constant(x),training=False)
 z=tf.nn.bias_add(tf.nn.conv2d(hidden,last.kernel,strides=[1,1,1,1],padding='SAME'),last.bias);tape.watch(z)
 a=tf.nn.relu(z);pred=tf.transpose(a,[0,3,1,2])*tf.constant(mask,dtype=tf.float32)[None,None];tape.watch(pred)
 loss=model.loss(target,pred)
 zero_positive=tf.constant(valid&(y>0)) & (pred==0)
 positive_prediction=tf.constant(valid&(y>0)) & (pred>0)
 # Keep the original B*142 denominator; isolate contributions without changing loss.
 element=tf.square(pred-target)/(len(y)*142.)
 blocked_loss=tf.reduce_sum(tf.where(zero_positive,element,0.))
 active_loss=tf.reduce_sum(tf.where(positive_prediction,element,0.))
gp=tape.gradient(loss,pred).numpy();gz=tf.transpose(tape.gradient(loss,z),[0,3,1,2]).numpy()
params=tape.gradient(loss,[last.kernel,last.bias]);blocked=tape.gradient(blocked_loss,[last.kernel,last.bias]);active=tape.gradient(active_loss,[last.kernel,last.bias])
output=pred.numpy();pre=tf.transpose(z,[0,3,1,2]).numpy();reference=model(x,training=False).numpy()
np.testing.assert_array_equal(output,reference)
assert np.array_equal(output[valid]==0,pre[valid]<=0)
rows=[]
for label,select in [('all_valid',valid),('positive_target_zero_output',valid&(y>0)&(output==0)),('positive_target_positive_output',valid&(y>0)&(output>0)),('zero_target',valid&(y==0)),('invalid',~valid)]:
 n=int(select.sum());e=((output-y).astype(float)**2)[select]
 rows.append(dict(group=label,N=n,mean_target=float(y[select].mean()),zero_output_pct=float(100*(output[select]==0).mean()),pre_min=float(pre[select].min()),pre_median=float(np.median(pre[select])),pre_max=float(pre[select].max()),negative_pre_pct=float(100*(pre[select]<0).mean()),zero_pre_pct=float(100*(pre[select]==0).mean()),positive_pre_pct=float(100*(pre[select]>0).mean()),mean_abs_dloss_doutput=float(abs(gp[select]).mean()),max_abs_dloss_doutput=float(abs(gp[select]).max()),mean_abs_dloss_dpre=float(abs(gz[select]).mean()),max_abs_dloss_dpre=float(abs(gz[select]).max()),SSE=float(e.sum())))
pd.DataFrame(rows).to_csv(O/'activation_gradient_statistics.csv',index=False)
for a,b in zip(original,model.get_weights()):np.testing.assert_array_equal(a,b)
assert int(model.optimizer.iterations)==iterations and sha(M)==before
assert np.all(gz[valid&(y>0)&(output==0)]==0);assert np.all(gp[valid&(y>0)&(output==0)]<0)
assert all(np.all(t.numpy()==0) for t in blocked)
assert np.all(gp[~valid]==0) and np.all(gz[~valid]==0)
loss_manual=float(np.square(output.astype(float)-y)[valid].sum()/(len(y)*142));assert np.isclose(float(loss),loss_manual,rtol=1e-6)
result=dict(classification='A_CONFIRMED_ACTIVATION_GRADIENT_BLOCKING',batch='Jan7 2026 local: 00,03,06,09,12,15,18,21; eight eligible training samples; prefix Jan1-7 for exact history',checkpoint_sha256=before,shape=list(x.shape),target_zero_pct=float(100*(y[valid]==0).mean()),loss=float(loss),loss_manual=loss_manual,output_bias=last.bias.numpy().tolist(),parameter_gradient_L2={label:[float(tf.linalg.norm(t)) for t in ts] for label,ts in [('full_loss',params),('positive_target_zero_output_only',blocked),('positive_target_positive_output_only',active)]},parameter_order=['final_kernel','final_bias'],blocked_loss=float(blocked_loss),active_positive_loss=float(active_loss),original_forward_exact=True,weights_unchanged=True,optimizer_iterations_before=iterations,optimizer_iterations_after=int(model.optimizer.iterations),optimizer_steps_performed=0,checkpoint_unchanged=True,statistics=rows,limitations='One deterministic training-day batch; mechanism at saved checkpoint, not a reconstruction of optimization history',source_sha256={p:sha(ROOT/p) for p in ['src/demand/final_cnn.py','src/demand/causal_timing.py','src/demand/persistence_weather.py']},batch_sha256=hashlib.sha256(x.tobytes()+y.tobytes()).hexdigest(),selected_demand_sha256=hashlib.sha256(pd.util.hash_pandas_object(d,index=False).values.tobytes()).hexdigest())
(O/'validation.json').write_text(json.dumps(result,indent=2)+'\n');(O/'model_structure.json').write_text(model.to_json()+'\n')
print(json.dumps(result,indent=2))
