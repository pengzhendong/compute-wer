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

from collections import defaultdict
from typing import List, Optional
from unicodedata import east_asian_width

from edit_distance import DELETE, EQUAL, INSERT, REPLACE, SequenceMatcher


class WER:
    def __init__(self, reference: Optional[List[str]] = None, hypothesis: Optional[List[str]] = None):
        self.equal = 0
        self.replace = 0
        self.delete = 0
        self.insert = 0

        if reference is not None and hypothesis is not None:
            self.reference = []
            self.hypothesis = []
            self.tokens = defaultdict(WER)

            matcher = SequenceMatcher(reference, hypothesis)
            for op, i, _, j, _ in matcher.get_opcodes():
                setattr(self, op, getattr(self, op) + 1)
                # For the cluster WER
                token = reference[i] if op != INSERT else hypothesis[j]
                if token not in self.tokens:
                    self.tokens[token] = WER()
                self.tokens[token][op] += 1

                ref_token = reference[i] if op != INSERT else ""
                hyp_token = hypothesis[j] if op != DELETE else ""
                diff = WER.width(hyp_token) - WER.width(ref_token)
                self.reference.append(ref_token + " " * diff)
                self.hypothesis.append(hyp_token + " " * -diff)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    @staticmethod
    def width(token: str) -> int:
        """
        Get the width of a token.

        Args:
            token: The token to get the width.
        Returns:
            The width of the token.
        """
        return sum(1 + (east_asian_width(char) in "AFW") for char in token)

    @property
    def all(self) -> int:
        return self.equal + self.replace + self.delete

    @property
    def wer(self) -> float:
        if self.all == 0:
            return 0
        return (self.replace + self.delete + self.insert) / self.all

    def __str__(self) -> str:
        return f"{self.wer * 100:4.2f} % N={self.all} Cor={self.equal} Sub={self.replace} Del={self.delete} Ins={self.insert}"

    def update(self, other: "WER"):
        """
        Update this WER with another WER.

        Args:
            other (WER): The other WER.
        """
        self.equal += other.equal
        self.replace += other.replace
        self.delete += other.delete
        self.insert += other.insert

    @staticmethod
    def overall(wers: List["WER"]) -> "WER":
        """
        Calculate the overall WER.

        Args:
            wers: The list of WERs.
        Returns:
            The overall WER.
        """
        overall = WER()
        for wer in wers:
            if wer is None:
                continue
            for key in (EQUAL, REPLACE, DELETE, INSERT):
                overall[key] += wer[key]
        return overall


class SER:
    def __init__(self):
        self.cor = 0
        self.err = 0

    @property
    def all(self) -> int:
        return self.cor + self.err

    @property
    def ser(self) -> float:
        return self.err / self.all if self.all != 0 else 0

    def __str__(self) -> str:
        return f"{self.ser * 100:4.2f} % N={self.all} Cor={self.cor} Err={self.err}"
