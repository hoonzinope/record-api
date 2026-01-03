from utils.verifier.base import BaseVerifier


class KillerSudokuVerifier(BaseVerifier):
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
        for entry in entries:
            if not isinstance(entry, dict):
                return False
            if "board" in entry or "grid" in entry:
                board = entry.get("board", entry.get("grid"))
                if not self._validate_board(board):
                    return False
                continue
            cell_key = self._get_cell_key_from_entry(entry)
            value = entry.get("value", entry.get("number"))
            if require_value and not isinstance(value, int):
                return False
            if isinstance(value, int) and (value < 1 or value > 9):
                return False
            if not cell_key:
                return False
            if cell_key in seen_cells:
                return False
            seen_cells.add(cell_key)
        return True

    @staticmethod
    def _validate_board(board) -> bool:
        values = []
        if isinstance(board, list):
            if len(board) != 81:
                return False
            if not all(isinstance(val, int) and 1 <= val <= 9 for val in board):
                return False
            values = board
        else:
            return False

        for row in range(9):
            start = row * 9
            if len(set(values[start:start + 9])) != 9:
                return False
        for col in range(9):
            if len(set(values[col::9])) != 9:
                return False
        for box_row in range(0, 9, 3):
            for box_col in range(0, 9, 3):
                block = []
                for r in range(3):
                    offset = (box_row + r) * 9 + box_col
                    block.extend(values[offset:offset + 3])
                if len(set(block)) != 9:
                    return False
        return True
