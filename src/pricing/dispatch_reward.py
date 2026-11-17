"""Master Eq.(3) reward only; no change to destination-context decisions."""
import math

REWARD_VERSION = "SUCCESSFUL_DISPATCH_REWARD_V1"


def reconcile_dispatch_rewards(rows, contexts):
    """Return per-request and per-context rewards, rejecting contradictory audits."""
    totals = {context: 0.0 for context in contexts}
    contributions = []
    seen = set()
    for row in rows:
        identity = (row['slot'], row['request_id'])
        if identity in seen:
            raise ValueError('Duplicate request reward')
        seen.add(identity)
        context = row['destination_context']
        if context not in totals:
            raise ValueError('Unknown reward context')
        outcome = row['dispatch_outcome']
        if outcome not in {'PASSENGER_REJECTED', 'ACCEPTED_BUT_UNMATCHED', 'ACCEPTED_AND_ASSIGNED'}:
            raise ValueError('Unknown dispatch outcome')
        if bool(row['accepted']) != (outcome != 'PASSENGER_REJECTED'):
            raise ValueError('Acceptance/dispatch contradiction')
        fare = float(row['P_offer'])
        if not math.isfinite(fare) or fare < 0:
            raise ValueError('Invalid offered fare')
        reward = fare if outcome == 'ACCEPTED_AND_ASSIGNED' else 0.0
        contributions.append(reward)
        totals[context] += reward
    return contributions, totals
