"""Unit tests for GitViz."""

import importlib.util
import io
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout

ROOT = pathlib.Path(__file__).resolve().parent.parent
GITVIZ_PATH = ROOT / "pymisctools" / "GitViz" / "gitviz.py"


def load_gitviz():
    spec = importlib.util.spec_from_file_location("gitviz_mod", GITVIZ_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestGitViz(unittest.TestCase):
    def setUp(self):
        self.gv = load_gitviz()
        self.gv._strip_color()

    def test_assign_lanes_branch_and_merge(self):
        commits = [
            {"hash": "c3", "parents": ["c2", "b1"], "author": "a", "when": "now", "refs": "HEAD -> main", "subject": "merge & <tag>"},
            {"hash": "b1", "parents": ["c1"], "author": "a", "when": "1m", "refs": "feat", "subject": "branch commit"},
            {"hash": "c2", "parents": ["c1"], "author": "a", "when": "2m", "refs": "", "subject": "main commit"},
            {"hash": "c1", "parents": [], "author": "a", "when": "3m", "refs": "", "subject": "init"},
        ]
        rows = self.gv.assign_lanes(commits)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["lane"], 0)
        self.assertNotEqual(rows[1]["lane"], rows[2]["lane"])

        buf = io.StringIO()
        with redirect_stdout(buf):
            self.gv.render_ascii(commits)
        out = buf.getvalue()
        self.assertIn("merge & <tag>", out)
        self.assertIn("4 commit(s)", out)

        with tempfile.TemporaryDirectory() as tmp:
            svg_path = os.path.join(tmp, "graph.svg")
            self.gv.render_svg(commits, svg_path, title='repo <"x"> & y')
            ET.parse(svg_path)

    def test_cli_on_temp_git_repo_no_color(self):
        with tempfile.TemporaryDirectory() as repo:
            subprocess.run(["git", "init", repo], check=True, capture_output=True)
            subprocess.run(["git", "-C", repo, "config", "user.name", "Test"], check=True)
            subprocess.run(["git", "-C", repo, "config", "user.email", "test@example.com"], check=True)
            pathlib.Path(repo, "a.txt").write_text("hi\n")
            subprocess.run(["git", "-C", repo, "add", "a.txt"], check=True)
            subprocess.run(["git", "-C", repo, "commit", "-m", "initial commit"], check=True, capture_output=True)

            cp = subprocess.run(
                [sys.executable, str(GITVIZ_PATH), repo, "--no-color", "--limit", "5"],
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(cp.returncode, 0, cp.stderr)
            self.assertIn("initial commit", cp.stdout)
            self.assertNotIn("\x1b[", cp.stdout)


if __name__ == "__main__":
    unittest.main()
