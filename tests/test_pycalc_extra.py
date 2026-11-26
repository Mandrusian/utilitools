"""Additional tests for PYCalc (CLI, base conversions, SVG escaping, sessions)."""

import importlib.util
import io
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

ROOT = pathlib.Path(__file__).resolve().parent.parent
PYCALC_PATH = ROOT / "pymisctools" / "PYCalc" / "PYCalc.py"


def load_pycalc():
    spec = importlib.util.spec_from_file_location("pycalc_mod", PYCALC_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestPYCalcExtra(unittest.TestCase):
    def setUp(self):
        self.pc = load_pycalc()
        self.pc.STATE["rainbow"] = "off"
        self.pc.STATE["animations"] = False

    def test_hex_to_dec_conversion(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.pc.process_input("0xff to dec")
        self.assertIn("255", buf.getvalue())

    def test_bin_to_hex_conversion(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.pc.process_input("0b1010 to hex")
        self.assertIn("0xa", buf.getvalue())

    def test_unit_scientific_notation_conversion(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.pc.process_input("1e3 m to km")
        self.assertIn("1 km", buf.getvalue())

    def test_svg_escapes_xml(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "plot.svg")
            # x + 0 & check XML remains valid (parseable by ElementTree)
            import xml.etree.ElementTree as ET
            self.pc.generate_svg(["x"], -2, 2, None, None, out)
            ET.parse(out)
            # Directly verify _esc_xml handles special characters
            self.assertEqual(self.pc._esc_xml('a & b < c > "d"'), 'a &amp; b &lt; c &gt; &quot;d&quot;')

    def test_session_preserves_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.pc.SESSION_DIR = tmp
            self.pc.STATE["var_cache"] = {"x": 42}
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.pc.process_input("save MyLab")
            self.assertTrue(os.path.exists(os.path.join(tmp, "MyLab.json")))
            self.pc.STATE["var_cache"] = {}
            with redirect_stdout(buf):
                self.pc.process_input("load MyLab")
            self.assertEqual(self.pc.STATE["var_cache"].get("x"), 42)

    def test_cli_eval_no_color(self):
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ, "HOME": home}
            cp = subprocess.run(
                [sys.executable, str(PYCALC_PATH), "--no-anim", "--no-color", "-e", "2^10 + 24"],
                capture_output=True, text=True, env=env, timeout=10,
            )
            self.assertEqual(cp.returncode, 0, cp.stderr)
            self.assertIn("1048", cp.stdout)
            self.assertNotIn("\x1b[", cp.stdout)


if __name__ == "__main__":
    unittest.main()
