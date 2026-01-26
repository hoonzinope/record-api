from dataclasses import dataclass
from typing import Optional

@dataclass
class GameRecord:
    id: Optional[int] = None
    game_name: str = ""
    level: str = ""
    user_uuid: str = ""
    nickname: str = ""
    clear_time: int = 0
    score: int = 0
    mistake_count: int = 0
    hint_count: int = 0
    is_verified: bool = False
    user_ip: str = ""
    insert_ts: Optional[str] = None
    # Optional field for logging actions related to the game record (not in DB)
    action_log: str = ""

# -- game_record table
# CREATE TABLE game_records (
#     id BIGINT AUTO_INCREMENT PRIMARY KEY,
#     game_name VARCHAR(50) NOT NULL,
#     level VARCHAR(20) NOT NULL,
#     user_uuid VARCHAR(100) NOT NULL,
#     nickname VARCHAR(50) DEFAULT 'Guest',
#     clear_time INT NOT NULL,
#     mistake_count INT DEFAULT 0,
#     hint_count INT DEFAULT 0,
#     is_verified BOOLEAN DEFAULT FALSE,
#     user_ip VARCHAR(45),
#     insert_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     INDEX idx_ranking (game_name, level, is_verified, clear_time) -- 랭킹 조회 최적화 (mistake, hint 의 경우, 정렬 조건에 추가)
# );
