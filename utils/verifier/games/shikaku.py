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
            rect = entry.get("rect")
            cells = entry.get("cells")
            if rect:
                if not isinstance(rect, dict):
                    return False
                for key in ("x", "y", "width", "height"):
                    if not isinstance(rect.get(key), int):
                        return False
                if rect["width"] <= 0 or rect["height"] <= 0:
                    return False
            elif cells:
                if not isinstance(cells, list) or not cells:
                    return False
            else:
                return False

        return True
