DROP TABLE IF EXISTS stg_crm_clients;
CREATE TABLE stg_crm_clients
(
    client_id       BIGINT PRIMARY KEY,
    full_name       TEXT,
    email           TEXT,
    country         TEXT,
    city            TEXT,
    prosthesis_id   BIGINT,
    activation_date DATE
);

DROP TABLE IF EXISTS stg_telemetry;
CREATE TABLE stg_telemetry
(
    event_id         BIGSERIAL PRIMARY KEY,
    event_ts         TIMESTAMP,
    client_id        BIGINT,
    prosthesis_id    BIGINT,
    reaction_time_ms INT,
    battery_level    INT,
    error_code       TEXT
);

DROP TABLE IF EXISTS mart_user_telemetry_daily;
CREATE TABLE mart_user_telemetry_daily
(
    client_id         BIGINT,
    report_date       DATE,
    full_name         TEXT,
    email             TEXT,
    country           TEXT,
    city              TEXT,
    prosthesis_id     BIGINT,
    activation_date   DATE,
    total_events      INT,
    avg_reaction_ms   NUMERIC,
    p95_reaction_ms   NUMERIC,
    avg_battery_level NUMERIC,
    errors_count      INT,
    last_event_ts     TIMESTAMP,
    PRIMARY KEY (client_id, report_date)
);

CREATE INDEX IF NOT EXISTS idx_mart_user_telemetry_daily_client
    ON mart_user_telemetry_daily (client_id);