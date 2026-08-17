CREATE TABLE IF NOT EXISTS production_events
(
    occurred_at DateTime64(3, 'UTC'),
    run_id String,
    project_id String,
    stage LowCardinality(String),
    event_type LowCardinality(String),
    attributes_json String
)
ENGINE = MergeTree
ORDER BY (project_id, run_id, occurred_at)
TTL occurred_at + INTERVAL 90 DAY DELETE;
