import subprocess
import sys
import unittest


class EvezCliSurfaceTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "tools/evez.py", *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_help_lists_canonical_subcommands(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("{lint,play,visualize-thought,verify}", result.stdout)

    def test_legacy_documented_command_not_available(self):
        result = self.run_cli("cycle", "--help")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)


if __name__ == "__main__":
    unittest.main()
