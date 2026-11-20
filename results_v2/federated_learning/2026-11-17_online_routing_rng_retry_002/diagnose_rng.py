import json,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
import tensorflow as tf,numpy as np
from src.simulation.v3_checkpoint import rng_bundle
from src.simulation.v3_checkpoint_codec import encode
from src.routing.learning import build_routing_policy_model,RoutingLearningParameters
from src.fleet.research_mixed import configure
from tests.test_research_hierarchy import fleet
h=lambda x:hashlib.sha256(json.dumps(encode(x),sort_keys=True).encode()).hexdigest()
def snap():return {k:h(v) for k,v in rng_bundle().items()}
a={'process_initial':snap()}
tf.keras.utils.set_random_seed(42);a['seed42']=snap()
m=build_routing_policy_model(RoutingLearningParameters(),seed=42);a['model']=snap();a['weights']=h(m.get_weights())
f=fleet(10);configure(f,.1,42);a['fleet']=snap()
a['capture_again']=snap()
print(json.dumps(a))
