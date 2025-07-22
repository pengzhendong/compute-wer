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
from unicodedata import category, east_asian_width

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


def characterize(text, tochar):
    """
    Characterize the text.
    Args:
        text: text to characterize
        tochar: whether to characterize to character
    Returns:
        list of characterized tokens
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
        elif tochar and cat.startswith(("L", "N")):
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


def default_cluster(word):
    """
    Get the default cluster of a word.
    Args:
        word: word to get the default cluster
    Returns:
        default cluster
    """
    replacements = {
        "DIGIT": "Number",
        "CJK UNIFIED IDEOGRAPH": "Chinese",
        "CJK COMPATIBILITY IDEOGRAPH": "Chinese",
        "LATIN CAPITAL LETTER": "English",
        "LATIN SMALL LETTER": "English",
        "HIRAGANA LETTER": "Japanese",
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
    )
    clusters = set()
    for name in [unicodedata.name(char) for char in word]:
        if any(name.startswith(prefix) for prefix in ignored_prefixes):
            continue
        cluster = "Other"
        for key, value in replacements.items():
            if name.startswith(key):
                cluster = value
                break
        clusters.add(cluster or "Other")
    return clusters.pop() if len(clusters) == 1 else "Other"


def read_scp(scp_path):
    """
    Read the scp file and return a dictionary of utterance to text.
    Args:
        scp_path: path to the scp file
    Returns:
        dictionary of utterance to text
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


def strip_tags(token):
    """
    Strip the tags from the token.
    Args:
        token: token to strip the tags
    Returns:
        token without tags
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


def width(str):
    """
    Get the width of a string.
    Args:
        str: string to get the width
    Returns:
        width of the string
    """
    return sum(1 + (east_asian_width(char) in "AFW") for char in str)
