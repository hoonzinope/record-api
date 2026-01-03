from utils.verifier.base import BaseVerifier


class NonogramVerifier(BaseVerifier):
    def verify_payload(self, data) -> bool:
        if not super().verify_payload(data):
            return False

        answers = data.get("answers", [])
        if not answers:
            return False

        if not self._validate_entries(answers, require_state=True):
            return False
        if not self._validate_entries(data.get("wrong_answers", []), require_state=False):
            return False
        if not self._validate_entries(data.get("hint_events", []), require_state=False):
            return False

        return True

    def _validate_entries(self, entries: list, require_state: bool) -> bool:
        if not isinstance(entries, list):
            return False
        seen_cells = set()
        for entry in entries:
            if not isinstance(entry, dict):
                return False
            cell_key = self._get_cell_key_from_entry(entry)
            if not cell_key:
                return False
            if cell_key in seen_cells:
                return False
            seen_cells.add(cell_key)
            if require_state:
                if "filled" in entry:
                    if not isinstance(entry.get("filled"), bool):
                        return False
                elif "state" in entry:
                    state = entry.get("state")
                    if not isinstance(state, str):
                        return False
                    if state not in ("filled", "marked", "empty", "clear"):
                        return False
                else:
                    return False
        return True
