"""Versioned fitted-information guard; realized events have a separate clock."""
import hashlib
from pathlib import Path
import pandas as pd
VERSION='PROSPECTIVE_INFORMATION_CUTOFF_V1'

def aware(value):
    t=pd.Timestamp(value)
    if pd.isna(t) or t.tz is None:raise ValueError('Explicit aware information timestamp required')
    return t.tz_convert('UTC')

def validate_artifact(a, permitted_cutoff):
    for k in ['source_start','source_end_exclusive','latest_observation','fitting_cutoff','path','sha256','methodology_version']:
        if k not in a:raise ValueError('Missing fitted provenance: '+k)
    start,end,last,fit=map(aware,[a['source_start'],a['source_end_exclusive'],a['latest_observation'],a['fitting_cutoff']])
    if not start<=last<end<=fit<=aware(permitted_cutoff):raise ValueError('Fitted information exceeds cutoff')
    if a.get('selection_end_exclusive') is not None and aware(a['selection_end_exclusive'])>aware(permitted_cutoff):raise ValueError('Upstream model selection exceeds cutoff')
    if not a['methodology_version']:raise ValueError('Missing methodology identity')
    if hashlib.sha256(Path(a['path']).read_bytes()).hexdigest()!=a['sha256']:raise ValueError('Fitted artifact fingerprint mismatch')

def validate_manifest(m):
    if m.get('version') not in {VERSION,'CHRONOLOGICAL_INFORMATION_CUTOFF_V2'}:raise ValueError('Information contract mismatch')
    limits={'sensitivity':'2026-03-01T00:00:00-05:00','od_support':'2026-02-01T00:00:00-05:00','routing':'2026-03-12T00:00:00-04:00','forecast':'2026-03-11T23:30:00-04:00','popularity':'2026-02-01T00:00:00-05:00','operational_prior':'2026-03-01T00:00:00-05:00','driver_profiles':'2026-03-01T00:00:00-05:00'}
    if m['version']=='CHRONOLOGICAL_INFORMATION_CUTOFF_V2':
        limits.update(routing='2026-03-01T05:00Z',forecast='2026-03-01T05:00Z')
    for role,a in m['artifacts'].items():
        if role not in limits or aware(m['permitted_cutoffs'][role])!=aware(limits[role]):raise ValueError('Unapproved permitted cutoff')
        if role=='routing' and a.get('kind')=='FRESH_ONLINE':
            import json
            from src.routing.online_provenance import validate, VERSION as ONLINE, MULTI_VERSION
            validate(json.loads(Path(a['path']).read_text()))
            expected_online=MULTI_VERSION if m['version']=='CHRONOLOGICAL_INFORMATION_CUTOFF_V2' else ONLINE
            if a['methodology_version']!=expected_online or hashlib.sha256(Path(a['path']).read_bytes()).hexdigest()!=a['sha256']:raise ValueError('Online routing fingerprint mismatch')
        elif role=='routing' and a.get('kind')=='NONLEARNED':
            from src.simulation.research_utility_routing import validate, VERSION as ROUTING_VERSION
            validate(a['path'])
            if a['methodology_version']!=ROUTING_VERSION or hashlib.sha256(Path(a['path']).read_bytes()).hexdigest()!=a['sha256']:raise ValueError('Non-learned routing identity mismatch')
            if a.get('fitted_observations')!=0:raise ValueError('Non-learned routing cannot contain fitted observations')
        else:validate_artifact(a,m['permitted_cutoffs'][role])
    if not m['artifacts']:raise ValueError('Empty fitted provenance')

def validate_event(timestamp, slot_start, slot_end):
    if not aware(slot_start)<=aware(timestamp)<aware(slot_end):raise ValueError('Realized event outside scheduled slot')
