"""One deterministic synthetic fixture, not experimental pricing training."""
import os
os.environ.setdefault('TF_DETERMINISTIC_OPS','1')
from pathlib import Path
from dataclasses import asdict
import json
import numpy as np,pandas as pd,tensorflow as tf
from src.rl.pricing_dqn import PricingDQN,DQNConfig,ACTIONS,bellman_targets
out=Path('results/analysis/2026-10-21_standalone_pricing_dqn');modelpath=Path('models/pricing_dqn/standalone_13x64x64x7_fixture')
if (out/'checkpoint_validation.json').exists():raise SystemExit('Completed fixture exists; refusing implicit rerun.')
tf.config.experimental.enable_op_determinism();agent=PricingDQN()
base=np.array([1,0,0,1,0,0,0,0,0,0,0,0,.5],np.float32)
# Seven explicit terminal examples repeated solely to meet default replay warmup.
for i in range(1000):agent.store(base,i%7,float(i%7+1),base,True)
def fixed_loss(a):
 q=a.online(base[None,:],training=False).numpy()[0];d=np.abs(q-np.arange(1,8));return float(np.mean(np.where(d<=1,.5*d*d,d-.5)))
initial=fixed_loss(agent);history=[]
for i in range(100):
 row=agent.train_step();row.update(step=i+1,fixed_fixture_loss=fixed_loss(agent));history.append(row)
final=fixed_loss(agent);assert final<initial
agent.save(modelpath);loaded=PricingDQN.load(modelpath)
for model1,model2 in [(agent.online,loaded.online),(agent.target,loaded.target)]:
 for x,y in zip(model1.get_weights(),model2.get_weights()):np.testing.assert_array_equal(x,y)
for x,y in zip(agent.online.optimizer.variables,loaded.online.optimizer.variables):np.testing.assert_array_equal(x.numpy(),y.numpy())
assert agent.select_action(base)==loaded.select_action(base)
a,b=agent.train_step(),loaded.train_step();assert a==b
for x,y in zip(agent.online.get_weights(),loaded.online.get_weights()):np.testing.assert_array_equal(x,y)
(out/'dqn_config.json').write_text(json.dumps(dict(**asdict(DQNConfig()),architecture=[13,64,64,7],hidden_activation='ReLU',output='raw Q',optimizer='Adam',loss='Huber delta=1',normalization='identity',epsilon_step_counter='completed optimizer updates',fixture_updates=100,checkpoint_status='SYNTHETIC_FIXTURE_NOT_FINAL_EXPERIMENTAL_MODEL'),indent=2)+'\n')
(out/'action_mapping.json').write_text(json.dumps(dict(enumerate(ACTIONS)),indent=2)+'\n')
pd.DataFrame(history).to_csv(out/'synthetic_training_history.csv',index=False)
pd.DataFrame([dict(reward=10,gamma=.99,max_target_next_q=6,done=done,expected_target=10 if done else 15.94,actual_target=float(value)) for done,value in zip([False,True],bellman_targets([10,10],[False,True],np.tile(np.arange(7),(2,1)),.99))]).to_csv(out/'bellman_fixture.csv',index=False)
validation=dict(initial_fixed_loss=initial,final_fixed_loss=final,saved_steps=100,resumed_next_update_identical=True,optimizer_restored=True,online_target_restored=True,replay_size=1000,replay_persisted=True,rng_restored=True,checkpoint=str(modelpath),notes='Checkpoint remains at step100; one unsaved continuation verifies exact resume on this environment.')
(out/'checkpoint_validation.json').write_text(json.dumps(validation,indent=2)+'\n');print(json.dumps(validation))
