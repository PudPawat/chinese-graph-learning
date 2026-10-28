"""Meaning part and sound part for each character, in the same sense as the character page.

A left-side form such as 忄 is stored as the full character 心. The other side is the
sound part when it is a real phonetic (青 in 情), or when it is the sibling of a
side form (工 in 江). Same sound and same part family are other characters that
share that part.
"""

from __future__ import annotations

import gzip
import re
import unicodedata
from pathlib import Path

IDS_PATH = Path(__file__).resolve().parent / "source" / "ids.txt"
CEDICT_PATH = Path(__file__).resolve().parent / "source" / "cedict.txt.gz"
TONE_MARKS = {
    "a": "āáǎà",
    "e": "ēéěè",
    "i": "īíǐì",
    "o": "ōóǒò",
    "u": "ūúǔù",
    "ü": "ǖǘǚǜ",
}

IDC = {
    "⿰": 2,
    "⿱": 2,
    "⿲": 3,
    "⿳": 3,
    "⿴": 2,
    "⿵": 2,
    "⿶": 2,
    "⿷": 2,
    "⿸": 2,
    "⿹": 2,
    "⿺": 2,
    "⿻": 2,
}

# Side form -> the character the page teaches as the meaning part.
SIDE = {
    "忄": "心",
    "⺗": "心",
    "氵": "水",
    "氺": "水",
    "⺢": "水",
    "扌": "手",
    "龵": "手",
    "亻": "人",
    "𠆢": "人",
    "讠": "言",
    "訁": "言",
    "艹": "艸",
    "⺾": "艸",
    "⺿": "艸",
    "犭": "犬",
    "饣": "食",
    "飠": "食",
    "纟": "糸",
    "糹": "糸",
    "钅": "金",
    "釒": "金",
    "灬": "火",
    "⺮": "竹",
    "⻊": "足",
    "𧾷": "足",
    "辶": "辵",
    "⻌": "辵",
    "⻍": "辵",
    "刂": "刀",
    "⺉": "刀",
    "衤": "衣",
    "⻂": "衣",
    "礻": "示",
    "⺬": "示",
    "牜": "牛",
    "⺧": "牛",
    "⺶": "羊",
    "⺷": "羊",
    "⺼": "肉",
    "罒": "网",
    "⺲": "网",
    "⻗": "雨",
    "⻏": "邑",
    "⻖": "阜",
    "⺌": "小",
}

# Full characters that can be the meaning part when they sit on the meaning side.
SEMANTIC = set(
    "一心水木火土金口言人女日月目手足走魚馬鳥犬虫米禾竹雨山石田肉衣示刀牛羊食糸"
    "玉王貝車門風頁見耳身力巾广宀尸戶文子小大工白矢穴立缶羽老而自至舌舟艮色虍血"
    "行西角谷豆豕豸赤辛辰邑酉里長阜隹青非面革韋音飛首香骨高鬼鹿麻黃黑齊齒龍"
    "皿父方斤斗止欠歹殳毛氏气爪片牙牛父爻片用生用"
)

TOP = set("艹⺾⺿宀⺮⻗穴⺌广尸厂戶户戸⻌")
BOTTOM = set("心⺗灬皿儿⺕")
ENCLOSE = set("⿴⿵⿶⿷")
INITIALS = (
    "zh", "ch", "sh", "b", "p", "m", "f", "d", "t", "n", "l", "g", "k", "h",
    "j", "q", "x", "r", "z", "c", "s", "y", "w",
)
CAP = 8


def syllable(pinyin: str) -> str:
    token = pinyin.strip().split()[0] if pinyin else ""
    token = token.replace("ü", "v").replace("u:", "v")
    text = unicodedata.normalize("NFD", token)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower()


def rime(syl: str) -> str:
    for initial in INITIALS:
        if syl.startswith(initial) and len(syl) > len(initial):
            return syl[len(initial):]
    return syl


def sounds_alike(left: str, right: str, loose: bool = False) -> int:
    if not left or not right:
        return 0
    if left == right:
        return 10
    left_rime, right_rime = rime(left), rime(right)
    if left_rime == right_rime and (len(left_rime) >= 2 or loose):
        return 6
    return 0


def apply_tone(text: str, tone: int) -> str:
    if tone < 1 or tone > 4:
        return text
    chars = list(text)

    def mark(index: int) -> str:
        chars[index] = TONE_MARKS[chars[index]][tone - 1]
        return "".join(chars)

    if "a" in text:
        return mark(text.index("a"))
    if "e" in text:
        return mark(text.index("e"))
    if "ou" in text:
        return mark(text.index("ou"))
    for index in range(len(chars) - 1, -1, -1):
        if chars[index] in TONE_MARKS:
            return mark(index)
    return text


