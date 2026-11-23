"""检查阶段资料的原文件校验值、内部链接和归档状态。"""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import hashlib
import json
import re
import sys

root = Path(__file__).resolve().parents[1]
version = root / '版本/V1'
manifest = json.loads((version / '版本清单.json').read_text())
errors = []
for item in manifest['original_files']:
    p = version / item['path']
    if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != item['sha256']:
        errors.append('原文件不一致：' + item['path'])
new_docs = [root / name for name in ['README.md', '项目说明.md', '更新规则.md', '当前版本/README.md', '历史版本/README.md']]
new_docs += [p for p in version.rglob('*.md') if '原有文件' not in p.parts]
for p in new_docs:
    for value in re.findall(r'\]\(([^)]+)\)', p.read_text()):
        parsed = urlsplit(value)
        if parsed.scheme or value.startswith('#'):
            continue
        target = (p.parent / unquote(parsed.path)).resolve()
        if not target.exists():
            errors.append(f'内部链接不存在：{p.relative_to(root)} → {value}')
if manifest['figma']['fig_file'] is None and manifest['figma']['restore_verified']:
    errors.append('没有 .fig 却标记恢复验证通过')
if manifest['release']['published'] and not manifest['figma']['restore_verified']:
    errors.append('未通过设计恢复验证却标记正式发布')
print(json.dumps({'original_files': len(manifest['original_files']), 'new_documents': len(new_docs), 'errors': errors, 'status': manifest['status']}, ensure_ascii=False, indent=2))
sys.exit(bool(errors))
