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
from collections import defaultdict

import contractions
from edit_distance import DELETE, EQUAL, INSERT, REPLACE, SequenceMatcher
from wetext import Normalizer

from compute_wer.utils import characterize, default_cluster, strip_tags, width


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
        return (self.replace + self.delete + self.insert) / self.all

    def __str__(self):
        return f"{self.wer * 100:4.2f} % N={self.all} Cor={self.equal} Sub={self.replace} Del={self.delete} Ins={self.insert}"

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
        return self.err / self.all if self.all != 0 else 0

    def __str__(self):
        return f"{self.ser * 100:4.2f} % N={self.all} Cor={self.cor} Err={self.err}"


class Calculator:

    def __init__(
        self,
        tochar: bool = False,
        case_sensitive: bool = False,
        remove_tag: bool = False,
        ignore_words: set = set(),
        operator: str = None,
        max_wer: float = sys.maxsize,
    ):
        self.tochar = tochar
        self.case_sensitive = case_sensitive
        self.remove_tag = remove_tag
        self.ignore_words = ignore_words
        self.normalizer = None if operator is None else Normalizer(operator=operator)

        self.clusters = defaultdict(set)
        self.data = {}
        self.max_wer = max_wer
        self.ser = SER()

    def normalize(self, text):
        """
        Normalize the input text.
        Args:
            text: input text
        Returns:
            list of normalized tokens
        """
        text = contractions.fix(text)
        if self.normalizer is not None:
            text = self.normalizer.normalize(text)
        tokens = characterize(text, self.tochar)
        tokens = (strip_tags(token) if self.remove_tag else token for token in tokens)
        tokens = (token.upper() if not self.case_sensitive else token for token in tokens)
        return [token for token in tokens if token and token not in self.ignore_words]

    def calculate(self, ref, hyp):
        """
        Calculate the WER and align the reference and hypothesis.
        Args:
            ref: reference text
            hyp: hypothesis text
        Returns:
            result: result of the WER calculation
        """
        ref = self.normalize(ref)
        hyp = self.normalize(hyp)
        for token in set(ref + hyp):
            if token not in self.data:
                self.data[token] = WER()
                self.clusters[default_cluster(token)].add(token)
        opcodes = SequenceMatcher(ref, hyp).get_opcodes()

        result = {"ref": [], "hyp": [], "wer": WER()}
        for op, i, _, j, _ in opcodes:
            result["wer"][op] += 1
            ref_token = ref[i] if op != INSERT else ""
            hyp_token = hyp[j] if op != DELETE else ""
            diff = width(hyp_token) - width(ref_token)
            result["ref"].append(ref_token + " " * diff)
            result["hyp"].append(hyp_token + " " * -diff)

        self.ser.cor += result["wer"].wer == 0
        if result["wer"].wer < self.max_wer:
            for op, i, _, j, _ in opcodes:
                self.data[ref[i] if op != INSERT else hyp[j]][op] += 1
            self.ser.err += result["wer"].wer > 0
        return result

    def cluster(self, data):
        """
        Calculate the WER for a cluster.
        Args:
            data: list of tokens
        Returns:
            WER for the cluster
        """
        return WER.overall((self.data.get(token) for token in data))

    def overall(self):
        """
        Calculate the overall WER and the WER for each cluster.
        Returns:
            overall WER
            WER for each cluster
        """
        cluster_wers = {}
        for name, cluster in self.clusters.items():
            wer = self.cluster(cluster)
            if wer.all > 0:
                cluster_wers[name] = wer
        return WER.overall(self.data.values()), cluster_wers
