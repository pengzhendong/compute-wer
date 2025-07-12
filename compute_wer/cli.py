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
import logging
import os
import sys

import click

from compute_wer.calculator import Calculator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@click.command(help="Compute Word Error Rate (WER) and align recognition results with references.")
@click.argument("ref")
@click.argument("hyp")
@click.argument("output-file", type=click.Path(dir_okay=False), required=False)
@click.option("--char", "-c", is_flag=True, default=False, help="Use character-level WER instead of word-level WER.")
@click.option("--sort", "-s", is_flag=True, default=False, help="Sort the hypotheses by WER in ascending order.")
@click.option("--case-sensitive", "-cs", is_flag=True, default=False, help="Use case-sensitive matching.")
@click.option("--remove-tag", "-rt", is_flag=True, default=True, help="Remove tags from the reference and hypothesis.")
@click.option("--ignore-file", "-ig", type=click.Path(exists=True, dir_okay=False), help="Path to the ignore file.")
@click.option("--verbose", "-v", is_flag=True, default=True, help="Print verbose output.")
@click.option("--max-wer", "-mw", type=float, default=sys.maxsize, help="Filter hypotheses with WER <= this value.")
def main(ref, hyp, output_file, char, sort, case_sensitive, remove_tag, ignore_file, verbose, max_wer):
    input_is_file = False
    if os.path.exists(ref):
        assert os.path.exists(hyp)
        input_is_file = True

    ignore_words = set()
    if ignore_file is not None:
        for line in codecs.open(ignore_file, encoding="utf-8"):
            word = line.strip()
            if len(word) > 0:
                ignore_words.add(word if case_sensitive else word.upper())
    calculator = Calculator(char, case_sensitive, remove_tag, ignore_words, max_wer)

    if input_is_file:
        hyp_set = {}
        for line in codecs.open(hyp, encoding="utf-8"):
            array = line.strip().split(maxsplit=1)
            if len(array) == 0:
                continue
            utt, hyp = array[0], array[1] if len(array) > 1 else ""
            if utt in hyp_set:
                if hyp != hyp_set[utt]:
                    raise ValueError(f"Conflicting hypotheses found:\n{utt}\t{hyp}\n{utt}\t{hyp_set[utt]}")
                logging.warning(f"Skip duplicate hypothesis: {utt}\t{hyp}")
            hyp_set[utt] = hyp

    results = []
    if input_is_file:
        ref_set = {}
        for line in codecs.open(ref, encoding="utf-8"):
            array = line.strip().split(maxsplit=1)
            if len(array) == 0 or array[0] not in hyp_set:
                continue
            utt, ref = array[0], array[1] if len(array) > 1 else ""
            if utt in ref_set:
                if ref != ref_set[utt]:
                    raise ValueError(f"Conflicting references found:\n{utt}\t{ref}\n{utt}\t{ref_set[utt]}")
                logging.warning(f"Skip duplicate reference: {utt}\t{ref}")
            ref_set[utt] = ref
            result = calculator.calculate(ref, hyp_set[utt])
            if result["wer"].wer < max_wer:
                results.append((utt, result))
    else:
        results.append((None, calculator.calculate(ref, hyp)))

    fout = sys.stdout
    if output_file is None:
        fout.write("\n")
    else:
        fout = codecs.open(output_file, "w", encoding="utf-8")

    if verbose:
        if sort:
            results = sorted(results, key=lambda x: x[1]["wer"].wer)
        for utt, result in results:
            if utt is not None:
                fout.write(f"utt: {utt}\n")
            fout.write(f"WER: {result['wer']}\n")
            for key in ("ref", "hyp"):
                fout.write(f"{key}: {' '.join(result[key])}\n")
            fout.write("\n")
    fout.write("===========================================================================\n")
    wer, cluster_wers = calculator.overall()
    fout.write(f"Overall -> {wer}\n")
    for cluster, wer in cluster_wers.items():
        fout.write(f"{cluster} -> {wer}\n")
    if input_is_file:
        fout.write(f"SER -> {calculator.ser}\n")
    fout.write("===========================================================================\n")
    fout.close()


if __name__ == "__main__":
    main()
