from utils.verifier.base import BaseVerifier


class KillerSudokuVerifier(BaseVerifier):
    def verify_payload(self, data) -> bool:
        if not super().verify_payload(data):
            return False

        answers = data.get("answers", [])
        if not answers:
            return False

        seen_cells = set()
        for entry in answers:
            if not isinstance(entry, dict):
                return False
            cell_key = self._get_cell_key(entry.get("cell"))
            value = entry.get("value")
            if not cell_key or not isinstance(value, int):
                return False
            if value < 1 or value > 9:
                return False
            if cell_key in seen_cells:
                return False
            seen_cells.add(cell_key)

        return True
