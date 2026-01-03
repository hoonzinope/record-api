from typing import Any, List, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from model.game_record import GameRecord
from service.logic import GameService
from utils.generate_uuid import GenerateUUID

app = FastAPI()
service = GameService()


class ActionLogEntry(BaseModel):
    ts: int = Field(..., description="Unix epoch milliseconds")
    action: str
    payload: Optional[dict[str, Any]] = None


class RecordCreateRequest(BaseModel):
    game_name: str
    level: str
    user_uuid: str
    nickname: Optional[str] = None
    clear_time: int = Field(..., gt=0)
    mistake_count: int = Field(0, ge=0)
    hint_count: int = Field(0, ge=0)
    answers: List[dict[str, Any]] = Field(default_factory=list)
    wrong_answers: List[dict[str, Any]] = Field(default_factory=list)
    hint_events: List[dict[str, Any]] = Field(default_factory=list)
    action_log: List[ActionLogEntry] = Field(default_factory=list)


class NicknameUpdateRequest(BaseModel):
    nickname: str


def record_to_dict(record: GameRecord) -> dict:
    return {
        "record_id": record.id or 0,
        "game_name": record.game_name,
        "level": record.level,
        "user_uuid": record.user_uuid,
        "nickname": record.nickname,
        "clear_time": record.clear_time,
        "mistake_count": record.mistake_count,
        "hint_count": record.hint_count,
        "is_verified": record.is_verified,
        "insert_ts": record.insert_ts,
    }


@app.get("/record/health")
def health_check():
    return {"status": "ok"}


@app.get("/record/user")
def get_user():
    generate_uuid = GenerateUUID()
    uuid = generate_uuid.get()
    nickname = uuid[0:8]
    return {"user_uuid": uuid, "nickname": nickname}


@app.patch("/record/user/{user_uuid}")
def update_nickname(user_uuid: str, payload: NicknameUpdateRequest):
    try:
        service.update_nickname(user_uuid, payload.nickname)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"user_uuid": user_uuid, "nickname": payload.nickname}


@app.post("/record")
def insert_game_record(payload: RecordCreateRequest, request: Request):
    user_ip = request.client.host if request.client else ""
    nickname = payload.nickname or "Guest"
    record = GameRecord(
        game_name=payload.game_name,
        level=payload.level,
        user_uuid=payload.user_uuid,
        nickname=nickname,
        clear_time=payload.clear_time,
        mistake_count=payload.mistake_count,
        hint_count=payload.hint_count,
        user_ip=user_ip,
    )

    verification_payload = {
        "answers": payload.answers,
        "wrong_answers": payload.wrong_answers,
        "hint_events": payload.hint_events,
        "action_log": [entry.model_dump() for entry in payload.action_log],
    }

    try:
        record_id, is_verified = service.add_game_record(record, verification_payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"record_id": record_id, "status": "success", "is_verified": is_verified}


@app.get("/record/history/{game_name}/{level}/{user_uuid}")
def get_user_history(game_name: str, level: str, user_uuid: str, limit: int = 10):
    try:
        records = service.get_user_history(game_name, level, user_uuid, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [record_to_dict(record) for record in records]


@app.get("/record/ranking/{game_name}/{level}")
def get_ranking(game_name: str, level: str, limit: int = 10):
    try:
        records = service.get_top_rankings(game_name, level, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    ranking = []
    for index, record in enumerate(records, start=1):
        ranking.append(
            {
                "rank": index,
                "user_uuid": record.user_uuid,
                "nickname": record.nickname,
                "clear_time": record.clear_time,
                "mistake_count": record.mistake_count,
                "hint_count": record.hint_count,
            }
        )
    return ranking
