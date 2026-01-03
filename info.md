정보 및 요구사항

이 프로젝트는 웹 게임의 기록을 저장하고 관리하는 시스템입니다. 
사용자는 게임 세션을 기록하고, 저장된 데이터를 조회하며, 필요에 따라 데이터를 수정할 수 있습니다.

주요 기능:
1. 게임 세션 기록: 사용자는 게임 플레이 중에 세션을 기록할 수 있습니다.
2. 데이터 저장: 기록된 게임 세션은 데이터베이스에 안전하게 저장됩니다.
3. 데이터 조회: 사용자는 저장된 게임 세션 데이터를 조회할 수 있습니다.
4. 데이터 수정: 사용자는 필요에 따라 저장된 데이터를 수정할 수 있습니다.
   - 수정 가능한 필드 : 사용자 닉네임

db는 mysql을 사용하며, 다음과 같은 테이블 구조를 가집니다:
테이블 : game_records
```sql
-- game_record table
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
    INDEX idx_ranking (game_name, level, is_verified, clear_time) -- 랭킹 조회 최적화 (mistake, hint 의 경우, 정렬 조건에 추가)
);
```

redis는 캐싱 및 세션 관리를 위해 사용됩니다.
- 캐싱: 자주 조회되는 게임 기록 데이터를 캐싱하여 조회 속도를 향상
- 세션 관리: 사용자 세션 정보를 저장하여 인증 및 권한 부여에 활용
- 랭킹 시스템: 게임별, 난이도별 랭킹 데이터를 Redis Sorted Set을 사용하여 관리

fastapi 프레임워크를 사용하여 API 서버를 구축하며, port는 8888을 사용, 주요 엔드포인트는 다음과 같습니다:
1. GET /record/user : 사용자 UUID 발급 (닉네임 포함)
    - 응답: { "user_uuid": "generated-uuid", "nickname": "generated-nickname" }
    - 설명: 사용자가 처음 접속할 때 고유한 UUID를 발급받습니다. 기본 닉네임은 UUID[:8]로 설정됩니다.
2. PATCH /record/user/{user_uuid} : 사용자 닉네임 수정
    - 요청: { "nickname": "new-nickname" }
    - 응답: { "user_uuid": "generated-uuid", "nickname": "new-nickname" }
    - 설명: 사용자는 자신의 UUID를 사용하여 닉네임을 수정할 수 있습니다.
3. POST /record : 게임 세션 기록 저장
    - 요청: { "game_name": "GameA", "level": "Easy", "user_uuid": "generated-uuid", "clear_time": 120, "mistake_count": 2, "hint_count": 1, "action_log": [...] }
    - 응답: { "record_id": 1, "status": "success" }
    - 설명: 사용자는 게임 세션 기록을 저장할 수 있습니다. 기록은 데이터베이스에 저장되고, 검증된 기록만 랭킹 시스템에 반영됩니다.
4. GET /record/history/{game_name}/{level}/{user_uuid} : 사용자 게임 기록 조회
    - 응답: [ { "record_id": 1, "clear_time": 120, "mistake_count": 2, "hint_count": 1, "is_verified": true, "insert_ts": "2024-01-01T12:00:00Z" }, ... ]
    - 설명: 사용자는 특정 게임과 난이도에 대한 자신의 게임 기록을 조회할 수 있습니다.
5. GET /record/ranking/{game_name}/{level} : 게임 랭킹 조회
    - 응답: [ { "rank": 1, "user_uuid": "generated-uuid", "nickname": "player1", "clear_time": 100 }, ... ]
    - 설명: 사용자는 특정 게임과 난이도에 대한 랭킹을 조회할 수 있습니다. 랭킹은 클리어 타임, 틀린 횟수, 힌트 횟수를 기준으로 정렬됩니다.
    - 캐싱: 랭킹 데이터는 Redis에 캐싱되어 빠른 조회가 가능합니다.
    - 갱신: 새로운 기록이 저장될 때마다 랭킹 데이터가 갱신됩니다.
    - 정렬 기준: 클리어 타임(오름차순), 틀린 횟수(오름차순), 힌트 횟수(오름차순)

웹게임의 verification 시스템을 구현하며, 다음과 같은 요구사항을 충족합니다:
- 서버가 검증을 수행한 후 is_verified 필드를 설정합니다.
- 검증된 기록만 랭킹 시스템에 반영, 검증되지 않은 기록은 랭킹 조회 시 제외됩니다.
- 사용자는 정답, 오답 및 힌트 사용 내역을 함께 제출해야 합니다.
- action_log 형식: 최근 10개의 액션을 시간순(오래된 -> 최신)으로 보낸 JSON 배열입니다.
  - 필드: ts(UNIX epoch ms), action(문자열), payload(선택, 객체)
  - 예시:
    ```json
    [
      {"ts": 1730000000123, "action": "start"},
      {"ts": 1730000001456, "action": "move", "payload": {"cell": "A1", "value": 3}},
      {"ts": 1730000002789, "action": "hint", "payload": {"count": 1}},
      {"ts": 1730000003999, "action": "submit", "payload": {"result": "success"}}
    ]
    ```
- 사용자의 정답이 맞는지, 액션 간 시간차가 합리적인지, 클리어 타임이 합리적인지 등을 서버 측에서 검증합니다.
- action_log는 저장하지 않습니다. 게임 기록에는 clear_time, mistake_count, hint_count, user_ip가 저장되어야 합니다.
- 각 게임별 검증 로직은 별도의 모듈로 구현되어 유지보수가 용이하도록 설계합니다.
- 게임 목록은 다음과 같다.
  - sudoku
  - 2048
  - nonogram
  - hidato
  - killer-sudoku
  - shikaku
  - *추후 신규 게임이 추가될 수 있음
  
배포 및 운영:
- Docker를 사용하여 컨테이너화된 환경에서 배포
- 로컬에서 테스트시 접근하는 mysql, redis는 localhost:3306, localhost:6379
- 운영 환경에서는 환경 변수로 데이터베이스 및 캐시 서버의 호스트와 포트를 설정
- 이미 존재하고 있는 nginx 리버스 프록시 뒤에서 동작하도록 설정 예정 (포트 8888 사용, prefix /record)
- 로컬, 운영 환경 모두에서 동일한 코드베이스 사용 가능하게끔 구성 필요

요구사항:
- Python 3.10.16 버전 사용
- FastAPI 프레임워크 사용
- MySQL 데이터베이스 사용
- Redis 캐싱 및 세션 관리 사용
