from utils.verifier.base import BaseVerifier
from utils.verifier.games.game_2048 import Game2048Verifier
from utils.verifier.games.hidato import HidatoVerifier
from utils.verifier.games.killer_sudoku import KillerSudokuVerifier
from utils.verifier.games.nonogram import NonogramVerifier
from utils.verifier.games.shikaku import ShikakuVerifier
from utils.verifier.games.sudoku import SudokuVerifier

DEFAULT_VERIFIER = BaseVerifier()

VERIFIER_MAP = {
    "sudoku": SudokuVerifier(),
    "2048": Game2048Verifier(),
    "nonogram": NonogramVerifier(),
    "hidato": HidatoVerifier(),
    "killer-sudoku": KillerSudokuVerifier(),
    "shikaku": ShikakuVerifier(),
}


def get_verifier(game_name: str) -> BaseVerifier:
    return VERIFIER_MAP.get(game_name, DEFAULT_VERIFIER)
