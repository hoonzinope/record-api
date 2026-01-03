from utils.verifier.base import BaseVerifier


class HidatoVerifier(BaseVerifier):
    def verify_payload(self, data) -> bool:
        if not super().verify_payload(data):
            return False

        answers = data.get("answers", [])
        if not answers:
            return False

        for entry in answers:
            if not isinstance(entry, dict):
                return False
            cell_key = self._get_cell_key(entry.get("cell"))
            value = entry.get("value")
            if not cell_key or not isinstance(value, int) or value < 1:
                return False

        return True
