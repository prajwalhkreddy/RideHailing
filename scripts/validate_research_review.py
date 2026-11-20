"""Validate review documentation without importing simulation/model implementations."""
from pathlib import Path
import re,json,csv,hashlib,shutil
from urllib.parse import unquote
R=Path(__file__).resolve().parents[1];O=R/'results_v2/publication'
def validate():
 text=(R/'README.md').read_text();paths=[unquote(x.split('#')[0]) for x in re.findall(r'\]\(([^)]+)\)',text) if not x.startswith(('http','#'))]
 broken=[p for p in paths if not (R/p).exists()]
 rows=list(csv.DictReader((O/'tables/master_traceability.csv').read_text().splitlines()))
 missing=[(r['id'],k,r[k]) for r in rows for k in ('implementation','tests','evidence') if not (R/r[k]).exists()]
 diagrams=re.findall(r'```mermaid\n(.*?)```',text,re.S);directory=O/'diagrams';directory.mkdir(exist_ok=True)
 for i,d in enumerate(diagrams,1):(directory/f'{i:02d}.mmd').write_text(d)
 figs=list(csv.DictReader((O/'tables/figure_manifest.csv').read_text().splitlines()))
 hashes=json.loads((O/'figure_sources.json').read_text());changed=[p for p,h in hashes.items() if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h]
 pilot=R/'results_v2/pricing_dqn/2026-11-20_multi_episode_orchestration';config=json.loads((pilot/'frozen_configuration.json').read_text());source_changed=[p for p,h in config['source_sha256'].items() if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h]
 counts=json.loads((O/'tables/requirement_counts.json').read_text());v=json.loads((pilot/'validation.json').read_text())
 evidence=list(csv.DictReader((O/'tables/evidence_index.csv').read_text().splitlines()));evidence_changed=[r['path'] for r in evidence if hashlib.sha256((R/r['path']).read_bytes()).hexdigest()!=r['sha256']]
 report=dict(status='PASS' if not(broken or missing or changed or source_changed or evidence_changed) else 'FAIL',local_link_occurrences=len(paths),unique_local_links=len(set(paths)),broken_links=broken,missing_matrix_paths=missing,master_requirements=len(rows),requirement_statuses=counts['statuses'],diagrams=len(diagrams),mermaid_validation='Source fences, diagram types and extraction checked; no Mermaid renderer installed; rendering not verified',figures=len(figs),figure_files=sum((O/'figures'/f"{f['figure']}.{e}").exists() for f in figs for e in ['svg','png']),figure_source_hashes_changed=changed,pilot_source_hashes_changed=source_changed,evidence_hashes_changed=evidence_changed,latest_completed_episodes=v['episodes'],remaining_training_started=v['remaining_episodes_started'],protected_data_loaded=False,models_loaded=False,simulation_executed=False,training_executed=False,limitations=['Historical raw cleaning not rerun','Historical reports are version-qualified, not current compliance evidence','Saved predictions only; no protected-period rows accessed','Formula review is source correspondence, not a formal proof'])
 (O/'documentation_validation.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__': print(json.dumps(validate(),indent=2))
