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
from typing import Any, Dict, Literal, Optional, Tuple

from compute_wer.utils import default_cluster, wer
from compute_wer.wer import SER, WER


class Calculator:

    def __init__(
        self,
        to_char: bool = False,
        fix_contractions: bool = False,
        to_kana: bool = False,
        case_sensitive: bool = False,
        remove_tag: bool = False,
        ignore_words: set = set(),
        max_wer: float = sys.maxsize,
        lang: Optional[Literal["auto", "en", "zh"]] = "auto",
        operator: Optional[Literal["tn", "itn"]] = None,
        traditional_to_simple: bool = False,
        full_to_half: bool = False,
        remove_interjections: bool = False,
        remove_puncts: bool = False,
        tag_oov: bool = False,
        enable_0_to_9: bool = False,
        remove_erhua: bool = False,
    ):
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
            full_to_half: Whether to convert full width characters to half width characters for text normalization.
            remove_interjections: Whether to remove interjections for text normalization.
            remove_puncts: Whether to remove punctuations for text normalization.
            tag_oov: Whether to tag OOV words for text normalization.
            enable_0_to_9: Whether to enable 0-9 for text normalization.
            remove_erhua: Whether to remove erhua for text normalization.
        """
        self.wer = partial(
            wer,
            to_char=to_char,
            fix_contractions=fix_contractions,
            to_kana=to_kana,
            case_sensitive=case_sensitive,
            remove_tag=remove_tag,
            ignore_words=ignore_words,
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
