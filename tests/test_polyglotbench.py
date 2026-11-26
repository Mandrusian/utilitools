"""Unit tests for PolyglotBench."""

import importlib.util
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PB_PATH = ROOT / "pymisctools" / "PolyglotBench" / "polyglotbench.py"


def load_pb():
    spec = importlib.util.spec_from_file_location("pb_mod", PB_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestPolyglotBench(unittest.TestCase):
    def test_discover_problems(self):
        pb = load_pb()
        problems = pb.discover_problems()
        names = [p[0] for p in problems]
        self.assertEqual(names, ["fib", "hello", "wordcount"])
        for _, spec, impls in problems:
            self.assertIn("cases", spec)
            self.assertIn("python", impls)

    def test_summarize(self):
        pb = load_pb()
        self.assertEqual(pb.summarize([{"status": "PASS"}]), "PASS")
        self.assertEqual(pb.summarize([{"status": "PASS"}, {"status": "WRONG"}]), "WRONG")
        self.assertEqual(pb.summarize([{"status": "COMPILE_FAIL"}, {"status": "WRONG"}]), "COMPILE_FAIL")

    def test_cli_list_and_python_run_no_color(self):
        cp_list = subprocess.run(
            [sys.executable, str(PB_PATH), "--list", "--no-anim", "--no-color"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(cp_list.returncode, 0, cp_list.stderr)
        self.assertIn("hello", cp_list.stdout)
        self.assertNotIn("\x1b[", cp_list.stdout)

        cp_py = subprocess.run(
            [sys.executable, str(PB_PATH), "--lang", "python", "--no-anim", "--no-color"],
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(cp_py.returncode, 0, cp_py.stderr)
        self.assertIn("3 pass   0 fail", cp_py.stdout)
        self.assertNotIn("\x1b[", cp_py.stdout)

    def test_cli_unknown_lang_fails(self):
        cp = subprocess.run(
            [sys.executable, str(PB_PATH), "--lang", "nonexistent", "--no-color"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(cp.returncode, 0)


if __name__ == "__main__":
    unittest.main()