def cedict_readings() -> dict[str, str]:
    readings: dict[str, str] = {}
    if not CEDICT_PATH.exists():
        return readings
    with gzip.open(CEDICT_PATH, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line or line.startswith("#") or "[" not in line:
                continue
            traditional = line.split(" ", 1)[0]
            if len(traditional) != 1 or traditional in readings:
                continue
            raw = line.split("[", 1)[1].split("]", 1)[0].split()
            if not raw:
                continue
            token = raw[0].replace("u:", "ü")
            tone = 5
            if token[-1].isdigit():
                tone = int(token[-1])
                token = token[:-1]
            readings[traditional] = apply_tone(token, tone)
    return readings


def load_trees() -> dict[str, object]:
    trees: dict[str, object] = {}
    if not IDS_PATH.exists():
        return trees
    for line in IDS_PATH.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3 or parts[1] in trees:
            continue
        try:
            trees[parts[1]] = parse_ids(parts[2])
        except (ValueError, IndexError):
            continue
    return trees


def parse_ids(raw: str) -> object:
    text = re.sub(r"\[[A-Za-z0-9]+\]", "", raw.strip())

    def read(index: int) -> tuple[object, int]:
        if index >= len(text):
            raise ValueError(raw)
        char = text[index]
        if char in IDC:
            index += 1
            kids = []
            for _ in range(IDC[char]):
                kid, index = read(index)
                kids.append(kid)
            return (char, kids), index
        return char, index + 1

    node, end = read(0)
    if end != len(text):
        raise ValueError(raw)
    return node


def canonical(char: str, op: str | None, index: int) -> str | None:
    if char == "阝":
        if op == "⿰" and index == 1:
            return "邑"
        return "阜"
    if char in SIDE:
        return SIDE[char]
    if char in SEMANTIC:
        return char
    return None


def flatten(node: object) -> list[str]:
    if isinstance(node, str):
        return [node]
    out: list[str] = []
    for kid in node[1]:
        out.extend(flatten(kid))
    return out


def keep_whole(char: str, known: set[str]) -> bool:
    # Ordinary characters stay intact so 可 in 河 is the sound part.
    # Rare pieces such as 𢖻 inside 愛 still open up, which reveals 心.
    return char in known or 0x4E00 <= ord(char) <= 0x9FFF


def expand(node: object, trees: dict[str, object], known: set[str], depth: int = 0) -> object:
    if isinstance(node, str):
        if depth < 3 and not keep_whole(node, known) and node in trees:
            return expand(trees[node], trees, known, depth + 1)
        return node
    return (node[0], [expand(kid, trees, known, depth) for kid in node[1]])


class Leaf:
    def __init__(self, char: str, op: str | None, index: int, sibling: str | None) -> None:
        self.char = char
        self.op = op
        self.index = index
        self.sibling = sibling
        self.name = canonical(char, op, index)
        self.variant = char in SIDE or char == "阝"


def collect(node: object, op: str | None, index: int, sibling: object | None, out: list[Leaf]) -> None:
    if isinstance(node, str):
        sib = None
        if sibling is not None:
            flat = flatten(sibling)
            if len(flat) == 1:
                sib = flat[0]
        out.append(Leaf(node, op, index, sib))
        return
    operator, kids = node
    for position, kid in enumerate(kids):
        others = [item for other, item in enumerate(kids) if other != position]
        sibling_node = others[0] if len(others) == 1 else None
        collect(kid, operator, position, sibling_node, out)


def meaning_score(leaf: Leaf) -> int:
    if leaf.name is None:
        return 0
    score = 2
    if leaf.variant:
        score += 8
    if leaf.op == "⿰" and leaf.index == 0:
        score += 4
    elif leaf.op == "⿱" and leaf.index == 0 and (leaf.char in TOP or leaf.char in SEMANTIC or leaf.variant):
        score += 4
    elif leaf.op == "⿱" and leaf.index == 1 and (leaf.char in BOTTOM or leaf.name == "心"):
        score += 4
    elif leaf.op in ENCLOSE and leaf.index == 0:
        score += 3
    elif leaf.op in ("⿸", "⿹", "⿺") and leaf.index == 0:
        score += 3
    if leaf.char == "心" or leaf.name == "心":
        score = max(score, 6)
    return score


def analyze(
    glyphs: set[str],
    pinyin_of: dict[str, str],
    family_glyphs: set[str],
    rank_of: dict[str, int],
) -> dict[str, dict]:
    """One record per glyph. Lists only include characters from family_glyphs."""
    trees = load_trees()
    readings = cedict_readings()
    readings.update({glyph: reading for glyph, reading in pinyin_of.items() if reading})
    known = set(readings) | SEMANTIC | set(SIDE) | set(SIDE.values())
    syllables = {glyph: syllable(readings.get(glyph, "")) for glyph in set(glyphs) | set(readings)}
    assigned: dict[str, dict] = {}

    for glyph in glyphs:
        tree = trees.get(glyph)
        if tree is None or isinstance(tree, str) or (isinstance(tree, tuple) and tree[0] == "⿻"):
            assigned[glyph] = {"glyph": glyph, "meaning": glyph, "sound": glyph, "side": None}
            continue
        expanded = expand(tree, trees, known)
        if isinstance(expanded, tuple) and expanded[0] == "⿻":
            assigned[glyph] = {"glyph": glyph, "meaning": glyph, "sound": glyph, "side": None}
            continue
        leaves: list[Leaf] = []
        collect(expanded, None, 0, None, leaves)
        char_syl = syllables.get(glyph, "")
        ranked = [(meaning_score(leaf), leaf) for leaf in leaves]
        ranked.sort(key=lambda item: item[0], reverse=True)
        meaning_leaf = ranked[0][1] if ranked and ranked[0][0] >= 5 else None
        sound_leaf = None
        best_sound = 0
        for leaf in leaves:
            loose = (
                meaning_leaf is not None
                and meaning_leaf.op == "⿰"
                and meaning_leaf.index == 0
                and leaf.char == meaning_leaf.sibling
            )
            score = sounds_alike(syllables.get(leaf.char, ""), char_syl, loose=loose)
            if score > best_sound:
                best_sound = score
                sound_leaf = leaf
        if (
            sound_leaf is not None
            and meaning_leaf is not None
            and sound_leaf.char == meaning_leaf.char
            and sound_leaf.op == meaning_leaf.op
            and sound_leaf.index == meaning_leaf.index
        ):
            for score, leaf in ranked:
                if score > 0 and leaf is not meaning_leaf:
                    meaning_leaf = leaf
                    break
        if meaning_leaf is None or meaning_score(meaning_leaf) < 5:
            # A borrowed sound can leave a weaker radical, as 口 does in 問.
            if sound_leaf is not None:
                for score, leaf in ranked:
                    if score > 0 and not (
                        leaf.char == sound_leaf.char and leaf.op == sound_leaf.op and leaf.index == sound_leaf.index
                    ):
                        meaning_leaf = leaf
                        break
                else:
                    meaning_leaf = None
            else:
                meaning_leaf = None
        if meaning_leaf is None:
            meaning = glyph
            side = None
        else:
            meaning = meaning_leaf.name or glyph
            side = meaning_leaf.char if meaning_leaf.variant and meaning_leaf.char != meaning else None
        if sound_leaf is not None and best_sound > 0 and sound_leaf.char != glyph:
            sound = sound_leaf.char
        elif meaning_leaf is not None and meaning_leaf.variant and meaning_leaf.sibling:
            sound = meaning_leaf.sibling
        elif (
            meaning_leaf is not None
            and meaning_leaf.op == "⿰"
            and meaning_leaf.index == 0
            and meaning_leaf.sibling
            and meaning_leaf.sibling not in SEMANTIC
        ):
            sound = meaning_leaf.sibling
        else:
            sound = glyph
        if sound == meaning and sound != glyph:
            sound = glyph
        assigned[glyph] = {"glyph": glyph, "meaning": meaning, "sound": sound, "side": side}

    by_sound: dict[str, list[str]] = {}
    by_meaning: dict[str, list[str]] = {}
    for glyph, part in assigned.items():
        if glyph not in family_glyphs:
            continue
        by_sound.setdefault(part["sound"], []).append(glyph)
        by_meaning.setdefault(part["meaning"], []).append(glyph)

    def ordered(chars: list[str], skip: set[str]) -> list[str]:
        rows = [char for char in chars if char not in skip]
        rows.sort(key=lambda char: (rank_of.get(char, 100000), char))
        return rows[:CAP]

    for glyph, part in assigned.items():
        sound = part["sound"]
        meaning = part["meaning"]
        glyph_syllable = syllables.get(glyph, "")
        siblings = [
            char for char in ordered(by_sound.get(sound, []), {glyph, sound})
            if glyph_syllable and syllables.get(char) == glyph_syllable
        ]
        if not siblings and glyph_syllable:
            homophones = [
                char for char in family_glyphs
                if char != glyph and syllables.get(char) == glyph_syllable
            ]
            homophones.sort(key=lambda char: (rank_of.get(char, 100000), char))
            siblings = homophones[:CAP]
        if not siblings:
            siblings = [sound] if sound != glyph else [glyph]
        family = ordered(by_meaning.get(meaning, []), {glyph})
        if not family:
            family = [meaning] if meaning != glyph else [glyph]
        part["same_sound"] = siblings
        part["same_family"] = family
        if not part["meaning"] or not part["sound"] or not part["same_sound"] or not part["same_family"]:
            raise RuntimeError(f"blank character part for {glyph}")
    return assigned
