"""One fresh seed42 Softplus run using the unchanged causal research trainer."""
import train_causal_research_cnn as runner
from src.demand.softplus_cnn import build_model,VERSION
runner.R=runner.ROOT/'results_v2/cnn_demand/2026-11-18_softplus_causal_research_training'
runner.M=runner.ROOT/'models/cnn/causal_persistence_120min_2026_seed42_softplus_v1'
runner.build_model=build_model
original_dump=runner.dump
def dump(path,value):
    if isinstance(value,dict):
        value['model_variant']=VERSION
        if 'architecture' in value:value['architecture']='Conv2D 7->14->7->1, hidden ReLU, final Softplus, 3x3 same, valid-grid mask'
        if 'provenance' in value:
            import json
            old=json.loads((runner.ROOT/'results_v2/cnn_demand/2026-11-18_causal_research_training/configuration.json').read_text())['provenance']
            for key in ['demand_selected_sha256','weather_selected_sha256','grid_sha256','mask_sha256','X_sha256','Y_sha256']:
                if value['provenance'][key]!=old[key]:raise ValueError('Preflight data mismatch: '+key)
            for p in ['src/demand/softplus_cnn.py','scripts/train_softplus_research_cnn.py']:value['provenance']['source_hashes'][p]=runner.sha(runner.ROOT/p)
    original_dump(path,value)
runner.dump=dump
if __name__=='__main__':
    import shutil
    if shutil.disk_usage(runner.ROOT).free<512*1024**2:raise RuntimeError('Require 512 MiB free reserve; expected new outputs <50 MiB')
    runner.main()
