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
from functools import partial
from typing import Any, Dict, Tuple

from compute_wer.utils import default_cluster, wer
from compute_wer.wer import SER, WER


class Calculator:
    def __init__(
        self,
        to_char: bool = False,
        case_sensitive: bool = False,
        remove_tag: bool = False,
        ignore_words: set = set(),
        max_wer: float = sys.maxsize,
    ):
        """
        Calculate the WER and align the reference and hypothesis.

        Args:
            reference: The reference text.
            hypothesis: The hypothesis text.
            to_char: Whether to characterize to character.
            case_sensitive: Whether to be case sensitive.
            remove_tag: Whether to remove the tags.
            ignore_words: The words to ignore.
        """
        self.wer = partial(
            wer, to_char=to_char, case_sensitive=case_sensitive, remove_tag=remove_tag, ignore_words=ignore_words
        )
        self.clusters = defaultdict(set)
        self.tokens = defaultdict(WER)
        self.max_wer = max_wer
        self.ser = SER()

    def calculate(self, reference: str, hypothesis: str) -> Dict[str, Any]:
        """
        Calculate the WER for the reference and hypothesis.

        Args:
            reference: The reference text.
            hypothesis: The hypothesis text.
        Returns:
            result: The WER result.
        """
        _wer = self.wer(reference, hypothesis)
        if _wer.wer < self.max_wer:
            for token in _wer.tokens:
                self.clusters[default_cluster(token)].add(token)
                self.tokens[token].update(_wer.tokens[token])
            if _wer.wer == 0:
                self.ser.cor += 1
            else:
                self.ser.err += 1
        return _wer

    def cluster(self, tokens) -> WER:
        """
        Calculate the WER for a cluster.

        Args:
            tokens: The list of tokens.
        Returns:
            The WER for the cluster.
        """
        return WER.overall((self.tokens.get(token) for token in tokens))

    def overall(self) -> Tuple[WER, Dict[str, WER]]:
        """
        Calculate the overall WER and the WER for each cluster.

        Returns:
            The overall WER.
            The WER for each cluster.
        """
        cluster_wers = {}
        for name, cluster in self.clusters.items():
            _wer = self.cluster(cluster)
            if _wer.all > 0:
                cluster_wers[name] = _wer
        return WER.overall(self.tokens.values()), cluster_wers
