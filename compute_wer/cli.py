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
import sys

import click

from .calculator import Calculator


@click.command(help="Compute Word Error Rate (WER) and align recognition results with references.")
@click.argument("ref", type=click.Path(exists=True, dir_okay=False))
@click.argument("hyp", type=click.Path(exists=True, dir_okay=False))
@click.argument("output", type=click.Path(dir_okay=False))
@click.option("--char", "-c", is_flag=True, default=False, help="Use character-level WER instead of word-level WER.")
@click.option("--sort", "-s", is_flag=True, default=False, help="Sort the results by WER in ascending order.")
@click.option("--case-sensitive", "-cs", is_flag=True, default=False, help="Use case-sensitive matching.")
@click.option("--remove-tag", "-rt", is_flag=True, default=True, help="Remove tags from the reference and hypothesis.")
@click.option("--ignore-file", "-ig", type=click.Path(exists=True, dir_okay=False), help="Path to the ignore file.")
@click.option("--verbose", "-v", is_flag=True, default=True, help="Print verbose output.")
@click.option("--max-wer", "-mw", type=float, default=sys.maxsize, help="Filter results with WER <= this value.")
def main(ref, hyp, output, char, sort, case_sensitive, remove_tag, ignore_file, verbose, max_wer):
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
        utt, rec = array[0], array[1] if len(array) > 1 else ""
        rec_set[utt] = rec

    calculator = Calculator(char, case_sensitive, remove_tag, ignore_words, max_wer)
    results = []
    for line in codecs.open(ref, encoding="utf-8"):
        array = line.strip().split(maxsplit=1)
        if len(array) == 0 or array[0] not in rec_set:
            continue
        utt, lab = array[0], array[1] if len(array) > 1 else ""
        result = calculator.calculate(lab, rec_set[utt])
        if result["wer"].wer < max_wer:
            results.append((utt, result))

    fout = codecs.open(output, "w", encoding="utf-8")
    if verbose:
        if sort:
            results = sorted(results, key=lambda x: x[1]["wer"].wer)
        for utt, result in results:
            fout.write(f"utt: {utt}\nWER: {result['wer']}\n")
            for key in ("lab", "rec"):
                fout.write(f"{key}: {' '.join(result[key])}\n")
            fout.write("\n")
    fout.write("===========================================================================\n")
    wer, cluster_wers = calculator.overall()
    fout.write(f"Overall -> {wer}\n")
    for cluster, wer in cluster_wers.items():
        fout.write(f"{cluster} -> {wer}\n")
    fout.write(f"SER -> {calculator.ser}\n")
    fout.write("===========================================================================\n")
    fout.close()


if __name__ == "__main__":
    main()
