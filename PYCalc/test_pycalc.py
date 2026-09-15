#!/usr/bin/env python3
"""Minimal unit tests for PYCalc. Run: python3 test_pycalc.py"""
import importlib.util, unittest

spec = importlib.util.spec_from_file_location("pc", "PYCalc.py")
pc = importlib.util.module_from_spec(spec); spec.loader.exec_module(pc)


class TestNormalize(unittest.TestCase):
    def test_pi(self):         self.assertEqual(pc.normalize("π"), "pi")
    def test_sqrt_paren(self): self.assertEqual(pc.normalize("√(x+1)"), "sqrt(x+1)")
    def test_sqrt_num(self):   self.assertEqual(pc.normalize("√16"), "sqrt(16)")
    def test_sqrt_var(self):   self.assertEqual(pc.normalize("√x"), "sqrt(x)")
    def test_2_sqrt(self):     self.assertEqual(pc.normalize("2√3"), "2sqrt(3)")
    def test_degree(self):     self.assertEqual(pc.normalize("30°"), "radians(30)")
    def test_percent_of(self): self.assertEqual(pc.normalize("20% of 80"), "(20/100)*(80)")
    def test_power(self):      self.assertEqual(pc.normalize("2^10"), "2**10")


class TestEval(unittest.TestCase):
    def setUp(self):    pc.STATE["advanced"] = True
    def tearDown(self): pc.STATE["advanced"] = False

    def test_basic(self):      self.assertEqual(pc.safe_eval("2+3", {}), 5.0)
    def test_power(self):      self.assertEqual(pc.safe_eval("2^10", {}), 1024.0)
    def test_sqrt_u(self):     self.assertEqual(pc.safe_eval("√16", {}), 4.0)
    def test_sin_deg(self):    self.assertAlmostEqual(pc.safe_eval("sin(30°)", {}), 0.5)
    def test_pct(self):        self.assertEqual(pc.safe_eval("20% of 80", {}), 16.0)
    def test_pct_plus(self):   self.assertEqual(pc.safe_eval("20% of 80 + 5", {}), 21.0)
    def test_modulo(self):     self.assertEqual(pc.safe_eval("20 % 5", {}), 0.0)
    def test_complex(self):    self.assertEqual(pc.safe_eval("sqrt(-1)", {}), 1j)
    def test_implicit(self):   self.assertEqual(pc.safe_eval("2(3+4)", {}), 14.0)
    def test_explicit(self):   self.assertEqual(pc.safe_eval("2*(3+4)", {}), 14.0)
    def test_round_2arg(self): self.assertEqual(pc.safe_eval("round(2.5, 1)", {}), 2.5)


class TestUnits(unittest.TestCase):
    def test_km_mi(self):   self.assertAlmostEqual(pc.convert_units(5, "km", "mi"), 3.1068559611867, places=6)
    def test_f_c(self):     self.assertAlmostEqual(pc.convert_units(100, "F", "C"), 37.777777777, places=6)
    def test_kg_lb(self):   self.assertAlmostEqual(pc.convert_units(2.5, "kg", "lb"), 5.511556, places=5)
    def test_aliases(self): self.assertEqual(pc.convert_units(1, "kilometre", "metres"), 1000.0)


class TestFormat(unittest.TestCase):
    def setUp(self):    pc.STATE["fractions"] = False
    def tearDown(self): pc.STATE["fractions"] = False

    def test_int(self):  self.assertEqual(pc.format_number(2.0), "2")
    def test_half(self): self.assertEqual(pc.format_number(0.5), "0.5")
    def test_tiny(self): self.assertEqual(pc.format_number(1e-20), "0")
    def test_inf(self):  self.assertEqual(pc.format_number(float("inf")), "inf")
    def test_fraction(self):
        pc.STATE["fractions"] = True
        self.assertIn("1/3", pc.format_number(1/3))


if __name__ == "__main__":
    unittest.main(verbosity=2)
