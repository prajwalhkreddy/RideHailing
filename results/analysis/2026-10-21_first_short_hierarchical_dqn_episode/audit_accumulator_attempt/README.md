# First short non-private hierarchical DQN episode

{
  "SHORT_HIERARCHICAL_EPISODE_READY": "NO",
  "slots_completed": 0,
  "blocker": "AssertionError: ",
  "optimizer_updates": 0,
  "replay_size": 331,
  "epsilon_start": 1.0,
  "epsilon_end": 1.0,
  "checkpoint": null,
  "elapsed_seconds": 39.98822808265686,
  "exact_reward_reconciliation": true,
  "checks": "Per completed slot: state/action/fare/acceptance finite; exact reward; prior dispatch; known incoming via runner; next states; fleet conservation; replay counts; operational fields; routing weights unchanged. Existing runner enforces active assignment conflicts and temporal sources.",
  "charging_events": [],
  "automatic_extension": false
}

Four-slot limit: March 16, 2026 00:00–02:00. Existing forecast-count and intact January empirical-trip generation, real epsilon-greedy actions, behavioural E acceptance and FCFS matching. No forced actions or replay prefill. Routing checkpoint frozen; no routing retraining or local updates supplied. Existing DQN warm-up and one training-step call per completed slot. Older blocked evidence is preserved in `blocked_attempt_before_himax_resolution/`.

CSV metrics describe completed and independently checked slots only. No automatic extension.
