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
from functools import partial
from typing import Dict, List, Literal, Optional
from unicodedata import category

from compute_wer.wer import WER

spacelist = [" ", "\t", "\r", "\n"]
puncts = [
    "!",
    ",",
    ".",
    "?",
    "-",
    "、",
    "。",
    "！",
    "，",
    "；",
    "？",
    "：",
    "「",
    "」",
    "︰",
    "『",
    "』",
    "《",
    "》",
]


def characterize(text: str, to_char: bool) -> List[str]:
    """
    Characterize the text.

    Args:
        text: The text to characterize.
        to_char: Whether to characterize to character.
    Returns:
        The list of characterized tokens
    """
    res = []
    i = 0
    length = len(text)
    while i < length:
        char = text[i]
        if char in puncts or char in spacelist:
            i += 1
            continue
        cat = category(char)
        # https://unicodebook.readthedocs.io/unicode.html#unicode-categories
        if cat in {"Zs", "Cn"}:  # space or not assigned
            i += 1
        elif cat == "Lo":  # Letter-other (Chinese letter)
            res.append(char)
            i += 1
        elif to_char and cat.startswith(("L", "N")):
            res.append(char)
            i += 1
        else:
            # some input looks like: <unk><noise>, we want to separate it to two words.
            sep = ">" if char == "<" else " "
            j = i + 1
            while j < length:
                c = text[j]
                if ord(c) >= 128 or c in spacelist or c == sep:
                    break
                j += 1
            if j < length and text[j] == ">":
                j += 1
            res.append(text[i:j])
            i = j
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
) -> List[str]:
    """
    Normalize the input text.

    Args:
        text: The input text.
        to_char: Whether to characterize to character.
        case_sensitive: Whether to be case sensitive.
        remove_tag: Whether to remove the tags.
        ignore_words: The words to ignore.
    Returns:
        The list of normalized tokens.
    """
    tokens = characterize(text, to_char)
    tokens = (strip_tags(token) if remove_tag else token for token in tokens)
    tokens = (token.upper() if not case_sensitive else token for token in tokens)
    if ignore_words is None:
        ignore_words = set()
    return [token for token in tokens if token and token not in ignore_words]


def wer(
    reference: str,
    hypothesis: str,
    to_char: bool = False,
    fix_contractions: bool = False,
    to_kana: bool = False,
    case_sensitive: bool = False,
    remove_tag: bool = False,
    ignore_words: set = None,
    lang: Optional[Literal["auto", "en", "zh"]] = "auto",
    operator: Optional[Literal["tn", "itn"]] = None,
    traditional_to_simple: bool = False,
    full_to_half: bool = False,
    remove_interjections: bool = False,
    remove_puncts: bool = False,
    tag_oov: bool = False,
    enable_0_to_9: bool = False,
    remove_erhua: bool = False,
) -> WER:
    """
    Calculate the WER and align the reference and hypothesis.

    Args:
        reference: The reference text.
        hypothesis: The hypothesis text.
        to_char: Whether to characterize to character.
        fix_contractions: Whether to fix the contractions for English.
        to_kana: Whether to convert the input text to kana (hiragana/katakana) for Japanese.
        case_sensitive: Whether to be case sensitive.
        remove_tag: Whether to remove the tags.
        ignore_words: The words to ignore.
        lang: The language for text normalization.
        operator: The operator for text normalization.
        traditional_to_simple: Whether to convert traditional Chinese to simplified Chinese for text normalization.
        full_to_half: Whether to convert full-width characters to half-width characters for text normalization.
        remove_interjections: Whether to remove interjections for text normalization.
        remove_puncts: Whether to remove punctuation for text normalization.
        tag_oov: Whether to tag out-of-vocabulary words for text normalization.
        remove_erhua: Whether to remove erhua for text normalization.
        enable_0_to_9: Whether to enable 0-to-9 conversion for text normalization.
    Returns:
        The WER of the reference and hypothesis.
    """

    if operator is not None:
        from wetext import normalize as wetext_normalize

        _normalize = partial(
            wetext_normalize,
            lang=lang,
            operator=operator,
            traditional_to_simple=traditional_to_simple,
            full_to_half=full_to_half,
            remove_interjections=remove_interjections,
            remove_puncts=remove_puncts,
            tag_oov=tag_oov,
            enable_0_to_9=enable_0_to_9,
            remove_erhua=remove_erhua,
        )
        reference = _normalize(reference)
        hypothesis = _normalize(hypothesis)

    _normalize = partial(
        normalize,
        to_char=to_char,
        case_sensitive=case_sensitive,
        remove_tag=remove_tag,
        ignore_words=ignore_words,
    )
    reference = _normalize(reference)
    hypothesis = _normalize(hypothesis)
    return WER(reference, hypothesis)
