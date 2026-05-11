import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


class ReplayLabTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [PYTHON, str(ROOT / "replay_lab.py"), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_validate_fixture(self):
        result = self.run_cli("validate", "fixtures/fake_customer_refund.json")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("pass", result.stdout)

    def test_good_sample_needs_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli("run", "fixtures/fake_customer_refund.json", "--label", "test", "--out", tmp, "--report-out", tmp)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("status: needs_review", result.stdout)
            files = list(Path(tmp).glob("*.json"))
            self.assertTrue(files)
            data = json.loads(files[0].read_text())
            self.assertEqual(data["status"], "needs_review")

    def test_bad_sample_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(
                "run",
                "fixtures/fake_customer_refund.json",
                "--actual",
                "outputs/sample_after/fake_customer_refund.txt",
                "--label",
                "testbad",
                "--out",
                tmp,
                "--report-out",
                tmp,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("status: fail", result.stdout)

    def test_command_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(
                "run",
                "fixtures/fake_customer_refund.json",
                "--command",
                f"{PYTHON} examples/mock_agent.py fixtures/fake_customer_refund.json good",
                "--label",
                "cmd",
                "--out",
                tmp,
                "--report-out",
                tmp,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("status: needs_review", result.stdout)

    def test_doctor(self):
        result = self.run_cli("doctor")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("pass: repo doctor checks completed", result.stdout)

    def test_validate_all(self):
        result = self.run_cli("validate-all")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("summary: 5 fixture files passed", result.stdout)

    def test_compare_fail_on_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            before = self.run_cli("run", "fixtures/fake_customer_refund.json", "--label", "before", "--out", tmp, "--report-out", tmp)
            self.assertEqual(before.returncode, 0, before.stderr + before.stdout)
            after = self.run_cli(
                "run",
                "fixtures/fake_customer_refund.json",
                "--actual",
                "outputs/sample_after/fake_customer_refund.txt",
                "--label",
                "after",
                "--out",
                tmp,
                "--report-out",
                tmp,
            )
            self.assertEqual(after.returncode, 0, after.stderr + after.stdout)
            files = sorted(Path(tmp).glob("*.json"))
            self.assertGreaterEqual(len(files), 2)
            result = self.run_cli("compare", str(files[0]), str(files[1]), "--out", tmp, "--fail-on-change")
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            self.assertIn("comparison status: changed", result.stdout)

    def test_scan_sessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli("scan-sessions", "examples", "--out", str(Path(tmp) / "scan.json"))
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("scanned 1 jsonl files", result.stdout)


if __name__ == "__main__":
    unittest.main()
