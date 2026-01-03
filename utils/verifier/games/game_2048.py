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

        max_tile = answers[0].get("max_tile") if isinstance(answers[0], dict) else None
        if not isinstance(max_tile, int) or max_tile < 2:
            return False

        return True
