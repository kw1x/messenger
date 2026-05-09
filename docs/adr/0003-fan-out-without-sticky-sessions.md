# 3. Real-time fan-out without sticky sessions

- **Status**: accepted
- **Date**: 2026-04-29

## Context

A user with multiple devices may be connected to different
`presence-gateway` replicas. When a new message lands in
`chat.messages.v1`, every recipient's socket must receive it,
regardless of which replica holds it. The naïve approach — a single
shared consumer group — would deliver each message to exactly one
replica, missing recipients connected elsewhere. Sticky sessions are
fragile, expensive (load balancer state) and break horizontal scaling.

## Decision

Each gateway replica subscribes to `chat.messages.v1` with a
**unique consumer group**: `presence-gateway.<hostname>-<pid>`.

- Every replica receives every message.
- Each replica iterates `MessageCreated.member_ids` and pushes only to
  sockets it actually holds (lookup in a local `defaultdict`).
- `MessageDelivered` is emitted on the spot when a replica successfully
  writes to a socket — that's the source of truth for delivery.

## Consequences

- Bandwidth scales with the number of replicas (every replica reads the
  full topic). For our throughput target this is negligible.
- No coordination service, no Redis pub/sub, no sticky sessions, no
  consistent-hash router.
- Member IDs are denormalised into the event payload itself so the
  gateway never has to read from Postgres. The chat list is small and
  changes rarely; the trade-off is favourable.
