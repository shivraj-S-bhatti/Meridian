CREATE TABLE IF NOT EXISTS url_queue (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    company_id TEXT,
    scheduled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    attempts INT NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_url_queue_status_scheduled
    ON url_queue(status, scheduled_at);

CREATE TABLE IF NOT EXISTS worker_heartbeats (
    worker_id TEXT PRIMARY KEY,
    last_seen TIMESTAMPTZ NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS raw_pages (
    id BIGSERIAL,
    company_id TEXT,
    url TEXT NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    content_hash TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (id, fetched_at)
) PARTITION BY RANGE (fetched_at);

CREATE TABLE IF NOT EXISTS raw_pages_default
    PARTITION OF raw_pages
    DEFAULT;

CREATE TABLE IF NOT EXISTS facts (
    id BIGSERIAL,
    company_id TEXT NOT NULL,
    source_url TEXT NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL,
    node_type TEXT NOT NULL,
    normalized_fact TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    extractor_version TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (id, captured_at)
) PARTITION BY RANGE (captured_at);

CREATE TABLE IF NOT EXISTS facts_default
    PARTITION OF facts
    DEFAULT;

CREATE INDEX IF NOT EXISTS idx_facts_company_captured
    ON facts(company_id, captured_at DESC);

CREATE TABLE IF NOT EXISTS contradictions (
    id BIGSERIAL PRIMARY KEY,
    company_id TEXT NOT NULL,
    as_of_ts TIMESTAMPTZ NOT NULL,
    contradiction_score DOUBLE PRECISION NOT NULL,
    novelty_score DOUBLE PRECISION NOT NULL,
    rationale JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS signal_cards (
    id BIGSERIAL PRIMARY KEY,
    company_id TEXT NOT NULL,
    as_of_ts TIMESTAMPTZ NOT NULL,
    horizon_days INT NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    uncertainty DOUBLE PRECISION NOT NULL,
    decay_half_life_days DOUBLE PRECISION NOT NULL,
    drivers JSONB NOT NULL,
    invalid_if JSONB NOT NULL,
    evidence_graph_id TEXT NOT NULL,
    lineage_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_signal_cards_unique
    ON signal_cards(company_id, as_of_ts, horizon_days);

CREATE TABLE IF NOT EXISTS run_lineage (
    lineage_hash TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    as_of_ts TIMESTAMPTZ NOT NULL,
    pipeline_version TEXT NOT NULL,
    agent_versions JSONB NOT NULL,
    evidence_node_count INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
