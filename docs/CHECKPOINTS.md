# Agent checkpoints

Status: accepted recovery approach; the wire schema and implementation are pending.

## In simple terms

A checkpoint is a save point for an investigation. The SDK is the helper library
developers use to connect their agent to Strange Physics. After an experiment,
the SDK stores the agent's declared working state and references to the recorded
observations and model artifacts.

If checkpoint 17 is saved and the worker crashes, a replacement worker can load
that checkpoint and continue with experiment 18. The agent developer must say
what working state to save. A checkpoint does not automatically capture every
Python variable or an entire running process.

## What must survive

- Run identity, schema version, agent package/version and immutable runtime image.
- The last committed experiment and a cursor into the durable event history.
- Agent-declared state, such as candidate hypotheses and fitting configuration.
- References and hashes for model artifacts and previously purchased observations.
- Random-generator state needed by the agent's supported replay contract.

The platform retains budgets and completed experiments independently of any
agent-provided checkpoint. Agent state cannot rewrite the budget, change a
recorded observation or reveal evaluator-only data. Provider credentials are
not checkpoint contents.

## Failure between an experiment and a checkpoint

Suppose experiment 17 committed, but the worker died before saving checkpoint 17.
The replacement restores checkpoint 16 and receives the already-recorded result
of experiment 17. Reprocessing that result must not run or charge for a second
logical physics experiment. The SDK uses durable operation identities to connect
restored work to existing records.

Model-provider calls have their own attempt and response records. An ambiguous
provider timeout can still incur cost. Checkpointing does not guarantee
exactly-once external billing or identical responses to a fresh model request.

## Storage contract to specify

Write required artifacts before publishing a checkpoint as complete. Commit the
checkpoint reference only after those artifacts are durable and identifiable by
hash. Restore a complete checkpoint or an earlier complete checkpoint; never
silently accept a partial one. Validate schema and runtime compatibility during
restore and expose a clear failure when migration is unsupported.

The trusted control plane treats agent state as untrusted data. It must not
deserialize executable Python objects supplied by an agent. Any necessary
agent-specific loading happens inside the agent's isolated runtime.

Explicit checkpoints preserve investigations across worker replacement. They do
not replace database backups, artifact retention or disaster recovery.
