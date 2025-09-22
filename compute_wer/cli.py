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
@click.option(
    "--fix-contractions",
    "-fc",
    is_flag=True,
    help="Fix the contractions for English",
)
@click.option(
    "--kana",
    "-k",
    is_flag=True,
    help="Convert the text to kana (hiragana/katakana) for Japanese.",
)
@click.option(
    "--sort",
    "-s",
    type=click.Choice(["utt", "wer"], case_sensitive=False),
    help="Sort the hypotheses by utterance-id or WER in ascending order.",
)
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
    "--max-wer",
    "-mw",
    type=float,
    default=sys.maxsize,
    help="Filter hypotheses with WER <= this value.",
)
@click.option(
    "--lang",
    "-l",
    type=click.Choice(["auto", "en", "zh"], case_sensitive=False),
    default="auto",
    help="Language for normalization (default: 'auto').",
)
@click.option(
    "--operator",
    "-o",
    type=click.Choice(["tn", "itn"], case_sensitive=False),
    help="Normalizer operator.",
)
@click.option("--traditional-to-simple", is_flag=True, help="Convert traditional Chinese to simplified Chinese.")
@click.option("--full-to-half", is_flag=True, help="Convert full-width characters to half-width characters.")
@click.option("--remove-interjections", is_flag=True, help="Remove interjections.")
@click.option("--remove-puncts", is_flag=True, help="Remove punctuation.")
@click.option("--tag-oov", is_flag=True, help="Tag out-of-vocabulary words.")
@click.option("--enable-0-to-9", is_flag=True, help="Enable 0-to-9 conversion.")
@click.option("--remove-erhua", is_flag=True, help="Remove erhua.")
@click.option("--verbose", "-v", is_flag=True, default=True, help="Print verbose output.")
def main(
    ref,
    hyp,
    output_file,
    align_to_hyp,
    char,
    fix_contractions,
    kana,
    sort,
    case_sensitive,
    remove_tag,
    ignore_file,
    max_wer,
    lang,
    operator,
    traditional_to_simple,
    full_to_half,
    remove_interjections,
    remove_puncts,
    tag_oov,
    enable_0_to_9,
    remove_erhua,
    verbose,
):
    input_is_file = os.path.exists(ref)
    assert os.path.exists(hyp) == input_is_file

    ignore_words = set()
    if ignore_file is not None:
        for line in codecs.open(ignore_file, encoding="utf-8"):
            word = line.strip()
            if len(word) > 0:
                ignore_words.add(word if case_sensitive else word.upper())
    calculator = Calculator(
        char,
        fix_contractions,
        kana,
        case_sensitive,
        remove_tag,
        ignore_words,
        max_wer,
        lang,
        operator,
        traditional_to_simple,
        full_to_half,
        remove_interjections,
        remove_puncts,
        tag_oov,
        enable_0_to_9,
        remove_erhua,
    )

    wers = []
    if input_is_file:
        hyps = read_scp(hyp)
        refs = read_scp(ref)
        ref_utts = set(refs.keys())
        hyp_utts = set(hyps.keys())

        if not align_to_hyp:
            for utt in ref_utts - hyp_utts:
                hyps[utt] = ""
                hyp_utts.add(utt)
                logging.warning("No hypothesis found for %s, use empty string as hypothesis.", utt)
        for utt in hyp_utts & ref_utts:
            wer = calculator.calculate(refs[utt], hyps[utt])
            if wer.wer <= max_wer:
                wers.append((utt, wer))
    else:
        wer = calculator.calculate(ref, hyp)
        wers.append((None, wer))

    fout = sys.stdout
    if output_file is None:
        fout.write("\n")
    else:
        fout = codecs.open(output_file, "w", encoding="utf-8")

    if verbose:
        if sort is not None:
            wers = sorted(wers, key=lambda x: x[0] if sort == "utt" else x[1].wer)
        for utt, wer in wers:
            if utt is not None:
                fout.write(f"utt: {utt}\n")
            fout.write(f"WER: {wer}\n")
            fout.write(f"ref: {' '.join(wer.reference)}\n")
            fout.write(f"hyp: {' '.join(wer.hypothesis)}\n\n")
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
