# service to handle business logic
import time

from repository.rdb_proc import RDBProc
from repository.kv_proc import KvProc
from utils.verifier.registry import get_verifier

class ConnService:
    def __init__(self):
        pass

    def ping(self) -> dict[str, bool]:
        result = {"rdb": False, "kv": False}
        try:
            with RDBProc() as rdb_proc:
                rdb_status = rdb_proc.ping()
                result.update({"rdb": rdb_status})
        except Exception:
            result.update({"rdb": False})
        try:
            with KvProc() as kv_proc:
                kv_status = kv_proc.ping()
                result.update({"kv": kv_status})
        except Exception:
            result.update({"kv": False})
        return result

GAME_WHITELIST = {
    "sudoku": {"easy", "medium", "hard", "expert"},
    "killer-sudoku": {"easy", "medium", "hard", "expert"},
    "shikaku": {"easy", "medium"},
    "hidato": {"size-5", "size-7"},
    "nonogram": {"size-5", "size-10", "size-15"},
    "2048": {"size-3", "size-4", "size-5", "size-6", "size-8"},
    "solitaire": {"classic", "draw3"},
    "shanghai": {"mobile", "desktop"},
    "mahjong": {"16x10", "6x10"}
}

class GameService:
    def __init__(self):
        pass

    def add_game_record(self, record, verification_payload: dict) -> tuple[int, bool]:
        # Business logic before inserting a game record
        if record.clear_time <= 0:
            raise ValueError("Clear time cannot be negative")
        if record.mistake_count < 0 or record.hint_count < 0:
            raise ValueError("Counts must be non-negative")

        valid_levels = GAME_WHITELIST.get(record.game_name)
        if valid_levels is None or record.level not in valid_levels:
            raise ValueError(f"Invalid game_name or level: {record.game_name} / {record.level}")

        if not self._is_session_valid(record.game_name, record.level, record.user_uuid, record.clear_time):
            return 0, False

        is_verified = self.verify_record(record, verification_payload)
        record.is_verified = is_verified
        if not is_verified:
            return 0, False

        with RDBProc() as rdb_proc:
            record_id = rdb_proc.insert_game_record(record)
        with KvProc() as kv_proc:
            kv_proc.insert_game_record(record)
        return record_id, is_verified

    def start_session(self, game_name: str, level: str, user_uuid: str) -> None:
        with KvProc() as kv_proc:
            kv_proc.insert_game_session(game_name, level, user_uuid)

    def _is_session_valid(self, game_name: str, level: str, user_uuid: str, clear_time: int) -> bool:
        with KvProc() as kv_proc:
            start_time = kv_proc.get_game_session_start(game_name, level, user_uuid)
        if start_time is None:
            return False
        elapsed_seconds = int(time.time()) - start_time
        return elapsed_seconds >= clear_time

    def update_nickname(self, user_uuid: str, nickname: str) -> None:
        if not nickname:
            raise ValueError("Nickname is required")
        with RDBProc() as rdb_proc:
            rdb_proc.update_nickname(user_uuid, nickname)
        with KvProc() as kv_proc:
            kv_proc.update_nickname(user_uuid, nickname)

    def get_user_history(self, game_name: str, level: str, user_uuid: str, limit: int = 10):
        if limit <= 0:
            raise ValueError("Limit must be a positive integer")
        with RDBProc() as rdb_proc:
            return rdb_proc.get_history_by_user_uuid(game_name, level, user_uuid, limit)

    def get_top_rankings(self, game_name, level, limit=10):
        # Business logic before retrieving rankings
        if limit <= 0:
            raise ValueError("Limit must be a positive integer")
        with KvProc() as kv_proc:
            records = kv_proc.get_ranking(game_name, level, limit)
        if records:
            return records
        with RDBProc() as rdb_proc:
            records = rdb_proc.get_ranking(game_name, level, limit)
        if records:
            with KvProc() as kv_proc:
                kv_proc.insert_game_records(records)
        return records

    def verify_record(self, record, payload: dict) -> bool:
        action_log = payload.get("action_log", [])
        if not self._validate_action_log(action_log, record.clear_time):
            return False

        wrong_answers = payload.get("wrong_answers", [])
        hint_events = payload.get("hint_events", [])
        if len(wrong_answers) != record.mistake_count:
            return False
        if len(hint_events) != record.hint_count:
            return False

        verifier = get_verifier(record.game_name)
        return verifier.verify(payload)

    @staticmethod
    def _validate_action_log(action_log: list[dict], clear_time: int) -> bool:
        if not action_log:
            return False
        if len(action_log) < 2:
            return False
        
        previous_ts = None
        for entry in action_log:
            ts = entry.get("ts")
            if ts is None:
                return False
            if previous_ts is not None and ts < previous_ts:
                return False
            previous_ts = ts
            
        duration_ms = action_log[-1]["ts"] - action_log[0]["ts"]
        if duration_ms < 0:
            return False
        if duration_ms < 1000: # Minimum 1 second
            return False
            
        return duration_ms <= (clear_time + 5) * 1000 # Allow 5s buffer
