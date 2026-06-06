import os
import tempfile

import pytest

from compute_wer.utils import (
    char_name,
    default_cluster,
    is_character_based,
    is_punctuation,
    normalize,
    read_scp,
    strip_tags,
    tokenize,
    wer,
)


class TestIsPunctuation:
    def test_common_punctuation(self):
        for ch in ".,;:!?":
            assert is_punctuation(ch)

    def test_symbols(self):
        for ch in "$+<=>":
            assert is_punctuation(ch)

    def test_not_punctuation(self):
        for ch in "abcABC123":
            assert not is_punctuation(ch)


class TestIsCharacterBased:
    def test_chinese(self):
        assert is_character_based("你")
        assert is_character_based("好")

    def test_japanese_hiragana(self):
        assert is_character_based("あ")

    def test_japanese_katakana(self):
        assert is_character_based("ア")

    def test_thai(self):
        assert is_character_based("ก")  # Thai character Ko Kai

    def test_latin_not_character_based(self):
        assert not is_character_based("a")
        assert not is_character_based("Z")

    def test_digit_not_character_based(self):
        assert not is_character_based("5")


class TestTokenize:
    def test_english_words(self):
        assert tokenize("hello world") == ["hello", "world"]

    def test_chinese_characters(self):
        assert tokenize("你好世界") == ["你", "好", "世", "界"]

    def test_mixed_chinese_english(self):
        tokens = tokenize("hello你好world")
        assert tokens == ["hello", "你", "好", "world"]

    def test_numbers(self):
        assert tokenize("test123 abc") == ["test123", "abc"]

    def test_punctuation_ignored(self):
        assert tokenize("hello, world!") == ["hello", "world"]

    def test_punctuation_kept(self):
        assert tokenize("hello, world!", ignore_punctuation=False) == ["hello", ",", "world", "!"]

    def test_single_quote_kept_in_word(self):
        tokens = tokenize("it's a test")
        assert "it's" in tokens

    def test_to_char_mode(self):
        tokens = tokenize("hello", to_char=True)
        assert tokens == ["h", "e", "l", "l", "o"]

    def test_empty_string(self):
        assert tokenize("") == []

    def test_whitespace_only(self):
        assert tokenize("   ") == []


class TestStripTags:
    def test_remove_tag(self):
        assert strip_tags("<unk>hello") == "hello"

    def test_multiple_tags(self):
        assert strip_tags("<s>hello</s>") == "hello"

    def test_no_tags(self):
        assert strip_tags("hello") == "hello"

    def test_unclosed_tag(self):
        assert strip_tags("<hello") == "<hello"

    def test_empty(self):
        assert strip_tags("") == ""


class TestNormalize:
    def test_basic(self):
        tokens = normalize("Hello World")
        assert tokens == ["HELLO", "WORLD"]

    def test_case_sensitive(self):
        tokens = normalize("Hello World", case_sensitive=True)
        assert tokens == ["Hello", "World"]

    def test_remove_tag(self):
        # With default ignore_punctuation=True, <> are stripped as punctuation
        # remove_tag applies strip_tags to each token after tokenization
        tokens = normalize("hello world", remove_tag=True)
        assert tokens == ["HELLO", "WORLD"]

    def test_remove_tag_with_punctuation_kept(self):
        # strip_tags removes <tag> content from within a token
        tokens = normalize("<unk>hello", remove_tag=True, ignore_punctuation=False)
        assert "HELLO" in tokens

    def test_ignore_words(self):
        tokens = normalize("hello world foo", ignore_words={"HELLO"})
        assert tokens == ["WORLD", "FOO"]

    def test_to_char(self):
        tokens = normalize("hi", to_char=True)
        assert tokens == ["H", "I"]

    def test_chinese(self):
        tokens = normalize("你好世界")
        assert tokens == ["你", "好", "世", "界"]


class TestCharName:
    def test_ascii(self):
        name = char_name("A")
        assert "LATIN" in name

    def test_soh(self):
        assert char_name("\x01") == "SOH"

    def test_chinese(self):
        name = char_name("你")
        assert "CJK" in name


class TestDefaultCluster:
    def test_english(self):
        assert default_cluster("hello") == "English"

    def test_chinese(self):
        assert default_cluster("你") == "Chinese"

    def test_number(self):
        assert default_cluster("123") == "Number"

    def test_japanese_hiragana(self):
        assert default_cluster("あ") == "Japanese"

    def test_mixed_returns_other(self):
        assert default_cluster("hello你") == "Other"


class TestReadScp:
    def test_basic(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".scp", delete=False, encoding="utf-8") as f:
            f.write("utt1 hello world\n")
            f.write("utt2 foo bar\n")
            f.name
        try:
            result = read_scp(f.name)
            assert result == {"utt1": "hello world", "utt2": "foo bar"}
        finally:
            os.unlink(f.name)

    def test_empty_text(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".scp", delete=False, encoding="utf-8") as f:
            f.write("utt1\n")
        try:
            result = read_scp(f.name)
            assert result == {"utt1": ""}
        finally:
            os.unlink(f.name)

    def test_skip_empty_lines(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".scp", delete=False, encoding="utf-8") as f:
            f.write("utt1 hello\n\n\nutt2 world\n")
        try:
            result = read_scp(f.name)
            assert len(result) == 2
        finally:
            os.unlink(f.name)

    def test_conflicting_text_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".scp", delete=False, encoding="utf-8") as f:
            f.write("utt1 hello\nutt1 world\n")
        try:
            with pytest.raises(ValueError):
                read_scp(f.name)
        finally:
            os.unlink(f.name)

    def test_duplicate_same_text_ok(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".scp", delete=False, encoding="utf-8") as f:
            f.write("utt1 hello\nutt1 hello\n")
        try:
            result = read_scp(f.name)
            assert result == {"utt1": "hello"}
        finally:
            os.unlink(f.name)


class TestWerFunction:
    def test_identical(self):
        result = wer("hello world", "hello world")
        assert result.wer == 0.0

    def test_completely_wrong(self):
        result = wer("hello world", "foo bar")
        assert result.wer == 1.0

    def test_case_insensitive_default(self):
        result = wer("Hello World", "hello world")
        assert result.wer == 0.0

    def test_case_sensitive(self):
        result = wer("Hello World", "hello world", case_sensitive=True)
        assert result.wer == 1.0

    def test_char_mode(self):
        result = wer("abc", "axc", to_char=True)
        assert result.replace == 1
        assert result.equal == 2

    def test_remove_tag(self):
        result = wer("hello world", "hello world", remove_tag=True)
        assert result.wer == 0.0

    def test_ignore_words(self):
        result = wer("um hello world", "hello world", ignore_words={"UM"})
        assert result.wer == 0.0

    def test_ignore_punctuation(self):
        result = wer("hello, world!", "hello world", ignore_punctuation=True)
        assert result.wer == 0.0
