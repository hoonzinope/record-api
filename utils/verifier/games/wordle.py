from utils.verifier.base import BaseVerifier


class WordleVerifier(BaseVerifier):
    def verify_payload(self, data) -> bool:
        if not super().verify_payload(data):
            return False

        action_log = data.get("action_log", [])
        if not self._has_action(action_log, "guess"):
            return False

        answers = data.get("answers", [])
        if not isinstance(answers, list) or not answers:
            return False

        for answer in answers:
            if not isinstance(answer, dict):
                return False
            word = answer.get("word")
            if not isinstance(word, str) or not word.strip():
                return False

        return True
