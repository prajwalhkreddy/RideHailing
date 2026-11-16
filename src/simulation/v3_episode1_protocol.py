"""Explicit Episode-1-only execution protocol; no future episode schedule."""
from datetime import datetime, timedelta
START=datetime(2026,3,1)
TIMESTAMPS=tuple(START+timedelta(minutes=30*i) for i in range(16))
def assert_slot(timestamp,index):
    if not 0<=index<16 or timestamp!=TIMESTAMPS[index]:
        raise ValueError('Outside frozen Episode-1 window')
def update_after_slot(runtime):
    if runtime.checkpoint_phase!='POST_SLOT_COMMIT':
        raise ValueError('Updates require completed slot')
    assert_slot(runtime.engine.timestamp-timedelta(minutes=30),runtime.slots-1)
    if len(runtime.learner.replay)<1000:return []
    before=runtime.learner.training_steps
    losses=[runtime.learner.train_step() for _ in range(8)]
    if any(x is None for x in losses) or runtime.learner.training_steps!=before+8:
        raise ValueError('Exactly eight warm-slot updates required')
    return losses
