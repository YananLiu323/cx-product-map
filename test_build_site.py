"""Acceptance checks: CSV is authoritative; Markdown edits reach the page; bad input fails."""
from pathlib import Path
import csv
import tempfile
import unittest
import shutil
import re
from urllib.parse import urlsplit

from build_site import build


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = Path(__file__).resolve().parent
        for name in ("产品全貌.md", "功能目录.csv", "site_template.html"):
            shutil.copyfile(source / name, self.root / name)
        for svg in source.rglob("*.svg"):
            relative = svg.relative_to(source)
            if "_site" in relative.parts:
                continue
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(svg, target)
        with (self.root / "功能目录.csv").open(encoding="utf-8-sig", newline="") as stream:
            self.feature_count = len(list(csv.DictReader(stream)))
        references = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", (self.root / "产品全貌.md").read_text())
        self.diagram_count = len({name for name in references if name.endswith(".svg") and not urlsplit(name).scheme})

    def rewrite_catalog(self, mutate):
        path = self.root / "功能目录.csv"
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        mutate(rows)
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    def test_csv_change_and_new_feature_replace_stale_markdown_table(self):
        def mutate(rows):
            rows[0]["功能"] = "CSV 更新验收：新名称"
            next_id = max((int(row["编号"][1:]) for row in rows if row["编号"].startswith("C")), default=0) + 1
            added = dict(rows[0], 编号=f"C{next_id:02}", 功能="CSV 新增功能验收")
            rows.append(added)
        self.rewrite_catalog(mutate)
        source_before = (self.root / "产品全貌.md").read_bytes()
        info = build(self.root, self.root / "_site")
        page = (self.root / "_site/index.html").read_text()
        self.assertIn("CSV 更新验收：新名称", page)
        self.assertIn("CSV 新增功能验收", page)
        self.assertEqual(info["features"], self.feature_count + 1)
        self.assertEqual(info["diagrams"], self.diagram_count)
        self.assertEqual((self.root / "产品全貌.md").read_bytes(), source_before)

    def test_markdown_only_change_reaches_page(self):
        path = self.root / "产品全貌.md"
        path.write_text(path.read_text() + "\n\n## 更新验收\n\n只改 Markdown 也会更新网页。\n")
        build(self.root, self.root / "_site")
        self.assertIn("只改 Markdown 也会更新网页。", (self.root / "_site/index.html").read_text())

    def test_duplicate_id_fails_without_replacing_existing_page(self):
        build(self.root, self.root / "_site")
        old = (self.root / "_site/index.html").read_bytes()
        self.rewrite_catalog(lambda rows: rows.append(dict(rows[0])))
        with self.assertRaisesRegex(ValueError, "重复功能编号"):
            build(self.root, self.root / "_site")
        self.assertEqual((self.root / "_site/index.html").read_bytes(), old)


if __name__ == "__main__":
    unittest.main()
