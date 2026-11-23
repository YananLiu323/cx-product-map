"""将阶段资料与 CX 参考构建资源打包，不修改参考文件。"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path, help='包含 cx-ref 的 frontend-ref-main 目录')
    parser.add_argument('--version', default='V1')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    version = root / '版本' / args.version
    manifest_path = version / '版本清单.json'
    manifest = json.loads(manifest_path.read_text())
    source = args.source.resolve()
    ref = source / 'cx-ref'
    if not ref.is_dir() or not (source / 'package.json').is_file():
        raise SystemExit('参考目录不完整：需要 cx-ref/ 和 package.json')
    output = root / '交付包'
    output.mkdir(exist_ok=True)
    target = output / f'CX-{args.version}-资料包.zip'
    if target.exists():
        raise SystemExit('同名资料包已存在，停止，避免覆盖')
    sources = sorted(p for p in ref.rglob('*') if p.is_file())
    sources.append(source / 'package.json')
    for p in sources:
        if not p.resolve().is_relative_to(source):
            raise SystemExit('参考目录中存在指向范围外的文件，停止')
    entries = []
    temporary = target.with_suffix('.zip.part')
    prefix = f'CX-{args.version}/'
    with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED, compresslevel=4) as archive:
        for index, p in enumerate(sources, 1):
            rel = p.relative_to(source).as_posix()
            digest = hashlib.sha256()
            size = 0
            with p.open('rb') as reader, archive.open(prefix + '代码/' + rel, 'w', force_zip64=True) as writer:
                while chunk := reader.read(1024 * 1024):
                    digest.update(chunk)
                    size += len(chunk)
                    writer.write(chunk)
            entries.append({'path': rel, 'bytes': size, 'sha256': digest.hexdigest()})
            if index % 5000 == 0:
                print(f'已收录 {index}/{len(sources)} 个参考文件', flush=True)
        package_copy = version / '代码/package.json'
        package_copy.write_bytes((source / 'package.json').read_bytes())
        inventory = version / '代码/参考文件清单.json'
        inventory.write_text(json.dumps({'scope': ['cx-ref/', 'package.json'], 'files': entries}, ensure_ascii=False, indent=2) + '\n')
        manifest['source_archive'].update({'file_count': len(entries), 'bytes': sum(e['bytes'] for e in entries), 'inventory': '代码/参考文件清单.json'})
        manifest['package'].update({'generated': True, 'name': target.name, 'sha256_file': target.name + '.sha256', 'contains_fig': False, 'status': '已有资料包；不含完整 Figma 归档'})
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        tracked = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root).decode().split('\0')
        for name in sorted(set(filter(None, tracked))):
            p = root / name
            if p.is_file() and not name.startswith('交付包/'):
                archive.write(p, prefix + name)
    temporary.replace(target)
    hasher = hashlib.sha256()
    with target.open('rb') as reader:
        while chunk := reader.read(1024 * 1024):
            hasher.update(chunk)
    digest = hasher.hexdigest()
    target.with_name(target.name + '.sha256').write_text(f'{digest}  {target.name}\n')
    print(json.dumps({'archive': str(target), 'bytes': target.stat().st_size, 'sha256': digest, 'source_files': len(entries), 'contains_fig': False}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
