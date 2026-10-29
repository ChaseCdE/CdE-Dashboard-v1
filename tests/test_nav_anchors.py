"""Every page and section anchor listed in the site navigation (layout.js NAV) must exist.

Reads NAV by importing layout.js with Node (skipped if Node is not installed).
"""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"


def load_nav():
    js = "import('./assets/js/layout.js').then((m) => console.log(JSON.stringify(m.NAV)))"
    out = subprocess.run(["node", "--input-type=module", "-e", js], cwd=SITE, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


@unittest.skipUnless(shutil.which("node"), "Node.js not installed")
class NavAnchorsTest(unittest.TestCase):
    def test_nav_anchors_exist(self):
        nav = load_nav()
        self.assertGreater(len(nav), 5)
        for page in nav:
            html = (SITE / page["path"]).read_text(encoding="utf-8")
            ids = set(re.findall(r'<h[23] id="([^"]+)"', html))
            for sec in page.get("sections", []):
                self.assertIn(sec["id"], ids, f"{page['path']}#{sec['id']}")
                for sub in sec.get("sub", []):
                    self.assertIn(sub["id"], ids, f"{page['path']}#{sub['id']}")

    def test_every_page_in_nav_or_redirect(self):
        paths = {p["path"] for p in load_nav()}
        for f in (SITE / "pages").glob("*.html"):
            html = f.read_text(encoding="utf-8")
            if 'http-equiv="refresh"' in html:  # old page kept as a redirect
                target = re.search(r"url=([^\"#]+)", html).group(1)
                self.assertIn(f"pages/{target}", paths, f.name)
            else:
                self.assertIn(f"pages/{f.name}", paths, f.name)


if __name__ == "__main__":
    unittest.main()
