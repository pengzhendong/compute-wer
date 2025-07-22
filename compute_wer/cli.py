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
from compute_wer.utils import read_scp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@click.command(help="Compute Word Error Rate (WER) and align recognition results with references.")
@click.argument("ref")
@click.argument("hyp")
@click.argument("output-file", type=click.Path(dir_okay=False), required=False)
@click.option(
    "--align-to-hyp",
    is_flag=True,
    help="If set, align to hypothesis (default: align to reference)",
)
@click.option(
    "--char",
    "-c",
    is_flag=True,
    help="Use character-level WER instead of word-level WER.",
)
@click.option("--sort", "-s", is_flag=True, help="Sort the hypotheses by WER in ascending order.")
@click.option("--case-sensitive", "-cs", is_flag=True, help="Use case-sensitive matching.")
@click.option(
    "--remove-tag",
    "-rt",
    is_flag=True,
    default=True,
    help="Remove tags from the reference and hypothesis.",
)
@click.option(
    "--ignore-file",
    "-ig",
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the ignore file.",
)
@click.option(
    "--operator",
    "-o",
    type=click.Choice(["tn", "itn"], case_sensitive=False),
    help="Normalizer operator.",
)
@click.option("--verbose", "-v", is_flag=True, default=True, help="Print verbose output.")
@click.option(
    "--max-wer",
    "-mw",
    type=float,
    default=sys.maxsize,
    help="Filter hypotheses with WER <= this value.",
)
def main(
    ref,
    hyp,
    output_file,
    align_to_hyp,
    char,
    sort,
    case_sensitive,
    remove_tag,
    ignore_file,
    operator,
    verbose,
    max_wer,
):
    input_is_file = os.path.exists(ref)
    assert os.path.exists(hyp) == input_is_file

    ignore_words = set()
    if ignore_file is not None:
        for line in codecs.open(ignore_file, encoding="utf-8"):
            word = line.strip()
            if len(word) > 0:
                ignore_words.add(word if case_sensitive else word.upper())
    calculator = Calculator(char, case_sensitive, remove_tag, ignore_words, operator, max_wer)

    results = []
    if input_is_file:
        hyps = read_scp(hyp)
        refs = read_scp(ref)
        ref_utts = set(refs.keys())
        hyp_utts = set(hyps.keys())

        if not align_to_hyp:
            for utt in ref_utts - hyp_utts:
                hyps[utt] = ""
                hyp_utts.add(utt)
                logging.warning(f"No hypothesis found for {utt}, use empty string as hypothesis.")
        for utt in hyp_utts & ref_utts:
            result = calculator.calculate(refs[utt], hyps[utt])
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
        # ML: Missing Labels(Extra Hypotheses)
        # MH: Missing Hypotheses(Extra Labels)
        fout.write(f"SER -> {calculator.ser} ML={len(hyp_utts - ref_utts)} MH={len(ref_utts - hyp_utts)}\n")
    fout.write("===========================================================================\n")
    fout.close()


if __name__ == "__main__":
    main()
