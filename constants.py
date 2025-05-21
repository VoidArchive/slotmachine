from dataclasses import dataclass

@dataclass(frozen=True)
class Symbol:
    emoji: str
    weight: int
    base: int
    name: str

SYMBOLS = [
    Symbol("\U0001F352", 40, 5, "Cherry"),
    Symbol("\U0001F34B", 40, 5, "Lemon"),
    Symbol("\U0001F34A", 40, 5, "Orange"),
    Symbol("\U0001F514", 15, 10, "Bell"),
    Symbol("\U0001F349", 15, 10, "Watermelon"),
    Symbol("\u2B50", 4, 20, "Star"),
    Symbol("\U0001F48E", 1, 50, "Diamond"),
]

EMOJIS = [s.emoji for s in SYMBOLS]
WEIGHTS = [s.weight for s in SYMBOLS]
SYMBOL_BY_EMOJI = {s.emoji: s for s in SYMBOLS} 