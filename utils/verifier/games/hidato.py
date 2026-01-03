from utils.verifier.base import BaseVerifier


class HidatoVerifier(BaseVerifier):
    def verify_payload(self, data) -> bool:
        if not super().verify_payload(data):
            return False

        answers = data.get("answers", [])
        if not answers:
            return False

        if not self._validate_entries(answers, require_value=True):
            return False
        if not self._validate_entries(data.get("wrong_answers", []), require_value=True):
            return False
        if not self._validate_entries(data.get("hint_events", []), require_value=True):
            return False

        return True

    def _validate_entries(self, entries: list, require_value: bool) -> bool:
        if not isinstance(entries, list):
            return False
        seen_cells = set()
        seen_values = set()
        for entry in entries:
            if not isinstance(entry, dict):
                return False
            cell_key = self._get_cell_key_from_entry(entry)
            value = entry.get("value", entry.get("number"))
            if require_value and not isinstance(value, int):
                return False
            if isinstance(value, int) and value < 1:
                return False
            if not cell_key:
                return False
            if cell_key in seen_cells:
                return False
            if isinstance(value, int) and value in seen_values:
                return False
            seen_cells.add(cell_key)
            if isinstance(value, int):
                seen_values.add(value)
        return True
