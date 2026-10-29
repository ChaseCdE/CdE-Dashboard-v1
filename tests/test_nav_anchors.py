"""Every page and section anchor listed in the site navigation (layout.js NAV) must exist."""
import re
import unittest
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"


class NavAnchorsTest(unittest.TestCase):
    def test_nav_anchors_exist(self):
        js = (SITE / "assets/js/layout.js").read_text(encoding="utf-8")
        nav = js[js.index("export const NAV"):js.index("];", js.index("export const NAV"))]
        # Split into page entries: each "path: '...'" is followed by its sections up to the next path.
        parts = re.split(r"path: '([^']+)'", nav)
        self.assertGreater(len(parts), 3)
        for i in range(1, len(parts), 2):
            path, body = parts[i], parts[i + 1]
            html_file = SITE / path
            self.assertTrue(html_file.exists(), path)
            ids = set(re.findall(r'<h2 id="([^"]+)"', html_file.read_text(encoding="utf-8")))
            for anchor in re.findall(r"\['([a-z0-9-]+)', '", body):
                self.assertIn(anchor, ids, f"{path}#{anchor}")

    def test_every_page_in_nav(self):
        js = (SITE / "assets/js/layout.js").read_text(encoding="utf-8")
        for f in (SITE / "pages").glob("*.html"):
            self.assertIn(f"pages/{f.name}", js, f.name)


if __name__ == "__main__":
    unittest.main()
