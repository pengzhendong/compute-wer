# compute-wer

## Installation

```bash
$ pip install compute-wer
```

## Usage

```bash
$ cat ref.txt

/path/to/audio1 莫愁前路无知己
/path/to/audio2 天下谁人不识君
```

```bash
$ cat hyp.txt

/path/to/audio1 海内存知己
/path/to/audio2 天下谁人不识君
```

```bash
$ compute-wer ref.txt hyp.txt wer.txt
```

```bash
$ compute-wer "莫愁前路无知己" "海内存知己"
```

## Help

```bash
$ compute-wer --help
```
