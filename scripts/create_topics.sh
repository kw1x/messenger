#!/usr/bin/env bash
# Provision the topic catalogue declared in `hexachat_shared.kafka.topics`.
# Idempotent: re-running is a no-op if a topic already exists.
set -euo pipefail

BOOTSTRAP="${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}"
PARTITIONS="${KAFKA_TOPIC_PARTITIONS:-12}"
REPLICATION="${KAFKA_TOPIC_REPLICATION:-1}"

TOPICS=(
  "chat.messages.v1"
  "chat.receipts.v1"
  "presence.events.v1"
)

for topic in "${TOPICS[@]}"; do
  echo "→ ensuring topic ${topic}"
  kafka-topics \
    --bootstrap-server "${BOOTSTRAP}" \
    --create \
    --if-not-exists \
    --topic "${topic}" \
    --partitions "${PARTITIONS}" \
    --replication-factor "${REPLICATION}" \
    --config retention.ms=604800000 \
    --config compression.type=producer
done

echo "✓ topics ready"
kafka-topics --bootstrap-server "${BOOTSTRAP}" --list
