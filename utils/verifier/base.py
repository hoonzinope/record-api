from utils.verifier.verifier_interface import VerifierInterface


class BaseVerifier(VerifierInterface):
    def verify(self, data) -> bool:
        return self.verify_payload(data)

    def verify_payload(self, data) -> bool:
        if not isinstance(data, dict):
            return False

        action_log = data.get("action_log", [])
        if not isinstance(action_log, list) or not action_log:
            return False
        if not self._has_action(action_log, "submit"):
            return False

        for key in ("answers", "wrong_answers", "hint_events"):
            value = data.get(key, [])
            if not isinstance(value, list):
                return False
        return True

    @staticmethod
    def _has_action(action_log: list[dict], name: str) -> bool:
        return any(entry.get("action") == name for entry in action_log if isinstance(entry, dict))

    @staticmethod
    def _get_cell_key(cell) -> str:
        if isinstance(cell, str):
            return cell
        if isinstance(cell, dict):
            row = cell.get("row")
            col = cell.get("col")
            if isinstance(row, int) and isinstance(col, int):
                return f"{row},{col}"
        return ""
