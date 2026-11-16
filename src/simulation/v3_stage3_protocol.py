"""Approved Episodes 11–25 segmentation; never reset physical/learning state."""
from datetime import datetime,timedelta
def timestamps(episode):
    if not 11<=episode<=25:raise ValueError('Only Episodes 11–25 authorized')
    start=datetime(2026,3,1)+timedelta(hours=8*(episode-1))
    return tuple(start+timedelta(minutes=30*i) for i in range(16))
def begin_episode(r,episode):
    expected=timestamps(episode)[0]
    if r.episode!=episode-1 or r.slots!=16 or r.checkpoint_phase!='POST_SLOT_COMMIT':raise ValueError('Previous episode not complete')
    if r.engine.timestamp!=expected or r.engine.clock!=expected or r.engine.slot_index!=16*(episode-1):raise ValueError('Continuation cursor mismatch')
    # Only segment metadata changes; cumulative engine/audits/replay are retained.
    r.episode=episode;r.slots=0
    r.checkpoint_phase='EPISODE_BOUNDARY'
def update_after_slot(r):
    if r.checkpoint_phase!='POST_SLOT_COMMIT' or not 1<=r.slots<=16:raise ValueError('Incomplete slot')
    if r.engine.timestamp!=timestamps(r.episode)[r.slots-1]+timedelta(minutes=30):raise ValueError('Wrong training window')
    if len(r.learner.replay)<1000:return []
    before=r.learner.training_steps
    losses=[r.learner.train_step() for _ in range(8)]
    if any(x is None for x in losses) or r.learner.training_steps!=before+8:raise ValueError('Incorrect update count')
    return losses
