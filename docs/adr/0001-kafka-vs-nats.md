# 1. Kafka over NATS as the message broker

- **Status**: accepted
- **Date**: 2026-04-29

## Context

We need a broker for two flows: in-process fan-out from `chat-core` to
WebSocket sessions held by `presence-gateway` replicas, and a durable
log of every chat message for future analytics, audit, and replay.

NATS JetStream and Apache Kafka were the two serious candidates.
JetStream is lighter to operate and has first-class request/reply, but
its log primitives are still maturing. Kafka has a mature ecosystem
(Kafka UI, MirrorMaker, ksqlDB, Debezium, every cloud-managed offering),
strong durability semantics, and is what most teams reach for when the
words *"event log"* come up in a sentence.

## Decision

Use Apache Kafka in KRaft mode (no ZooKeeper).

## Consequences

- We get a real, partitioned, replayable log out of the box. Adding a
  new consumer (analytics, search indexer, mobile push) is purely
  additive — no producer changes.
- Idempotent producers (`enable_idempotence=True`, `acks=all`) give us
  exactly-once semantics on the producer side, which dovetails with the
  transactional outbox pattern (ADR-0002).
- Operating Kafka is heavier than NATS — but a single-broker dev
  cluster fits in one container and the production story is well
  understood. For a learning/CV project that's a feature, not a bug.
