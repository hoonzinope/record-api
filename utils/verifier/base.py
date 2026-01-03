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
        if isinstance(cell, int):
            if cell < 0:
                return ""
            return f"idx:{cell}"
        if isinstance(cell, str):
            return cell
        if isinstance(cell, dict):
            index = cell.get("index")
            if isinstance(index, int):
                if index < 0:
                    return ""
                return f"idx:{index}"
            row = cell.get("row")
            col = cell.get("col")
            if isinstance(row, int) and isinstance(col, int):
                if row < 0 or col < 0:
                    return ""
                return f"{row},{col}"
            x = cell.get("x")
            y = cell.get("y")
            if isinstance(x, int) and isinstance(y, int):
                if x < 0 or y < 0:
                    return ""
                return f"{x},{y}"
        return ""

    @classmethod
    def _get_cell_key_from_entry(cls, entry: dict, cell_field: str = "cell") -> str:
        if not isinstance(entry, dict):
            return ""
        if cell_field in entry:
            key = cls._get_cell_key(entry.get(cell_field))
            if key:
                return key
        row = entry.get("row")
        col = entry.get("col")
        if isinstance(row, int) and isinstance(col, int):
            if row < 0 or col < 0:
                return ""
            return f"{row},{col}"
        x = entry.get("x")
        y = entry.get("y")
        if isinstance(x, int) and isinstance(y, int):
            if x < 0 or y < 0:
                return ""
            return f"{x},{y}"
        index = entry.get("index")
        if isinstance(index, int):
            if index < 0:
                return ""
            return f"idx:{index}"
        return ""
