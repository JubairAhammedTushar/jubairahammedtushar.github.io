from html.parser import HTMLParser
import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
EVIDENCE = (ROOT / "evidence" / "cipherline-backup-review.md").read_text(encoding="utf-8")

SENSITIVE = {
    "private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "secret assignment": r"(?i)(password|passwd|secret|token|private[_-]?key)\s*[:=]\s*['\"][^'\"]{8,}",
    "private IPv4 address": r"\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b",
    "CGNAT / Tailscale address": r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b",
    "Tailscale hostname": r"\.ts\.net\b",
    "private subdomain": r"\b(?!www\.)[a-z0-9-]+\.(?:jubairahammedtushar\.com|jatushar\.co\.uk)\b",
    "UK phone number": r"(?:\+44\s?7\d{3}|\b07\d{3})\s?\d{3}\s?\d{3}\b",
    "key file name": r"\b[\w-]+\.key\b",
    "backup archive name": r"cipherline-\d{8}T\d{6}Z",
}
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
        self.assertEqual(len(self.doc.projects), 8)
        self.assertEqual(self.doc.projects.count("built"), 5)
        self.assertEqual(self.doc.projects.count("history"), 1)
        self.assertEqual(self.doc.projects.count("training"), 2)
        numbers = re.findall(r'PROJECT / (\d\d)', SOURCE)
        self.assertEqual(numbers, [f"{n:02d}" for n in range(1, 9)])
        self.assertEqual(SOURCE.count('<p class="domain">'), 8)   # every card names its security domain
        self.assertIn("<b>Next:</b>", SOURCE)
        self.assertNotIn("data-filter", SOURCE)

    def test_lab_map_and_code(self):
        self.assertIn('<figure class="lab-map">', SOURCE)
        self.assertIn('aria-labelledby="labmapTitle labmapDesc"', SOURCE)
        self.assertIn("tree/main/detections", SOURCE)
        for f in ("detections/README.md", "detections/wazuh/cipherline_rules.xml", "detections/wazuh/cipherline_decoders.xml",
                  "detections/router-mail/router-mail.py", "detections/router-mail/test-router-mail.py"):
            self.assertTrue((ROOT / f).is_file(), f)
        import xml.dom.minidom
        for f in ("cipherline_rules.xml", "cipherline_decoders.xml"):
            text = (ROOT / "detections" / "wazuh" / f).read_text(encoding="utf-8")
            xml.dom.minidom.parseString("<root>" + text + "</root>")   # Wazuh files have several top-level elements
        rules = (ROOT / "detections" / "wazuh" / "cipherline_rules.xml").read_text(encoding="utf-8")
        self.assertIn('<rule id="100259" level="11" noalert="1">', rules)

    def test_cv_is_linked_and_present(self):
        self.assertEqual(SOURCE.count('href="cv/Jubair-Ahammed-Tushar-CV.pdf" download'), 2)
        pdf = ROOT / "cv" / "Jubair-Ahammed-Tushar-CV.pdf"
        self.assertTrue(pdf.is_file())
        self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))

    # Which VPN protocols the gateway runs stays private, so even this test does not name them:
    # it compares word hashes (first 16 hex digits of SHA-256) instead.
    HIDDEN_ANY_CASE = {"3ee9e81db1bcf90e", "361e620353d33dc7", "d7522a87ef41c1e3",
                       "f12a0235f3707973", "50304fca6fc6b3bb", "1a46e6a68c37e8f9"}
    HIDDEN_EXACT = {"54a88dc2544d5c26"}   # an ordinary English word, so only its all-capitals form

    def test_vpn_protocols_stay_private(self):
        def h(word):
            return hashlib.sha256(word.encode()).hexdigest()[:16]
        for text in (SOURCE, README):
            for word in set(re.findall(r"[A-Za-z0-9]+", text)):
                self.assertNotIn(h(word.lower()), self.HIDDEN_ANY_CASE, word)
                self.assertNotIn(h(word), self.HIDDEN_EXACT, word)

    def test_running_lab_states_its_limits(self):
        self.assertIn("JAT Cipherline 2300", SOURCE)
        self.assertIn("no independent audit or penetration test", SOURCE)
        self.assertIn("AI coding assistant", SOURCE)
        self.assertNotIn("The user previously reported", SOURCE)
        self.assertIn("Some exercises are completed practical work", SOURCE)
        self.assertIn("My home lab in Bangladesh, managed from Cardiff.", SOURCE)
        self.assertNotIn("Wifite", SOURCE)
        self.assertNotIn("Fluxion", SOURCE)

    def test_experience_is_current(self):
        self.assertIn('id="experience"', SOURCE)
        self.assertIn("Team Member, currently in management training", SOURCE)
        self.assertEqual(SOURCE.count('class="job"'), 9)          # five jobs, four education and training entries
        for role in ("Shanila Pan Products", "Sharhan Bayezid", "Band Lalon", "Al Aria Perfume Gallery", "Popeyes"):
            self.assertIn(role, SOURCE)
        self.assertIn('id="education"', SOURCE)
        self.assertNotIn("final examinations in autumn 2026", SOURCE)
        self.assertNotIn("family business", SOURCE.lower())

    def test_accessibility_and_mobile_basics(self):
        self.assertEqual(self.doc.headings.count("h1"), 1)
        self.assertIn('class="skip"', SOURCE)
        self.assertIn('aria-live="polite"', SOURCE)
        self.assertIn("document.querySelectorAll('.mail')", SOURCE)
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

    def test_contact_lists_three_addresses(self):
        order = ["hello@jubairahammedtushar.com", "hello@jatushar.co.uk", "jubairahmedtushar@gmail.com"]   # chosen primary first
        self.assertEqual(re.findall(r'href="mailto:([^"]+)"', SOURCE), order)
        self.assertEqual(re.findall(r'data-mail="([^"]+)"', SOURCE), order)
        # A failed copy must not claim success: it selects the address and says so.
        self.assertIn("selected — copy manually", SOURCE)
        self.assertNotIn("then(done).catch(sel)", SOURCE)

    def test_backup_evidence_is_private_and_scope_is_clear(self):
        self.assertIn("Private gateway-backup evidence (21 November 2026)", SOURCE)
        self.assertIn("no isolated restore has been performed", SOURCE)
        self.assertIn("evidence/cipherline-backup-review.md", SOURCE)
        for phrase in ("1,043 entries", "991 regular files", "PRAGMA integrity_check", "Nextcloud user files",
                       "Proxmox virtual-machine disk images", "recoverability is **not established**"):
            self.assertIn(phrase, EVIDENCE)
        for ext in ("*.tar", "*.tar.gz", "*.tgz", "*.zip", "*.sqlite*", "*.db", "*.conf", "*.key"):
            self.assertFalse(list((ROOT / "evidence").glob(ext)), ext)

    def test_no_known_sensitive_material(self):
        for text, name in ((SOURCE, "index.html"), (README, "README.md"), (EVIDENCE, "evidence note")):
            for label, pattern in SENSITIVE.items():
                self.assertNotRegex(text, pattern, f"{label} in {name}")

if __name__ == "__main__":
    unittest.main()
