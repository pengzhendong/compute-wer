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

import unicodedata
from unicodedata import category, east_asian_width

spacelist = [" ", "\t", "\r", "\n"]
puncts = ["!", ",", ".", "?", "-", "、", "。", "！", "，", "；", "？", "：", "「", "」", "︰", "『", "』", "《", "》"]


def characterize(text, tochar):
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
        elif tochar and cat.startswith("L"):
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


def strip_tags(token):
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
    return sum(1 + (east_asian_width(char) in "AFW") for char in str)
