"""Unit tests for pyinit and root installers."""

import importlib.util
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PYINIT_PATH = ROOT / "pymisctools" / "pyinit" / "pyinit.py"


def load_pyinit():
    spec = importlib.util.spec_from_file_location("pyinit_mod", PYINIT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestPyInit(unittest.TestCase):
    def test_find_root_and_discover(self):
        pi = load_pyinit()
        root = pi.find_root()
        self.assertEqual(pathlib.Path(root).resolve(), (ROOT / "pymisctools").resolve())
        tools = pi.discover(root)
        names = [t["name"] for t in tools]
        self.assertEqual(names, ["GitViz", "Nota", "PolyglotBench", "PYCalc", "UnitForge"])
        for t in tools:
            self.assertTrue(t["desc"], f"missing description for {t['name']}")
            self.assertTrue(pathlib.Path(t["entry"]).exists())

    def test_cli_list_and_help(self):
        cp_help = subprocess.run(
            [sys.executable, str(PYINIT_PATH), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(cp_help.returncode, 0, cp_help.stderr)
        self.assertIn("usage: pyinit", cp_help.stdout)

        cp_list = subprocess.run(
            [sys.executable, str(PYINIT_PATH), "--list"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(cp_list.returncode, 0, cp_list.stderr)
        for name in ("GitViz", "Nota", "PolyglotBench", "PYCalc", "UnitForge"):
            self.assertIn(name, cp_list.stdout)

    def test_installers_reference_pymisctools_pyinit(self):
        bat = (ROOT / "install.bat").read_text()
        sh = (ROOT / "pymisctools" / "install.sh").read_text()
        self.assertIn(r"pymisctools\pyinit\install_pyinit.py", bat)
        self.assertIn("pymisctools/pyinit/install_pyinit.py", sh)


if __name__ == "__main__":
    unittest.main()
