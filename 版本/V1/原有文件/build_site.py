"""Build the public documentation from Markdown + CSV, without the CX source snapshot."""
from pathlib import Path
import csv
import hashlib
import html
import json
import os
import re
import shutil
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

import markdown

MODULES = dict(enumerate("CPXTABSOG", 1))
COLUMNS = ["模块", "编号", "功能", "页面或呈现位置", "模块关系", "代码证据与范围", "关联流程", "Figma设计链接", "Prototype播放链接", "验证状态", "覆盖与缺口", "核对日期", "Figma版本记录"]
HEADERS = ["编号", "功能与页面位置", "模块关系", "代码依据与范围", "关联流程", "Figma 可编辑界面", "Prototype 播放", "验证状态与覆盖", "核对与版本"]


def read_catalog(path):
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing = set(COLUMNS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError("CSV 缺少列：" + ", ".join(sorted(missing)))
        rows = list(reader)
    seen = set()
    for row in rows:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("CSV 行列数不一致，请检查逗号和引号")
        code = row["编号"].strip()
        if not re.fullmatch(r"[A-Z]\d+", code) or code[0] not in MODULES.values():
            raise ValueError("无效或尚未配置模块的功能编号：" + code)
        if code in seen:
            raise ValueError("重复功能编号：" + code)
        if not row["功能"].strip():
            raise ValueError("功能名称为空：" + code)
        row["编号"] = code
        seen.add(code)
        for field in ("Figma设计链接", "Prototype播放链接"):
            link = row[field].strip()
            if link and urlsplit(link).scheme not in ("https", "http"):
                raise ValueError("设计/原型链接应为完整网页地址：" + code)
    if not rows:
        raise ValueError("功能目录不能为空")
    return rows


def catalog_table(rows, prefix):
    def clean(value):
        return value.replace("|", "／").replace("\r", "").replace("\n", "；")

    def link(label, value):
        return f"[{label}]({value.strip()})" if value.strip() else "待回填"

    lines = ["| " + " | ".join(HEADERS) + " |", "| " + " | ".join(["---"] * len(HEADERS)) + " |"]
    for row in rows:
        if not row["编号"].startswith(prefix):
            continue
        values = [row["编号"], row["功能"] + "；位置：" + row["页面或呈现位置"], row["模块关系"], row["代码证据与范围"], row["关联流程"], link("查看界面", row["Figma设计链接"]), link("播放局部流程", row["Prototype播放链接"]), row["验证状态"] + "；" + row["覆盖与缺口"], row["核对日期"] + "；" + row["Figma版本记录"]]
        lines.append("| " + " | ".join(clean(value) for value in values) + " |")
    return "\n".join(lines)


def sync_catalog(text, rows):
    for number, prefix in MODULES.items():
        section = re.compile(rf"(^### 4\.{number} [^\n]+\n)(.*?)(?=^### |^## |\Z)", re.M | re.S)
        def replace(match):
            body = match[2]
            table = catalog_table(rows, prefix)
            body, count = re.subn(r"(?:^\|[^\n]*\n?)+", lambda _: table + "\n", body, count=1, flags=re.M)
            return match[1] + (body if count else body.rstrip() + "\n\n" + table + "\n\n")
        text, count = section.subn(replace, text, count=1)
        if count != 1:
            raise ValueError(f"产品文档缺少功能目录章节 4.{number}（{prefix} 组）")
    return text


class PageCheck(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.anchors, self.images = set(), [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href", "").startswith("#"):
            self.anchors.append(unquote(attrs["href"][1:]))
        if tag == "img" and "src" in attrs:
            self.images.append(attrs["src"])


def build(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output == root or output in root.parents:
        raise ValueError("输出目录不能覆盖源文档目录")
    rows = read_catalog(root / "功能目录.csv")
    source = (root / "产品全貌.md").read_text(encoding="utf-8-sig")
    text = sync_catalog(source, rows)
    assets = {}

    def local_file(relative):
        path = (root / unquote(relative)).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("缺失或无效的图表/图片：" + relative)
        assets[path.relative_to(root).as_posix()] = path
        return path

    def diagram(match):
        alt, reference = match.groups()
        if urlsplit(reference).scheme:
            return match[0]
        path = local_file(reference)
        if path.suffix.lower() != ".svg":
            return match[0]
        svg = path.read_text(encoding="utf-8")
        svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
        return f'\n\n<figure>\n{svg}\n<figcaption>{html.escape(alt)}</figcaption></figure>\n\n'

    rendered_text = re.sub(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", diagram, text, flags=re.M)
    content = markdown.markdown(rendered_text, extensions=["tables", "fenced_code", "sane_lists", "toc"], extension_configs={"toc": {"slugify": lambda value, separator: re.sub(r"[^\w\u4e00-\u9fff]+", "-", value)}})
    content = content.replace("<table>", '<div class="table-scroll"><table>').replace("</table>", "</table></div>")
    template = (root / "site_template.html").read_text(encoding="utf-8")
    if template.count("{{CONTENT}}") != 1:
        raise ValueError("网页模板必须包含一个 CONTENT 占位符")
    commit = os.environ.get("GITHUB_SHA", "local")
    result = template.replace("{{CONTENT}}", content).replace("{{COMMIT}}", html.escape(commit, quote=True))
    check = PageCheck()
    check.feed(result)
    missing = set(check.anchors) - check.ids - {""}
    if missing:
        raise ValueError("失效的文档内跳转：" + ", ".join(sorted(missing)))
    for image in check.images:
        if not urlsplit(image).scheme:
            local_file(image)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    (output / "index.html").write_text(result, encoding="utf-8")
    (output / "产品全貌.md").write_text(text, encoding="utf-8")
    shutil.copyfile(root / "功能目录.csv", output / "功能目录.csv")
    for relative, path in assets.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    info = {"commit": commit, "features": len(rows), "diagrams": sum(path.suffix.lower() == ".svg" for path in assets.values()), "sources": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in ("产品全貌.md", "功能目录.csv")}}
    (output / "build-info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(info, ensure_ascii=False))
    return info


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    build(here, here / "_site")
