from utils.verifier.base import BaseVerifier


class TetrisVerifier(BaseVerifier):
    def verify_payload(self, data) -> bool:
        if not super().verify_payload(data):
            return False

        action_log = data.get("action_log", [])
        if not self._has_action(action_log, "move"):
            return False

        answers = data.get("answers", [])
        if not isinstance(answers, list) or not answers:
            return False
        for entry in answers:
            if not isinstance(entry, dict):
                return False
            score = entry.get("score")
            if score is not None and (not isinstance(score, int) or score < 0):
                return False
            lines = entry.get("lines_cleared")
            if lines is not None and (not isinstance(lines, int) or lines < 0):
                return False

        return True
