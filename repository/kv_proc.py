# game_record redis proc
import json
import time

import redis

from env import Env
from model.game_record import GameRecord

class KvProc:
    def __init__(self) -> None:
        self.config = Env()
        self.redis = redis.Redis(
            host=self.config.REDIS_HOST,
            port=self.config.REDIS_PORT,
            db=0,
            decode_responses=True,  # 문자열로 자동 변환
        )
        self._disposed = False

    def __enter__(self) -> "KvProc":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        if not self._disposed:
            self.redis.close()
            self._disposed = True

    def ping(self) -> bool:
        return bool(self.redis.ping())

    # game record save for top ranking
    def insert_game_record(self, record: GameRecord) -> None:
        if not record.is_verified:
            return
        key = f"ranking:{record.game_name}:{record.level}"
        member = self._encode_member(record)
        score = record.clear_time
        self.redis.zadd(key, {member: score})

    def insert_game_records(self, records: list[GameRecord]) -> None:
        if not records:
            return
        pipeline = self.redis.pipeline()
        for record in records:
            if not record.is_verified:
                continue
            key = f"ranking:{record.game_name}:{record.level}"
            member = self._encode_member(record)
            score = record.clear_time
            pipeline.zadd(key, {member: score})
        pipeline.execute()

    # get ranking by game name and level
    def get_ranking(self, game_name: str, level: str, limit: int = 10) -> list[GameRecord]:
        key = f"ranking:{game_name}:{level}"
        raw_rankings = self.redis.zrange(key, 0, -1, withscores=False)

        result = []
        for raw in raw_rankings:
            record = self._decode_member(raw, game_name, level)
            if not record or not record.is_verified:
                continue
            result.append(record)
            result.append(record)
        
        if game_name in ['woodoku', '2048']:
            result.sort(key=lambda item: item.score, reverse=True)
        else:
            result.sort(key=lambda item: (item.clear_time, item.mistake_count, item.hint_count))
            
        return result[:limit]

    @staticmethod
    def _encode_member(record: GameRecord) -> str:
        payload = {
            "user_uuid": record.user_uuid,
            "nickname": record.nickname,
            "clear_time": record.clear_time,
            "mistake_count": record.mistake_count,
            "hint_count": record.hint_count,
            "is_verified": record.is_verified,
            "is_verified": record.is_verified,
            "user_ip": record.user_ip,
            "score": record.score,
        }
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=True)

    @staticmethod
    def _decode_member(raw: str, game_name: str, level: str) -> GameRecord | None:
        raw = raw.strip()
        if raw.startswith("{"):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return None
            clear_time = KvProc._safe_int(data.get("clear_time"))
            mistake_count = KvProc._safe_int(data.get("mistake_count"))
            hint_count = KvProc._safe_int(data.get("hint_count"))
            score = KvProc._safe_int(data.get("score"))
            if score is None:
                score = 0
            if clear_time is None or mistake_count is None or hint_count is None:
                return None
            return GameRecord(
                game_name=game_name,
                level=level,
                user_uuid=str(data.get("user_uuid", "")),
                nickname=str(data.get("nickname", "")),
                clear_time=clear_time,
                mistake_count=mistake_count,
                hint_count=hint_count,
                is_verified=bool(data.get("is_verified", False)),
                user_ip=str(data.get("user_ip", "")),
                score=score,
            )

        # Backward compatibility for old "colon-joined" members.
        try:
            user_uuid, nickname, clear_time, mistake_count, hint_count, is_verified, user_ip = raw.split(":")
        except ValueError:
            return None
        clear_time_value = KvProc._safe_int(clear_time)
        mistake_count_value = KvProc._safe_int(mistake_count)
        hint_count_value = KvProc._safe_int(hint_count)
        if clear_time_value is None or mistake_count_value is None or hint_count_value is None:
            return None
        return GameRecord(
            game_name=game_name,
            level=level,
            user_uuid=user_uuid,
            nickname=nickname,
            clear_time=clear_time_value,
            mistake_count=mistake_count_value,
            hint_count=hint_count_value,
            is_verified=is_verified == "True",
            user_ip=user_ip,
        )

    @staticmethod
    def _safe_int(value) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def update_nickname(self, user_uuid: str, nickname: str) -> None:
        cursor = 0
        while True:
            cursor, keys = self.redis.scan(cursor=cursor, match="ranking:*", count=100)
            for key in keys:
                parts = key.split(":", 2)
                if len(parts) != 3:
                    continue
                game_name, level = parts[1], parts[2]
                entries = self.redis.zrange(key, 0, -1, withscores=True)
                if not entries:
                    continue
                pipe = self.redis.pipeline()
                updated = False
                for raw, score in entries:
                    record = self._decode_member(raw, game_name, level)
                    if not record or record.user_uuid != user_uuid:
                        continue
                    record.nickname = nickname
                    member = self._encode_member(record)
                    pipe.zadd(key, {member: score})
                    pipe.zrem(key, raw)
                    updated = True
                if updated:
                    pipe.execute()
            if cursor == 0:
                break

    def insert_game_session(self, game_name: str, level: str, user_uuid: str) -> None:
        key = f"session:{game_name}:{level}:{user_uuid}"
        start_time = f"{int(time.time())}"
        self.redis.set(key, start_time, ex=3600)  # 세션 유효기간 1시간

    def check_game_session(self, game_name: str, level: str, user_uuid: str) -> bool:
        key = f"session:{game_name}:{level}:{user_uuid}"
        if self.redis.exists(key):
            return True
        return False

    def get_game_session_start(self, game_name: str, level: str, user_uuid: str) -> int | None:
        key = f"session:{game_name}:{level}:{user_uuid}"
        value = self.redis.get(key)
        if not value:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def renew_game_session(self, game_name: str, level: str, user_uuid: str) -> None:
        key = f"session:{game_name}:{level}:{user_uuid}"
        self.redis.expire(key, 3600)  # 세션 유효기간 1시간 연장
