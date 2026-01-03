# record service

웹 퍼즐 게임의 기록을 저장하고 조회하는 FastAPI 서비스입니다. MySQL에 기록을 저장하고,
검증된 기록만 Redis Sorted Set에 랭킹으로 적재합니다.

## 주요 구성
- `router/`: HTTP API 엔드포인트 (`router/controller.py`)
- `service/`: 비즈니스 로직 (`service/logic.py`)
- `repository/`: MySQL/Redis 데이터 접근 (`repository/rdb_proc.py`, `repository/kv_proc.py`)
- `model/`: 데이터 모델 (`model/game_record.py`)
- `utils/`: UUID 생성, 검증기 레지스트리/게임별 검증기

## 실행 환경
- Python 3.10.16
- FastAPI
- MySQL, Redis

## 로컬 실행
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn router.controller:app --reload --port 8888
```

## 환경 변수
`.env`에 다음 값을 설정합니다. 미설정 시 기본값이 사용됩니다.
- `DB_HOST` (기본: localhost)
- `DB_PORT` (기본: 3306)
- `DB_USER` (기본: root)
- `DB_PASSWORD` (기본: 1q2w3e4r!)
- `DB_NAME` (기본: PUZZLE)
- `REDIS_HOST` (기본: localhost)
- `REDIS_PORT` (기본: 6379)

## 데이터 저장 구조
MySQL 테이블: `game_records`
```sql
CREATE TABLE game_records (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    game_name VARCHAR(50) NOT NULL,
    level VARCHAR(20) NOT NULL,
    user_uuid VARCHAR(100) NOT NULL,
    nickname VARCHAR(50) DEFAULT 'Guest',
    clear_time INT NOT NULL,
    mistake_count INT DEFAULT 0,
    hint_count INT DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    user_ip VARCHAR(45),
    insert_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ranking (game_name, level, is_verified, clear_time)
);
```

Redis 랭킹 키 형식:
- `ranking:{game_name}:{level}`
- member: `{user_uuid}:{nickname}:{clear_time}:{mistake_count}:{hint_count}:{is_verified}:{user_ip}`
- score: `clear_time * 10000 + mistake_count * 100 + hint_count`

Redis 세션 키 형식:
- `session:{game_name}:{level}:{user_uuid}`
- value: 시작 시각(UNIX epoch seconds)
- TTL: 3600초 (1시간)

## 기록 검증 흐름
`POST /record` 요청 시 서버가 기록을 검증합니다.

1) `action_log` 기본 검증
- 비어있지 않고 길이가 10 이하
- `ts`가 오름차순
- `action_log` 구간 시간(ms) <= `clear_time * 1000`
- `submit` 액션 포함

2) 카운트 일치
- `wrong_answers` 길이 == `mistake_count`
- `hint_events` 길이 == `hint_count`

3) 게임별 검증
- `utils/verifier/registry.py`에서 `game_name`에 맞는 검증기를 선택
- 미등록 게임은 `BaseVerifier` 기본 검증만 수행

검증이 성공하면 `is_verified=True`로 저장되고, Redis 랭킹에도 반영됩니다.

## API
모든 엔드포인트는 `/record` prefix를 사용합니다.

### GET /record/health
헬스 체크.

응답:
```json
{ "status": "ok" }
```

### GET /record/user
사용자 UUID 발급. 닉네임은 UUID 앞 8자리로 설정됩니다.

응답:
```json
{ "user_uuid": "generated-uuid", "nickname": "generated" }
```

### PATCH /record/user/{user_uuid}
닉네임 수정. 해당 UUID가 가진 모든 기록의 `nickname`을 갱신합니다.

요청:
```json
{ "nickname": "new-nickname" }
```

응답:
```json
{ "user_uuid": "generated-uuid", "nickname": "new-nickname" }
```

### POST /record
게임 세션 기록 저장.

저장 흐름:
- 입력값 검증 후 `GameRecord` 생성
- 기록 검증 수행 (`is_verified` 설정)
- MySQL에 항상 저장
- 검증 성공 시 Redis 랭킹에 반영
- `action_log`는 DB에 저장하지 않음

요청:
```json
{
  "game_name": "sudoku",
  "level": "easy",
  "user_uuid": "generated-uuid",
  "nickname": "guest",
  "clear_time": 120,
  "mistake_count": 2,
  "hint_count": 1,
  "answers": [],
  "wrong_answers": [],
  "hint_events": [],
  "action_log": [
    { "ts": 1730000000123, "action": "start" },
    { "ts": 1730000001456, "action": "move", "payload": { "cell": "A1", "value": 3 } },
    { "ts": 1730000003999, "action": "submit", "payload": { "result": "success" } }
  ]
}
```

응답:
```json
{ "record_id": 1, "status": "success", "is_verified": true }
```

### GET /record/history/{game_name}/{level}/{user_uuid}
사용자 게임 기록 조회. 최신 기록부터 반환됩니다.

쿼리 파라미터:
- `limit` (기본 10)

데이터 소스:
- MySQL (`game_records`)

응답:
```json
[
  {
    "record_id": 1,
    "game_name": "sudoku",
    "level": "easy",
    "user_uuid": "generated-uuid",
    "nickname": "guest",
    "clear_time": 120,
    "mistake_count": 2,
    "hint_count": 1,
    "is_verified": true,
    "insert_ts": "2024-01-01T12:00:00"
  }
]
```

### GET /record/ranking/{game_name}/{level}
게임/난이도 랭킹 조회. 검증된 기록만 반환됩니다.

쿼리 파라미터:
- `limit` (기본 10)

데이터 소스:
- Redis Sorted Set (`ranking:{game_name}:{level}`)
- 정렬 기준: `clear_time` -> `mistake_count` -> `hint_count` (오름차순)

응답:
```json
[
  {
    "rank": 1,
    "user_uuid": "generated-uuid",
    "nickname": "player1",
    "clear_time": 100,
    "mistake_count": 0,
    "hint_count": 0
  }
]
```

## 지원 게임
- sudoku
- 2048
- nonogram
- hidato
- killer-sudoku
- shikaku

## 비고
- API 서버는 8888 포트 사용을 전제로 합니다.
- 운영 환경에서는 nginx 리버스 프록시 뒤에서 `/record` prefix로 운영될 수 있습니다.

## 운영 환경 구성
### MySQL
- DB명: `DB_NAME` (기본 `PUZZLE`)
- 테이블: `game_records` (위 DDL 참조)
- 인덱스: `idx_ranking (game_name, level, is_verified, clear_time)`
- 기본 정렬/랭킹 기준은 `clear_time`, `mistake_count`, `hint_count` 오름차순

### Redis
- DB 인덱스: 0
- 랭킹: `ranking:{game_name}:{level}` Sorted Set
- 세션: `session:{game_name}:{level}:{user_uuid}` key-value

### Nginx 리버스 프록시 예시
`/record` prefix로 서비스할 때의 최소 설정 예시입니다.
```nginx
server {
    listen 80;
    server_name example.com;

    location /record/ {
        proxy_pass http://127.0.0.1:8888/record/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
