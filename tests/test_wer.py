import pytest

from compute_wer.wer import SER, WER


class TestWER:
    def test_identical(self):
        w = WER(["hello", "world"], ["hello", "world"])
        assert w.wer == 0.0
        assert w.equal == 2
        assert w.replace == 0
        assert w.delete == 0
        assert w.insert == 0

    def test_all_substitutions(self):
        w = WER(["a", "b", "c"], ["x", "y", "z"])
        assert w.replace == 3
        assert w.equal == 0
        assert w.wer == 1.0

    def test_all_deletions(self):
        w = WER(["a", "b", "c"], [])
        assert w.delete == 3
        assert w.wer == 1.0

    def test_all_insertions(self):
        w = WER([], ["a", "b", "c"])
        assert w.insert == 3
        assert w.wer == 0  # all == 0, so wer returns 0

    def test_mixed_operations(self):
        # ref: "the cat sat on the mat"
        # hyp: "the dog sat a mat"
        ref = ["the", "cat", "sat", "on", "the", "mat"]
        hyp = ["the", "dog", "sat", "a", "mat"]
        w = WER(ref, hyp)
        assert w.equal == 3  # the, sat, mat
        assert w.replace == 2  # cat->dog, on->a
        assert w.delete == 1  # the (second)
        assert w.insert == 0
        assert w.all == 6
        assert w.wer == pytest.approx(3 / 6)

    def test_empty_both(self):
        w = WER([], [])
        assert w.wer == 0
        assert w.all == 0

    def test_single_insertion(self):
        w = WER(["a", "b"], ["a", "x", "b"])
        assert w.insert == 1
        assert w.equal == 2
        assert w.wer == pytest.approx(1 / 2)

    def test_single_deletion(self):
        w = WER(["a", "x", "b"], ["a", "b"])
        assert w.delete == 1
        assert w.equal == 2
        assert w.wer == pytest.approx(1 / 3)

    def test_str_format(self):
        w = WER(["a", "b", "c", "d"], ["a", "b", "c", "d"])
        s = str(w)
        assert "0.00 %" in s
        assert "N=4" in s

    def test_update(self):
        w1 = WER()
        w1.equal = 5
        w1.replace = 1
        w1.delete = 1
        w1.insert = 0

        w2 = WER()
        w2.equal = 3
        w2.replace = 2
        w2.delete = 0
        w2.insert = 1

        w1.update(w2)
        assert w1.equal == 8
        assert w1.replace == 3
        assert w1.delete == 1
        assert w1.insert == 1

    def test_overall(self):
        w1 = WER()
        w1.equal = 10
        w1.replace = 2
        w1.delete = 1
        w1.insert = 1

        w2 = WER()
        w2.equal = 5
        w2.replace = 1
        w2.delete = 0
        w2.insert = 2

        overall = WER.overall([w1, w2])
        assert overall.equal == 15
        assert overall.replace == 3
        assert overall.delete == 1
        assert overall.insert == 3

    def test_overall_with_none(self):
        w1 = WER()
        w1.equal = 4
        w1.replace = 1
        overall = WER.overall([w1, None, None])
        assert overall.equal == 4
        assert overall.replace == 1

    def test_tokens_tracking(self):
        w = WER(["hello", "world"], ["hello", "earth"])
        assert "hello" in w.tokens
        assert "world" in w.tokens
        assert w.tokens["hello"].equal == 1
        assert w.tokens["world"].replace == 1

    def test_width_ascii(self):
        assert WER.width("hello") == 5

    def test_width_cjk(self):
        assert WER.width("你好") == 4  # each CJK char is width 2


class TestSER:
    def test_initial(self):
        ser = SER()
        assert ser.all == 0
        assert ser.ser == 0

    def test_all_correct(self):
        ser = SER()
        ser.cor = 10
        ser.err = 0
        assert ser.ser == 0.0

    def test_all_errors(self):
        ser = SER()
        ser.cor = 0
        ser.err = 5
        assert ser.ser == 1.0

    def test_mixed(self):
        ser = SER()
        ser.cor = 7
        ser.err = 3
        assert ser.ser == pytest.approx(0.3)

    def test_str_format(self):
        ser = SER()
        ser.cor = 8
        ser.err = 2
        s = str(ser)
        assert "20.00 %" in s
        assert "N=10" in s
