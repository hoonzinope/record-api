from utils.verifier.base import BaseVerifier


class Game2048Verifier(BaseVerifier):
    def verify_payload(self, data) -> bool:
        if not super().verify_payload(data):
            return False

        action_log = data.get("action_log", [])
        if not self._has_action(action_log, "move"):
            return False

        answers = data.get("answers", [])
        if not answers:
            return False

        if not self._validate_answers(answers):
            return False
        if data.get("wrong_answers") or data.get("hint_events"):
            return False
        if not self._validate_move_actions(action_log):
            return False

        return True

    def _validate_answers(self, answers: list) -> bool:
        for entry in answers:
            if not isinstance(entry, dict):
                return False
            if "board" in entry or "grid" in entry:
                board = entry.get("board", entry.get("grid"))
                if not self._validate_board(board):
                    return False
            max_tile = entry.get("max_tile")
            if max_tile is not None and not self._is_power_of_two(max_tile):
                return False
            score = entry.get("score")
            if score is not None and (not isinstance(score, int) or score < 0):
                return False
            if max_tile is None and "board" not in entry and "grid" not in entry and score is None:
                return False
        return True

    def _validate_move_actions(self, action_log: list[dict]) -> bool:
        for entry in action_log:
            if not isinstance(entry, dict):
                return False
            if entry.get("action") != "move":
                continue
            payload = entry.get("payload") or {}
            if not isinstance(payload, dict):
                return False
            direction = payload.get("direction")
            if direction is not None and direction not in ("up", "down", "left", "right"):
                return False
        return True

    @staticmethod
    def _validate_board(board) -> bool:
        if not isinstance(board, list) or not board:
            return False
        if all(isinstance(row, list) for row in board):
            size = len(board)
            if any(len(row) != size for row in board):
                return False
            values = [val for row in board for val in row]
        else:
            values = board
        for value in values:
            if not isinstance(value, int):
                return False
            if value == 0:
                continue
            if value < 2 or (value & (value - 1)) != 0:
                return False
        return True

    @staticmethod
    def _is_power_of_two(value: int) -> bool:
        return isinstance(value, int) and value >= 2 and (value & (value - 1)) == 0
