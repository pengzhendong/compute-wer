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

import sys

from edit_distance import DELETE, EQUAL, INSERT, REPLACE, SequenceMatcher


class WER:
    def __init__(self):
        self.equal = 0
        self.replace = 0
        self.delete = 0
        self.insert = 0

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    @property
    def all(self):
        return self.equal + self.replace + self.delete

    @property
    def wer(self):
        if self.all == 0:
            return 0
        return (self.replace + self.delete + self.insert) * 100 / self.all

    def __str__(self):
        return f"{self.wer:4.2f} % N={self.all} C={self.equal} S={self.replace} D={self.delete} I={self.insert}"

    @staticmethod
    def overall(wers):
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
    def all(self):
        return self.cor + self.err

    @property
    def ser(self):
        return self.err * 100 / self.all if self.all != 0 else 0

    def __str__(self):
        return f"{self.ser:4.2f} % N={self.all} C={self.cor} E={self.err}"


class Calculator:

    def __init__(self, max_wer=sys.maxsize):
        self.data = {}
        self.max_wer = max_wer
        self.ser = SER()

    def calculate(self, lab, rec):
        for token in set(lab + rec):
            self.data.setdefault(token, WER())
        opcodes = SequenceMatcher(lab, rec).get_opcodes()

        result = {"lab": [], "rec": [], "wer": WER()}
        for op, i, _, j, _ in opcodes:
            result["wer"][op] += 1
            result["lab"].append(lab[i] if op != INSERT else "")
            result["rec"].append(rec[j] if op != DELETE else "")

        self.ser.cor += result["wer"].wer == 0
        if result["wer"].wer < self.max_wer:
            for op, i, _, j, _ in opcodes:
                self.data[lab[i] if op != INSERT else rec[j]][op] += 1
            self.ser.err += result["wer"].wer > 0
        return result

    def overall(self):
        return WER.overall(self.data.values()), self.ser

    def cluster(self, data):
        return WER.overall((self.data.get(token) for token in data))
