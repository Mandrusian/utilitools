"""Unit tests for Nota."""

import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
NOTA_PATH = ROOT / "pymisctools" / "Nota" / "nota.py"
EXAMPLE_NOTA = ROOT / "pymisctools" / "Nota" / "example.nota"


def load_nota():
    spec = importlib.util.spec_from_file_location("nota_mod", NOTA_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestNota(unittest.TestCase):
    def setUp(self):
        self.nota = load_nota()
        self.nota.reset_plot()

    def test_parse_nota_and_crlf(self):
        src = "# Title\r\n\r\n```python\r\nx = 2 + 3\r\nx\r\n```\r\n\r\n```plot\r\nplot([1,2], [3,4])\r\n```\r\n"
        blocks = self.nota.parse_nota(src)
        self.assertEqual([b[0] for b in blocks], ["prose", "python", "plot"])

    def test_exec_cell_shared_namespace(self):
        ns = self.nota.make_namespace()
        self.assertIsNone(self.nota.exec_cell("a = 6\nb = 7", ns))
        self.assertEqual(self.nota.exec_cell("a * b", ns), 42)

    def test_ascii_and_svg_plot_xml_escaping(self):
        self.nota.plot([0, 1, 2], [0, 1, 4], label="a & b < c")
        self.nota.set_title('x^2 & "test"')
        self.nota.xlabel("x < 3")
        self.nota.ylabel("y > 0")
        lines = self.nota.render_ascii_plot(width=40, height=10)
        self.assertIsNotNone(lines)
        with tempfile.TemporaryDirectory() as tmp:
            svg_path = os.path.join(tmp, "out.svg")
            self.nota.render_svg_plot(svg_path)
            ET.parse(svg_path)

    def test_cli_check_and_quiet(self):
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ, "HOME": home}
            cp_check = subprocess.run(
                [sys.executable, str(NOTA_PATH), str(EXAMPLE_NOTA), "--check", "--no-color"],
                capture_output=True, text=True, env=env, timeout=10,
            )
            self.assertEqual(cp_check.returncode, 0, cp_check.stderr)
            self.assertIn("blocks:", cp_check.stdout)
            self.assertNotIn("\x1b[", cp_check.stdout)

            cp_run = subprocess.run(
                [sys.executable, str(NOTA_PATH), str(EXAMPLE_NOTA), "--quiet", "--no-anim", "--no-color"],
                capture_output=True, text=True, env=env, timeout=10,
            )
            self.assertEqual(cp_run.returncode, 0, cp_run.stderr)
            self.assertIn("25", cp_run.stdout)
            self.assertIn("sine and cosine", cp_run.stdout)
            self.assertNotIn("\x1b[", cp_run.stdout)


if __name__ == "__main__":
    unittest.main()
