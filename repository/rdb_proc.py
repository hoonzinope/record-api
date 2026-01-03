# game_record table logic
from sqlalchemy import create_engine, text
from model.game_record import GameRecord
from env import Env

class RDBProc:
    def __init__(self):
        # Initialize database connection here
        self.config = Env()
        self.DB_URL = f"mysql+pymysql://{self.config.DB_USER}:{self.config.DB_PASSWORD}@{self.config.DB_HOST}:{self.config.DB_PORT}/{self.config.DB_NAME}"
        self.engine = create_engine(self.DB_URL)
        self._disposed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    def close_connection(self):
        if not self._disposed:
            self.engine.dispose()
            self._disposed = True

    # insert game record
    def insert_game_record(self, record: GameRecord) -> int:
        insert_query = text("""
            INSERT INTO game_records
            (game_name, level, user_uuid, nickname, clear_time, mistake_count, hint_count, is_verified, user_ip)
            VALUES
            (:game_name, :level, :user_uuid, :nickname, :clear_time, :mistake_count, :hint_count, :is_verified, :user_ip)
        """)
        params = {
            "game_name": record.game_name,
            "level": record.level,
            "user_uuid": record.user_uuid,
            "nickname": record.nickname,
            "clear_time": record.clear_time,
            "mistake_count": record.mistake_count,
            "hint_count": record.hint_count,
            "is_verified": record.is_verified,
            "user_ip": record.user_ip,
        }
        with self.engine.begin() as conn:
            result = conn.execute(insert_query, params)
            record_id = result.lastrowid
        return int(record_id) if record_id is not None else 0

    # get ranking by game name and level
    def get_ranking(self, game_name: str, level: str, limit: int = 10) -> list[GameRecord]:
        # Retrieve the top 'limit' rankings for the specified game and level
        select_query = text(f"""
            SELECT * FROM game_records
            WHERE game_name = :game_name AND level = :level AND is_verified = TRUE
            ORDER BY clear_time ASC, mistake_count ASC, hint_count ASC
            LIMIT :limit
        """)
        params = {
            "game_name": game_name,
            "level": level,
            "limit": limit
        }

        result = []
        for row_data in self.select_query(select_query, params):
            result.append(GameRecord(**row_data))
        return result

    # get history by nickname
    def get_history_by_user_uuid(self, game_name: str, level: str, user_uuid: str, limit: int = 10) -> list[GameRecord]:
        # Retrieve recent records for a user and game/level
        select_query = text(f"""
            SELECT * FROM game_records
            WHERE game_name = :game_name AND level = :level AND user_uuid = :user_uuid
            ORDER BY insert_ts DESC
            LIMIT :limit
        """)
        params = {
            "game_name": game_name,
            "level": level,
            "user_uuid": user_uuid,
            "limit": limit
        }

        result = []
        for row_data in self.select_query(select_query, params):
            result.append(GameRecord(**row_data))
        return result

    def update_nickname(self, user_uuid: str, nickname: str) -> None:
        update_query = text("""
            UPDATE game_records
            SET nickname = :nickname
            WHERE user_uuid = :user_uuid
        """)
        with self.engine.begin() as conn:
            conn.execute(update_query, {"nickname": nickname, "user_uuid": user_uuid})

    def select_query(self, query: str, params: dict = {}) -> list[dict]:
        with self.engine.begin() as conn:
            result = conn.execute(text(query), params)
            records = [dict(row) for row in result]
            return records
