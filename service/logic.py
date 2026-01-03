# service to handle business logic
from repository.rdb_proc import RDBProc
from repository.kv_proc import KvProc
from utils.verifier.registry import get_verifier

class GameService:
    def __init__(self):
        pass

    def add_game_record(self, record, verification_payload: dict) -> tuple[int, bool]:
        # Business logic before inserting a game record
        if record.clear_time <= 0:
            raise ValueError("Clear time cannot be negative")
        if record.mistake_count < 0 or record.hint_count < 0:
            raise ValueError("Counts must be non-negative")

        is_verified = self.verify_record(record, verification_payload)
        record.is_verified = is_verified

        with RDBProc() as rdb_proc:
            record_id = rdb_proc.insert_game_record(record)
        if is_verified:
            with KvProc() as kv_proc:
                kv_proc.insert_game_record(record)
        return record_id, is_verified

    def update_nickname(self, user_uuid: str, nickname: str) -> None:
        if not nickname:
            raise ValueError("Nickname is required")
        with RDBProc() as rdb_proc:
            rdb_proc.update_nickname(user_uuid, nickname)

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
        if not action_log or len(action_log) > 10:
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
        return duration_ms <= clear_time * 1000
