import pytest

from compute_wer.calculator import Calculator


class TestCalculator:
    def test_basic_calculation(self):
        calc = Calculator()
        result = calc.calculate("hello world", "hello world")
        assert result.wer == 0.0

    def test_ser_tracking(self):
        calc = Calculator()
        calc.calculate("hello world", "hello world")
        calc.calculate("foo bar", "foo baz")
        assert calc.ser.cor == 1
        assert calc.ser.err == 1

    def test_overall(self):
        calc = Calculator()
        calc.calculate("hello world", "hello world")
        calc.calculate("foo bar", "foo baz")
        overall_wer, cluster_wers = calc.overall()
        assert overall_wer.wer == pytest.approx(1 / 4)

    def test_cluster_wer(self):
        calc = Calculator()
        calc.calculate("hello world", "hello earth")
        _, cluster_wers = calc.overall()
        assert "English" in cluster_wers

    def test_chinese_cluster(self):
        calc = Calculator()
        calc.calculate("你好世界", "你好地球")
        _, cluster_wers = calc.overall()
        assert "Chinese" in cluster_wers

    def test_char_mode(self):
        calc = Calculator(to_char=True)
        result = calc.calculate("abc", "axc")
        assert result.equal == 2
        assert result.replace == 1

    def test_case_sensitive(self):
        calc = Calculator(case_sensitive=True)
        result = calc.calculate("Hello", "hello")
        assert result.wer == 1.0

    def test_remove_tag(self):
        calc = Calculator(remove_tag=True)
        # With default settings, <unk> is stripped as punctuation anyway
        result = calc.calculate("hello world", "hello world")
        assert result.wer == 0.0

    def test_ignore_words(self):
        calc = Calculator(ignore_words={"UM"})
        result = calc.calculate("um hello", "hello")
        assert result.wer == 0.0

    def test_max_wer_filters(self):
        calc = Calculator(max_wer=0.5)
        calc.calculate("a b c d", "a b c d")  # wer=0, included
        calc.calculate("a b", "x y")  # wer=1.0, excluded
        assert calc.ser.cor == 1
        assert calc.ser.err == 0

    def test_ignore_punctuation(self):
        calc = Calculator(ignore_punctuation=True)
        result = calc.calculate("hello, world!", "hello world")
        assert result.wer == 0.0
