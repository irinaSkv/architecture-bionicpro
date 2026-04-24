INSERT INTO stg_telemetry
(event_ts, client_id, prosthesis_id, reaction_time_ms, battery_level, error_code)
VALUES ('2024-12-01T10:00:00', 1, 101, 80, 87, NULL);
INSERT INTO stg_telemetry
(event_ts, client_id, prosthesis_id, reaction_time_ms, battery_level, error_code)
VALUES ('2024-12-01T10:00:10', 1, 101, 95, 85, 'ERR_TIMEOUT');
INSERT INTO stg_telemetry
(event_ts, client_id, prosthesis_id, reaction_time_ms, battery_level, error_code)
VALUES ('2024-12-01T11:05:00', 2, 102, 90, 76, NULL);
INSERT INTO stg_telemetry
(event_ts, client_id, prosthesis_id, reaction_time_ms, battery_level, error_code)
VALUES ('2024-12-02T09:30:00', 1, 101, 70, 90, NULL);
INSERT INTO stg_telemetry
(event_ts, client_id, prosthesis_id, reaction_time_ms, battery_level, error_code)
VALUES ('2024-12-02T12:00:00', 3, 201, 85, 65, 'ERR_SIGNAL');