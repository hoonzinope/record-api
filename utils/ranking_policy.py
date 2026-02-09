from model.game_record import GameRecord


POLICY_DEFAULT = "time_asc"
POLICY_SCORE_ASC_TIE_TIME_ASC = "score_desc_tie_time_asc"
POLICY_SCORE_ASC_TIE_TIME_DESC = "score_desc_tie_time_desc"
POLICY_ATTEMPT_ASC_TIE_TIME_ASC = "attempt_asc_tie_time_asc"

GAME_RANKING_POLICY: dict[str, str] = {
    "2048": POLICY_SCORE_ASC_TIE_TIME_ASC,
    "woodoku": POLICY_SCORE_ASC_TIE_TIME_ASC,
    "tetris": POLICY_SCORE_ASC_TIE_TIME_DESC,
    "wordle": POLICY_ATTEMPT_ASC_TIE_TIME_ASC,
    "kordle": POLICY_ATTEMPT_ASC_TIE_TIME_ASC,
}


def get_policy(game_name: str) -> str:
    return GAME_RANKING_POLICY.get(game_name, POLICY_DEFAULT)


def get_clear_time_ns(record: GameRecord) -> int:
    if getattr(record, "clear_time_ns", 0):
        return int(record.clear_time_ns)
    clear_time = max(1, int(getattr(record, "clear_time", 0) or 0))
    return clear_time * 1_000_000_000


def redis_score_for(game_name: str, record: GameRecord) -> float:
    policy = get_policy(game_name)
    if policy in (POLICY_SCORE_ASC_TIE_TIME_ASC, POLICY_SCORE_ASC_TIE_TIME_DESC):
        return float(-(int(record.score) if record.score is not None else 0))
    if policy == POLICY_ATTEMPT_ASC_TIE_TIME_ASC:
        return float(int(record.mistake_count) if record.mistake_count is not None else 0)
    return float(get_clear_time_ns(record))


def sort_key_for(game_name: str, record: GameRecord) -> tuple:
    policy = get_policy(game_name)
    clear_time_ns = get_clear_time_ns(record)
    score = int(record.score) if record.score is not None else 0
    attempt_count = int(record.mistake_count) if record.mistake_count is not None else 0
    hint_count = int(record.hint_count) if record.hint_count is not None else 0

    if policy == POLICY_SCORE_ASC_TIE_TIME_ASC:
        return (-score, clear_time_ns)
    if policy == POLICY_SCORE_ASC_TIE_TIME_DESC:
        return (-score, -clear_time_ns)
    if policy == POLICY_ATTEMPT_ASC_TIE_TIME_ASC:
        return (attempt_count, clear_time_ns)
    return (clear_time_ns, attempt_count, hint_count)


def sql_order_clause_for(game_name: str) -> str:
    policy = get_policy(game_name)
    effective_ns = "COALESCE(clear_time_ns, clear_time * 1000000000)"
    if policy == POLICY_SCORE_ASC_TIE_TIME_ASC:
        return f"score DESC, {effective_ns} ASC"
    if policy == POLICY_SCORE_ASC_TIE_TIME_DESC:
        return f"score DESC, {effective_ns} DESC"
    if policy == POLICY_ATTEMPT_ASC_TIE_TIME_ASC:
        return f"mistake_count ASC, {effective_ns} ASC"
    return f"{effective_ns} ASC, mistake_count ASC, hint_count ASC"
