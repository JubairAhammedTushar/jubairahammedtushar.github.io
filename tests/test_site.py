from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "index.html").read_text(encoding="utf-8")
VOID = {"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}

class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.ids = []
        self.anchors = []
        self.projects = []
        self.headings = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a" and attrs.get("href", "").startswith("#"):
            self.anchors.append(attrs["href"][1:])
        if tag == "article" and "card" in attrs.get("class","").split():
            self.projects.append(attrs.get("data-stage"))
        if tag in {"h1","h2","h3","h4","h5","h6"}:
            self.headings.append(tag)
        if tag not in VOID:
            self.stack.append(tag)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)
    def handle_endtag(self, tag):
        if not self.stack:
            self.errors.append(f"Unexpected closing tag: {tag}")
        elif self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append(f"Expected </{self.stack[-1]}> but saw </{tag}>")
            if tag in self.stack:
                while self.stack and self.stack[-1] != tag:
                    self.stack.pop()
                if self.stack:
                    self.stack.pop()

class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = Document()
        cls.doc.feed(SOURCE)
        cls.doc.close()

    def test_valid_structure(self):
        self.assertFalse(self.doc.errors, "\n".join(self.doc.errors))
        self.assertFalse(self.doc.stack, str(self.doc.stack))
        self.assertTrue(SOURCE.lower().lstrip().startswith("<!doctype html>"))

    def test_unique_ids_and_internal_links(self):
        self.assertEqual(len(self.doc.ids), len(set(self.doc.ids)))
        for href_id in self.doc.anchors:
            self.assertIn(href_id, self.doc.ids, f"Missing destination #{href_id}")

    def test_projects_are_honestly_classified(self):
        self.assertEqual(len(self.doc.projects), 15)
        self.assertEqual(self.doc.projects.count("built"), 6)
        self.assertEqual(self.doc.projects.count("candidate"), 1)
        self.assertEqual(self.doc.projects.count("practice"), 8)
        self.assertIn('data-filter="all">All entries <span>15</span>', SOURCE)
        self.assertIn("Showing 15 entries", SOURCE)
        numbers = re.findall(r'PROJECT / (\d\d)', SOURCE)
        self.assertEqual(numbers, [f"{n:02d}" for n in range(1, 16)])

    def test_running_lab_states_its_limits(self):
        self.assertIn("JAT Cipherline 2300", SOURCE)
        self.assertIn("no independent audit or penetration test", SOURCE)
        self.assertIn("AI coding assistant", SOURCE)
        self.assertNotIn("The user previously reported", SOURCE)

    def test_experience_is_current(self):
        self.assertIn('id="experience"', SOURCE)
        self.assertIn("Trainee Manager", SOURCE)
        self.assertEqual(SOURCE.count('class="job"'), 4)

    def test_accessibility_and_mobile_basics(self):
        self.assertEqual(self.doc.headings.count("h1"), 1)
        self.assertIn('class="skip"', SOURCE)
        self.assertIn('aria-live="polite"', SOURCE)
        self.assertIn("prefers-reduced-motion:reduce", SOURCE)
        self.assertIn('name="viewport"', SOURCE)
        self.assertIn('aria-label="Main navigation"', SOURCE)

    def test_public_metadata(self):
        self.assertIn('rel="canonical"', SOURCE)
        self.assertIn('property="og:title"', SOURCE)
        self.assertIn('name="description"', SOURCE)
        self.assertIn("JACG-2300", SOURCE)

    def test_analytics_opt_in_without_fake_tracking(self):
        loader = (ROOT / "analytics.js").read_text(encoding="utf-8")
        self.assertIn('src="analytics.js"', SOURCE)
        self.assertIn('const CLOUDFLARE_SITE_TOKEN = "26318f2ca4074a669e923e404958f836";', loader)
        self.assertIn("static.cloudflareinsights.com/beacon.min.js", loader)
        self.assertIn('data-cf-beacon', loader)
        self.assertIn("if (!/^[a-f0-9]{32}$/i.test(token)) return;", loader)
        self.assertNotIn("googletagmanager.com", SOURCE)

    def test_no_known_sensitive_material(self):
        for needle in ("-----BEGIN PRIVATE KEY-----", "-----BEGIN OPENSSH PRIVATE KEY-----",
                       "REALITY_PRIVATE=", "wg-server.key", "192.168.0.18", "10.5.5.1",
                       "192.168.0.", "100.64.", "ts.net", "console.jubairahammedtushar", "vault.jubairahammedtushar"):
            self.assertNotIn(needle, SOURCE)
        self.assertNotRegex(SOURCE, r"(?i)(password|private[_-]?key)\s*[:=]\s*['\"][^'\"]{8,}")

if __name__ == "__main__":
    unittest.main()
