# compute-wer

[![PyPI](https://img.shields.io/pypi/v/compute-wer)](https://pypi.org/project/compute-wer/)
[![License](https://img.shields.io/github/license/pengzhendong/compute-wer)](LICENSE)

A Python package for computing Word Error Rate (WER) and Sentence Error Rate (SER) for evaluating speech recognition systems.

## Features

- Compute WER and SER for speech recognition evaluation
- Support for both word-level and character-level WER calculation
- Detailed alignment visualization between reference and hypothesis texts
- Support for case-sensitive and case-insensitive matching
- Cluster-based error analysis (Chinese, English, Numbers, etc.)
- Text normalization with TN (Text Normalization) and ITN (Inverse Text Normalization)
- Support for filtering results based on maximum WER threshold
- Handle tagged text with option to remove tags

## Installation

```bash
pip install compute-wer
```

## Usage

### Command Line Interface

#### Basic Usage

Compute WER between reference and hypothesis texts:

```bash
# Compare two texts directly
compute-wer "你好世界" "你好"

# Compare texts from files
compute-wer ref.txt hyp.txt wer.txt
```

#### File Format

The input files should contain lines in the format `utterance_id text`. For example:

ref.txt:

```
utt1 你好世界
utt2 欢迎使用 compute-wer
```

hyp.txt:

```
utt1 你好
utt2 欢迎使用 computer-wer
```

#### Advanced Options

```bash
# Character-level WER
compute-wer --char ref.txt hyp.txt

# Case-sensitive matching
compute-wer --case-sensitive ref.txt hyp.txt

# Sort results by WER
compute-wer --sort ref.txt hyp.txt

# Remove tags from text
compute-wer --remove-tag ref.txt hyp.txt

# Use text normalizer
compute-wer --operator tn ref.txt hyp.txt

# Filter results with WER <= 50%
compute-wer --max-wer 0.5 ref.txt hyp.txt

# Ignore specific words from a file
compute-wer --ignore-file ignore_words.txt ref.txt hyp.txt
```

### Python API

```python
from compute_wer import Calculator

# Initialize calculator
calculator = Calculator(
    tochar=False,           # Character-level WER
    case_sensitive=False,   # Case-sensitive matching
    remove_tag=True,        # Remove tags from text
    operator=None,          # Text normalizer operator ("tn" or "itn")
    max_wer=float('inf')    # Maximum WER threshold
)

# Calculate WER
result = calculator.calculate("你好世界", "你好")
print(f"WER: {result['wer']}")
print(f"Reference : {' '.join(result['ref'])}")
print(f"Hypothesis: {' '.join(result['hyp'])}")

# Get overall statistics
overall_wer, cluster_wers = calculator.overall()
print(f"Overall WER: {overall_wer}")
for cluster, wer in cluster_wers.items():
    print(f"{cluster} WER: {wer}")
```

## CLI Options

| Option                    | Description                                       |
| ------------------------- | ------------------------------------------------- |
| `--char`, `-c`            | Use character-level WER instead of word-level WER |
| `--sort`, `-s`            | Sort the hypotheses by WER in ascending order     |
| `--case-sensitive`, `-cs` | Use case-sensitive matching                       |
| `--remove-tag`, `-rt`     | Remove tags from the reference and hypothesis     |
| `--ignore-file`, `-ig`    | Path to the ignore file                           |
| `--operator`, `-o`        | Normalizer operator (tn or itn)                   |
| `--max-wer`, `-mw`        | Filter hypotheses with WER <= this value          |
| `--verbose`, `-v`         | Print verbose output                              |

## Output Format

The output includes detailed alignment information:

```
utt: utt1
WER: 50.00 % N=4 Cor=2 Sub=0 Del=2 Ins=0
ref: 你 好 世 界
hyp: 你 好

===========================================================================
Overall -> 50.00 % N=4 Cor=2 Sub=0 Del=2 Ins=0
Chinese -> 50.00 % N=4 Cor=2 Sub=0 Del=2 Ins=0
SER -> 100.00 % N=1 Cor=0 Err=1 ML=1 MH=0
===========================================================================
```

Where:

- `N`: Total number of reference words/characters
- `Cor`: Correct matches
- `Sub`: Substitutions
- `Del`: Deletions
- `Ins`: Insertions
- `SER`: Sentence Error Rate
- `ML`: Missing Labels (Extra Hypotheses)
- `MH`: Missing Hypotheses (Extra Labels)

## License

[MIT License](LICENSE)
