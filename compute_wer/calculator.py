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

from edit_distance import SequenceMatcher


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

    def __str__(self):
        wer = 0
        all = self.equal + self.replace + self.delete
        if all > 0:
            wer = float(self.replace + self.delete + self.insert) * 100.0 / all
        return f"{wer:4.2f} % N={all} C={self.equal} S={self.replace} D={self.delete} I={self.insert}"

    @staticmethod
    def overall(wers):
        overall = WER()
        for wer in wers:
            if wer is None:
                continue
            for key in ("equal", "replace", "delete", "insert"):
                overall[key] += wer[key]
        return overall


class Calculator:

    def __init__(self):
        self.data = {}

    def calculate(self, lab, rec):
        for token in set(lab + rec):
            self.data.setdefault(token, WER())
        result = {"lab": [], "rec": [], "wer": WER()}

        i, j = 0, 0
        for op, *_ in SequenceMatcher(lab, rec).get_opcodes():
            result["wer"][op] += 1
            result["lab"].append(lab[i] if op != "insert" else "")
            result["rec"].append(rec[j] if op != "delete" else "")
            self.data[lab[i] if op != "insert" else rec[j]][op] += 1
            i += op != "insert"
            j += op != "delete"
        return result

    def overall(self):
        return WER.overall(self.data.values())

    def cluster(self, data):
        return WER.overall((self.data.get(token) for token in data))
