# 2. Transactional outbox for Postgres → Kafka

- **Status**: accepted
- **Date**: 2026-04-29

## Context

When `chat-core` accepts a new message it must do two writes: insert the
row into `messages` and produce a `MessageCreated` event into Kafka. If
those two writes are independent, any partial failure (broker timeout
after a successful insert; process crash between insert and `send`)
leaves the system inconsistent.

A fancier alternative would be Kafka transactions across DB and broker
via `KAFKA_TRANSACTIONAL_ID` plus `commit_transaction`, but aiokafka
doesn't support that and it's operationally finicky.

## Decision

Use the transactional outbox pattern:

1. The HTTP request handler opens a single Postgres transaction, inserts
   the `Message` row and an `OutboxEvent` row, then commits.
2. A background `OutboxPublisher` polls `outbox_events` with
   `SELECT … FOR UPDATE SKIP LOCKED`, ships claimed rows to Kafka via
   the idempotent producer, and marks them published.
3. Several replicas can run the publisher safely — `SKIP LOCKED` makes
   them work-stealing.

## Consequences

- Postgres becomes the source of truth for "did this message exist".
  Kafka is an at-least-once mirror.
- Consumers must be idempotent. They already need to be, because Kafka
  itself can re-deliver during rebalance.
- A short publishing lag is possible under publisher backpressure, but
  the steady-state latency is one poll interval (50 ms by default).
