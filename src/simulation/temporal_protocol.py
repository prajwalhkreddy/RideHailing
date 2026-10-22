"""Minimal shared final-experiment time and initialization guards."""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'config/final_temporal_protocol.json'

def protocol():
    return json.loads(CONFIG.read_text())

def aligned_timestamp(value):
    t=pd.Timestamp(value)
    if pd.isna(t) or t.tz is not None or t!=t.floor('30min'):
        raise ValueError('Aligned timezone-naive slot timestamp required.')
    return t

def training_update_allowed(timestamp):
    t=aligned_timestamp(timestamp);p=protocol()
    return pd.Timestamp(p['cnn_train_start'])<=t<=pd.Timestamp(p['training_cutoff'])

def is_final_evaluation(timestamp):
    t=aligned_timestamp(timestamp);p=protocol()
    return pd.Timestamp(p['final_eval_start'])<=t<=pd.Timestamp(p['final_eval_end'])

def assert_training_update_allowed(timestamp,*,evaluation_only=False):
    if evaluation_only or not training_update_allowed(timestamp):
        raise ValueError('Final temporal protocol prohibits model/FedAvg updates for this slot or evaluation mode.')

def assert_final_training_checkpoint(path):
    forbidden=(ROOT/protocol()['quarantined_checkpoint']).resolve()
    if Path(path).resolve()==forbidden:
        raise ValueError('DO_NOT_CONTINUE_FOR_FINAL_EXPERIMENTS: integration-only checkpoint.')
