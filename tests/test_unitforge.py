"""Unit tests for UnitForge."""

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
UNITFORGE_PATH = ROOT / "pymisctools" / "UnitForge" / "unitforge.py"


def load_unitforge():
    spec = importlib.util.spec_from_file_location("unitforge_mod", UNITFORGE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestUnitForge(unittest.TestCase):
    def setUp(self):
        self.uf = load_unitforge()
        self.uf.STATE["rainbow"] = "off"
        self.uf.STATE["animations"] = False
        self.uf.STATE["last_ans"] = None

    def test_basic_force_expression(self):
        q = self.uf.eval_quantity("5 kg * 9.8 m/s^2")
        self.assertAlmostEqual(q.value, 49.0)
        self.assertEqual(q.dims, {"M": 1, "L": 1, "T": -2})
        self.assertEqual(self.uf.find_named_unit(q.dims), "N")

    def test_implicit_mul_binds_tighter_than_division(self):
        speed = self.uf.eval_quantity("10 m / 2 s")
        self.assertAlmostEqual(speed.value, 5.0)
        self.assertEqual(speed.dims, {"L": 1, "T": -1})

        accel = self.uf.eval_quantity("60 km/h / 4 s")
        self.assertAlmostEqual(accel.value, 60000.0 / 3600.0 / 4.0)
        self.assertEqual(accel.dims, {"L": 1, "T": -2})

    def test_in_keyword_unit(self):
        val, target, _ = self.uf.do_conversion("10 in", "cm")
        self.assertAlmostEqual(val, 25.4)
        self.assertEqual(target, "cm")

        left, right = self.uf.split_conversion("5 in in cm")
        self.assertEqual((left, right), ("5 in", "cm"))

    def test_unit_aliases(self):
        val, _, _ = self.uf.do_conversion("5 miles", "kilometers")
        self.assertAlmostEqual(val, 8.04672)

    def test_temperature_conversions(self):
        c, du, su = self.uf.do_conversion("100 F", "C")
        self.assertEqual((su, du), ("F", "C"))
        self.assertAlmostEqual(c, 37.777777777, places=6)

        f, du2, su2 = self.uf.do_conversion("100 celsius", "fahrenheit")
        self.assertEqual((su2, du2), ("C", "F"))
        self.assertAlmostEqual(f, 212.0)

        k, _, _ = self.uf.do_conversion("0 °C", "K")
        self.assertAlmostEqual(k, 273.15)

    def test_dimension_mismatch_raises(self):
        with self.assertRaises(ValueError):
            self.uf.do_conversion("5 kg", "m")
        with self.assertRaises(ValueError):
            self.uf.eval_quantity("5 kg + 2 m")

    def test_ans_preserves_dimensions(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.uf.process_input("5 km")
            self.uf.process_input("ans to mi")
        out = buf.getvalue()
        self.assertIn("3.10686 mi", out)

    def test_cli_oneshot_no_color(self):
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ, "HOME": home}
            cp = subprocess.run(
                [sys.executable, str(UNITFORGE_PATH), "--no-anim", "--no-color", "100 F to C"],
                capture_output=True, text=True, env=env, timeout=10,
            )
            self.assertEqual(cp.returncode, 0, cp.stderr)
            self.assertIn("37.7778 C", cp.stdout)
            self.assertNotIn("\x1b[", cp.stdout)


if __name__ == "__main__":
    unittest.main()
