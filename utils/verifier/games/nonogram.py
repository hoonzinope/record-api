from utils.verifier.base import BaseVerifier


class NonogramVerifier(BaseVerifier):
    def verify_payload(self, data) -> bool:
        if not super().verify_payload(data):
            return False

        answers = data.get("answers", [])
        if not answers:
            return False

        for entry in answers:
            if not isinstance(entry, dict):
                return False
            row = entry.get("row")
            col = entry.get("col")
            if not isinstance(row, int) or not isinstance(col, int):
                return False
            if row < 0 or col < 0:
                return False
            if "filled" not in entry and "state" not in entry:
                return False

        return True
