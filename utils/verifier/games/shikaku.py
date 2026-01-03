from utils.verifier.base import BaseVerifier


class ShikakuVerifier(BaseVerifier):
    def verify_payload(self, data) -> bool:
        if not super().verify_payload(data):
            return False

        answers = data.get("answers", [])
        if not answers:
            return False

        for entry in answers:
            if not isinstance(entry, dict):
                return False
            rect = entry.get("rect", entry)
            cells = entry.get("cells")
            if rect and any(key in rect for key in ("x", "y", "w", "h", "width", "height")):
                if not isinstance(rect, dict):
                    return False
                if not self._validate_rect(rect):
                    return False
            elif cells:
                if not isinstance(cells, list) or not cells:
                    return False
                if not self._validate_cells(cells):
                    return False
            else:
                return False

        return True

    @staticmethod
    def _validate_rect(rect: dict) -> bool:
        x = rect.get("x")
        y = rect.get("y")
        w = rect.get("w", rect.get("width"))
        h = rect.get("h", rect.get("height"))
        if not all(isinstance(value, int) for value in (x, y, w, h)):
            return False
        if x < 0 or y < 0 or w <= 0 or h <= 0:
            return False
        return True

    def _validate_cells(self, cells: list) -> bool:
        seen_cells = set()
        for cell in cells:
            if not isinstance(cell, dict):
                return False
            cell_key = self._get_cell_key_from_entry(cell, cell_field="cell")
            if not cell_key:
                return False
            if cell_key in seen_cells:
                return False
            seen_cells.add(cell_key)
        return True
