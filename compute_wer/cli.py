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
from collections import defaultdict

import click

from .calculator import Calculator
from .utils import characterize, default_cluster, normalize, width


@click.command(help="Compute Word Error Rate (WER) and align recognition results with references.")
@click.argument("ref", type=click.Path(exists=True, dir_okay=False))
@click.argument("hyp", type=click.Path(exists=True, dir_okay=False))
@click.option("--char/--word", default=False)
@click.option("--sort", "--s", is_flag=True, default=False)
@click.option("--case-sensitive", "--cs", is_flag=True, default=False)
@click.option("--remove-tag", "--rt", is_flag=True, default=True)
@click.option("--ignore-file", "--ig", type=click.Path(exists=True, dir_okay=False))
@click.option("--verbose", "--v", is_flag=True, default=True)
def main(ref, hyp, char, sort, case_sensitive, remove_tag, ignore_file, verbose):
    ignore_words = set()
    if ignore_file is not None:
        for line in codecs.open(ignore_file, encoding="utf-8"):
            word = line.strip()
            if len(word) > 0:
                ignore_words.add(word if case_sensitive else word.upper())

    rec_set = {}
    for line in codecs.open(hyp, encoding="utf-8"):
        array = line.strip().split(maxsplit=1)
        if len(array) == 0:
            continue
        utt, text = array[0], array[1] if len(array) > 1 else ""
        tokens = characterize(text, char)
        rec_set[utt] = normalize(tokens, ignore_words, case_sensitive, remove_tag)

    calculator = Calculator()
    clusters = defaultdict(set)
    words = set()
    results = []
    for line in codecs.open(ref, encoding="utf-8"):
        array = line.strip().split(maxsplit=1)
        if len(array) == 0 or array[0] not in rec_set:
            continue
        utt, text = array[0], array[1] if len(array) > 1 else ""
        rec = rec_set[utt]
        tokens = characterize(text, char)
        lab = normalize(tokens, ignore_words, case_sensitive, remove_tag)
        for word in set(rec + lab) - words:
            words.add(word)
            clusters[default_cluster(word)].add(word)
        results.append((utt, calculator.calculate(lab, rec)))

    if verbose:
        if sort:
            results = sorted(results, key=lambda x: x[1]["wer"].wer)
        for utt, result in results:
            print(f"utt: {utt}\nWER: {result['wer']}")
            lengths = [max(width(lab), width(rec)) for lab, rec in zip(result["lab"], result["rec"])]
            for key in ("lab", "rec"):
                text = " ".join((token + " " * (length - width(token)) for token, length in zip(result[key], lengths)))
                print(f"{key}: {text}")
            print()
    print("===========================================================================\n")
    wer, ser = calculator.overall()
    print(f"Overall -> {wer}")
    for name, cluster in clusters.items():
        wer = calculator.cluster(cluster)
        if wer.all > 0:
            print(f"{name} -> {wer}")
    print(f"SER -> {ser}")
    print("\n===========================================================================")


if __name__ == "__main__":
    main()
