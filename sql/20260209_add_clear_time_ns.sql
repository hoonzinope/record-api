ALTER TABLE game_records
    ADD COLUMN clear_time_ns BIGINT NOT NULL DEFAULT 1000000000 AFTER clear_time;

UPDATE game_records
SET clear_time_ns = clear_time * 1000000000
WHERE clear_time_ns IS NULL OR clear_time_ns <= 0;

CREATE INDEX idx_ranking_ns ON game_records (game_name, level, is_verified, clear_time_ns);
