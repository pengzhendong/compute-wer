# Copyright (c) 2025, Zhendong Peng (pzd17@tsinghua.org.cn)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import codecs
import unicodedata
from typing import Dict, List
from unicodedata import category

from compute_wer.wer import WER

spacelist = [" ", "\t", "\r", "\n"]
single_quote = "'"


def is_punctuation(char):
    """Checks if a character is a punctuation mark or a symbol across all languages."""
    cat = category(char)
    return cat.startswith("P") or cat.startswith("S")


def is_character_based(char):
    """
    Identifies languages that are naturally character-based or
    do not use spaces (non-segmented languages).
    """
    cp = ord(char)
    # 1. CJK (Chinese, Japanese Kanji/Kana)
    if (0x4E00 <= cp <= 0x9FFF) or (0x3040 <= cp <= 0x30FF):
        return True
    # 2. Thai
    if 0x0E00 <= cp <= 0x0E7F:
        return True
    # 3. Lao
    if 0x0E80 <= cp <= 0x0EFF:
        return True
    # 4. Myanmar (Burmese)
    if 0x1000 <= cp <= 0x109F:
        return True
    # 5. Khmer (Cambodian)
    if 0x1780 <= cp <= 0x17FF:
        return True
    # 6. Tibetan
    if 0x0F00 <= cp <= 0x0FFF:
        return True
    return False


def tokenize(text, to_char=False, ignore_punctuation=True):
    res = []
    i = 0
    length = len(text)

    while i < length:
        char = text[i]
        cat = category(char)
        # 1. Skip whitespace or unassigned characters
        if cat in {"Zs", "Cn"}:
            i += 1
            continue
        # 2. Handle Punctuation
        if is_punctuation(char):
            if not ignore_punctuation:
                res.append(char)
                i += 1
                continue
            elif char == single_quote:
                # Keep it for potential word-internal use (e.g., "it's")
                pass
            else:
                i += 1
                continue
        # 3. Handle Character-based scripts (CN, JP, TH, etc.)
        if is_character_based(char):
            res.append(char)
            i += 1
        # 4. Handle Alphabetic/Syllabic scripts (EN, KR, RU, etc.)
        elif cat.startswith(("L", "N")):
            if to_char:
                # If to_char is True, treat every letter as a separate token (CER mode)
                res.append(char)
                i += 1
            else:
                # If to_char is False, group letters into a word (WER mode)
                j = i + 1
                while j < length:
                    next_char = text[j]
                    next_cat = category(next_char)
                    # Break if we hit a boundary
                    if next_cat == "Zs" or is_character_based(next_char):
                        break
                    if is_punctuation(next_char) and next_char != single_quote:
                        break
                    # Continue grouping if it's a Letter/Number or internal quote
                    if next_cat.startswith(("L", "N")) or next_char == single_quote:
                        j += 1
                    else:
                        break
                res.append(text[i:j])
                i = j
        else:
            # Skip other types of characters
            i += 1
    return res


def char_name(char):
    """
    Get the name of a character.

    Args:
        char (str): The character.
    Return:
        str: The name of the character.
    """
    if char == "\x01":
        return "SOH"
    return unicodedata.name(char, "UNK")


def default_cluster(word: str) -> str:
    """
    Get the default cluster of a word.

    Args:
        word: The word to get the default cluster.
    Returns:
        The default cluster.
    """
    replacements = {
        "DIGIT": "Number",
        "CJK UNIFIED IDEOGRAPH": "Chinese",
        "CJK COMPATIBILITY IDEOGRAPH": "Chinese",
        "LATIN CAPITAL LETTER": "English",
        "LATIN SMALL LETTER": "English",
        "HIRAGANA LETTER": "Japanese",
        "KATAKANA LETTER": "Japanese",
    }
    ignored_prefixes = (
        "AMPERSAND",
        "APOSTROPHE",
        "COMMERCIAL AT",
        "DEGREE CELSIUS",
        "EQUALS SIGN",
        "FULL STOP",
        "HYPHEN-MINUS",
        "LOW LINE",
        "NUMBER SIGN",
        "PLUS SIGN",
        "SEMICOLON",
        "SOH (Start of Header)",
        "UNK (UNKOWN)",
    )
    clusters = set()
    for name in [char_name(char) for char in word]:
        if any(name.startswith(prefix) for prefix in ignored_prefixes):
            continue
        cluster = "Other"
        for key, value in replacements.items():
            if name.startswith(key):
                cluster = value
                break
        clusters.add(cluster or "Other")
    return clusters.pop() if len(clusters) == 1 else "Other"


def read_scp(scp_path: str) -> Dict[str, str]:
    """
    Read the scp file and return a dictionary of utterance to text.

    Args:
        scp_path: The path to the scp file.
    Returns:
        The dictionary of utterance to text.
    """
    utt2text = {}
    for line in codecs.open(scp_path, encoding="utf-8"):
        arr = line.strip().split(maxsplit=1)
        if len(arr) == 0:
            continue
        utt, text = arr[0], arr[1] if len(arr) > 1 else ""
        if utt in utt2text and text != utt2text[utt]:
            raise ValueError(f"Conflicting text found:\n{utt}\t{text}\n{utt}\t{utt2text[utt]}")
        utt2text[utt] = text
    return utt2text


def strip_tags(token: str) -> str:
    """
    Strip the tags from the token.

    Args:
        token: The token to strip the tags.
    Returns:
        The token without tags.
    """
    if not token:
        return ""
    chars = []
    i = 0
    while i < len(token):
        if token[i] == "<":
            end = token.find(">", i) + 1
            if end == 0:
                chars.append(token[i])
                i += 1
            else:
                i = end
        else:
            chars.append(token[i])
            i += 1
    return "".join(chars)


def normalize(
    text: str,
    to_char: bool = False,
    case_sensitive: bool = False,
    remove_tag: bool = False,
    ignore_words: set = None,
    ignore_punctuation: bool = False,
) -> List[str]:
    """
    Normalize the input text.

    Args:
        text: The input text.
        to_char: Whether to tokenize to character.
        case_sensitive: Whether to be case sensitive.
        remove_tag: Whether to remove the tags.
        ignore_words: The words to ignore.
        ignore_punctuation: Whether to ignore punctuation (except single quotes).
    Returns:
        The list of normalized tokens.
    """
    tokens = tokenize(text, to_char, ignore_punctuation)
    tokens = (strip_tags(token) if remove_tag else token for token in tokens)
    tokens = (token.upper() if not case_sensitive else token for token in tokens)
    if ignore_words is None:
        ignore_words = set()
    return [token for token in tokens if token and token not in ignore_words]


def wer(
    reference: str,
    hypothesis: str,
    to_char: bool = False,
    case_sensitive: bool = False,
    remove_tag: bool = False,
    ignore_words: set = None,
    ignore_punctuation: bool = False,
) -> WER:
    """
    Calculate the WER and align the reference and hypothesis.

    Args:
        reference: The reference text.
        hypothesis: The hypothesis text.
        to_char: Whether to tokenize to character.
        case_sensitive: Whether to be case sensitive.
        remove_tag: Whether to remove the tags.
        ignore_words: The words to ignore.
        ignore_punctuation: Whether to ignore punctuation (except single quotes).
    Returns:
        The WER of the reference and hypothesis.
    """
    reference = normalize(reference, to_char, case_sensitive, remove_tag, ignore_words, ignore_punctuation)
    hypothesis = normalize(hypothesis, to_char, case_sensitive, remove_tag, ignore_words, ignore_punctuation)
    return WER(reference, hypothesis)
