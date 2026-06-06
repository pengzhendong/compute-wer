import os
import tempfile

from click.testing import CliRunner

from compute_wer.cli import main


class TestCLI:
    def setup_method(self):
        self.runner = CliRunner()

    def _write_scp(self, lines):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".scp", delete=False, encoding="utf-8")
        for line in lines:
            f.write(line + "\n")
        f.close()
        return f.name

    def test_file_input(self):
        ref_file = self._write_scp(["utt1 hello world", "utt2 foo bar"])
        hyp_file = self._write_scp(["utt1 hello world", "utt2 foo baz"])
        out_file = tempfile.mktemp(suffix=".txt")
        try:
            result = self.runner.invoke(main, [ref_file, hyp_file, out_file])
            assert result.exit_code == 0
            with open(out_file) as f:
                content = f.read()
            assert "Overall" in content
            assert "SER" in content
        finally:
            os.unlink(ref_file)
            os.unlink(hyp_file)
            if os.path.exists(out_file):
                os.unlink(out_file)

    def test_file_output(self):
        ref_file = self._write_scp(["utt1 hello world"])
        hyp_file = self._write_scp(["utt1 hello world"])
        out_file = tempfile.mktemp(suffix=".txt")
        try:
            result = self.runner.invoke(main, [ref_file, hyp_file, out_file])
            assert result.exit_code == 0
            assert os.path.exists(out_file)
            with open(out_file) as f:
                content = f.read()
            assert "0.00 %" in content
        finally:
            os.unlink(ref_file)
            os.unlink(hyp_file)
            if os.path.exists(out_file):
                os.unlink(out_file)

    def test_char_mode(self):
        ref_file = self._write_scp(["utt1 abc"])
        hyp_file = self._write_scp(["utt1 axc"])
        out_file = tempfile.mktemp(suffix=".txt")
        try:
            result = self.runner.invoke(main, ["--char", ref_file, hyp_file, out_file])
            assert result.exit_code == 0
            with open(out_file) as f:
                content = f.read()
            assert "N=3" in content
        finally:
            os.unlink(ref_file)
            os.unlink(hyp_file)
            if os.path.exists(out_file):
                os.unlink(out_file)

    def test_case_sensitive(self):
        ref_file = self._write_scp(["utt1 Hello"])
        hyp_file = self._write_scp(["utt1 hello"])
        out_file = tempfile.mktemp(suffix=".txt")
        try:
            result = self.runner.invoke(main, ["--case-sensitive", ref_file, hyp_file, out_file])
            assert result.exit_code == 0
            with open(out_file) as f:
                content = f.read()
            assert "100.00 %" in content
        finally:
            os.unlink(ref_file)
            os.unlink(hyp_file)
            if os.path.exists(out_file):
                os.unlink(out_file)

    def test_sort_by_wer(self):
        ref_file = self._write_scp(["utt1 a b c", "utt2 x"])
        hyp_file = self._write_scp(["utt1 a b d", "utt2 y"])
        out_file = tempfile.mktemp(suffix=".txt")
        try:
            result = self.runner.invoke(main, ["--sort", "wer", ref_file, hyp_file, out_file])
            assert result.exit_code == 0
            with open(out_file) as f:
                content = f.read()
            utt1_pos = content.find("utt1")
            utt2_pos = content.find("utt2")
            assert utt1_pos < utt2_pos  # utt1 has lower WER
        finally:
            os.unlink(ref_file)
            os.unlink(hyp_file)
            if os.path.exists(out_file):
                os.unlink(out_file)

    def test_missing_hypothesis(self):
        ref_file = self._write_scp(["utt1 hello", "utt2 world"])
        hyp_file = self._write_scp(["utt1 hello"])
        out_file = tempfile.mktemp(suffix=".txt")
        try:
            result = self.runner.invoke(main, [ref_file, hyp_file, out_file])
            assert result.exit_code == 0
            with open(out_file) as f:
                content = f.read()
            assert "MH=" in content
        finally:
            os.unlink(ref_file)
            os.unlink(hyp_file)
            if os.path.exists(out_file):
                os.unlink(out_file)

    def test_ignore_punctuation(self):
        ref_file = self._write_scp(["utt1 hello, world!"])
        hyp_file = self._write_scp(["utt1 hello world"])
        out_file = tempfile.mktemp(suffix=".txt")
        try:
            result = self.runner.invoke(main, ["--ignore-punctuation", ref_file, hyp_file, out_file])
            assert result.exit_code == 0
            with open(out_file) as f:
                content = f.read()
            assert "0.00 %" in content
        finally:
            os.unlink(ref_file)
            os.unlink(hyp_file)
            if os.path.exists(out_file):
                os.unlink(out_file)
