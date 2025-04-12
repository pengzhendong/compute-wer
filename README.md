# compute-wer

## Usage

```bash
$ pip install compute-wer
$ compute-wer ref.txt hyp.txt output.txt
```

Each line of the `ref.txt` and `hyp.txt` should meet the following format:

```bash
$utt $text
```

or

```bash
$utt\t$text
```

## Help

```bash
$ compute-wer --help
```
