import os
from typing import Any, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from model.game_record import GameRecord
from service.logic import GameService, ConnService
from utils.generate_uuid import GenerateUUID

app = FastAPI()
service = GameService()
RECORD_API_KEY = os.getenv("RECORD_API_KEY", "")
ALLOWED_ORIGINS = {"https://urrrm.com", "https://www.urrrm.com"}
MAX_LIST_LEN = 1000
MAX_LIMIT = 50
MAX_NICKNAME_LEN = 20
MAX_GAME_NAME_LEN = 32
MAX_LEVEL_LEN = 20
MAX_USER_UUID_LEN = 64


def _is_safe_slug(value: str, max_len: int) -> bool:
    if not value or len(value) > max_len:
        return False
    for ch in value:
        if not (ch.isalnum() or ch in ("-", "_")):
            return False
    return True


def verify_request(request: Request, x_record_key: Optional[str] = Header(default=None, alias="X-Record-Key")):
    if RECORD_API_KEY:
        if not x_record_key or x_record_key != RECORD_API_KEY:
            raise HTTPException(status_code=403, detail="Unauthorized")
    origin = request.headers.get("origin")
    if origin and origin not in ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail="Forbidden origin")


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


class SessionCreateRequest(BaseModel):
    game_name: str
    level: str
    user_uuid: str


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
def health_check(key: Optional[str] = None):
    if key != "health_8f3c9b2a":
        raise HTTPException(status_code=403, detail="Forbidden")
    #check database connection
    conn_service = ConnService()
    ping = conn_service.ping()
    return {"status": "ok", "ping" : ping}


@app.get("/record/user")
def get_user(_: None = Depends(verify_request)):
    generate_uuid = GenerateUUID()
    uuid = generate_uuid.get()
    nickname = uuid[0:8]
    return {"user_uuid": uuid, "nickname": nickname}


@app.post("/record/session")
def create_session(payload: SessionCreateRequest, _: None = Depends(verify_request)):
    if not _is_safe_slug(payload.game_name, MAX_GAME_NAME_LEN):
        raise HTTPException(status_code=400, detail="Invalid game name")
    if not _is_safe_slug(payload.level, MAX_LEVEL_LEN):
        raise HTTPException(status_code=400, detail="Invalid level")
    if not payload.user_uuid or len(payload.user_uuid) > MAX_USER_UUID_LEN:
        raise HTTPException(status_code=400, detail="Invalid user UUID")
    service.start_session(payload.game_name, payload.level, payload.user_uuid)
    return {"status": "ok"}


@app.patch("/record/user/{user_uuid}")
def update_nickname(user_uuid: str, payload: NicknameUpdateRequest, _: None = Depends(verify_request)):
    if not payload.nickname or len(payload.nickname) > MAX_NICKNAME_LEN:
        raise HTTPException(status_code=400, detail="Invalid nickname")
    try:
        service.update_nickname(user_uuid, payload.nickname)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"user_uuid": user_uuid, "nickname": payload.nickname}


@app.post("/record")
def insert_game_record(payload: RecordCreateRequest, request: Request, _: None = Depends(verify_request)):
    if not _is_safe_slug(payload.game_name, MAX_GAME_NAME_LEN):
        raise HTTPException(status_code=400, detail="Invalid game name")
    if not _is_safe_slug(payload.level, MAX_LEVEL_LEN):
        raise HTTPException(status_code=400, detail="Invalid level")
    if not payload.user_uuid or len(payload.user_uuid) > MAX_USER_UUID_LEN:
        raise HTTPException(status_code=400, detail="Invalid user UUID")
    if payload.nickname and len(payload.nickname) > MAX_NICKNAME_LEN:
        raise HTTPException(status_code=400, detail="Invalid nickname")
    if len(payload.answers) > MAX_LIST_LEN:
        raise HTTPException(status_code=400, detail="Answers list too large")
    if len(payload.wrong_answers) > MAX_LIST_LEN:
        raise HTTPException(status_code=400, detail="Wrong answers list too large")
    if len(payload.hint_events) > MAX_LIST_LEN:
        raise HTTPException(status_code=400, detail="Hint events list too large")
    if len(payload.action_log) > MAX_LIST_LEN:
        raise HTTPException(status_code=400, detail="Action log too large")
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

    status = "success" if record_id else "rejected"
    return {"record_id": record_id, "status": status, "is_verified": is_verified}


@app.get("/record/history/{game_name}/{level}/{user_uuid}")
def get_user_history(
    game_name: str,
    level: str,
    user_uuid: str,
    limit: int = 10,
    _: None = Depends(verify_request),
):
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT
    try:
        records = service.get_user_history(game_name, level, user_uuid, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [record_to_dict(record) for record in records]


@app.get("/record/ranking/{game_name}/{level}")
def get_ranking(game_name: str, level: str, limit: int = 10, _: None = Depends(verify_request)):
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT
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
