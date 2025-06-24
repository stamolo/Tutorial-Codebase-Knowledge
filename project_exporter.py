#!/usr/bin/env python3
# project_exporter.py — Export a project's structure and file contents into a single text file.

from __future__ import annotations
import argparse
import os
from pathlib import Path
from typing import Iterable, Set

# --- configuration ---------------------------------------------------------
# «Белый» список исключений: показываем в структуре, но не заходим внутрь и не включаем в контент
DEFAULT_EXCLUDES: Set[str] = {
'output', '.env', '.dockerignore', 'README.md'

}

# Чёрный список: полностью игнорируемые элементы
DEFAULT_BLACKLIST: Set[str] = {
    '.venv', 'docs', 'assets', '__pycache__', '.idea', '.git','.pytest_cache'
    ,'project_dump.txt','.clinerules', '.cursorrules', '.gitignore'
    ,'.windsurfrules', 'logs', 'llm_cache.json', '.env.sample'
}

DEFAULT_MAX_BYTES = 1_000_000  # 1 MiB
STRUCTURE_HEADER = "=== PROJECT STRUCTURE ==="
CONTENT_HEADER = "=== FILE CONTENTS ==="

# --- helpers ---------------------------------------------------------------

def is_binary(path: Path, sniff: int = 1024) -> bool:
    """Heuristically detect binary files by looking for NUL bytes."""
    try:
        with path.open('rb') as fp:
            return b'\0' in fp.read(sniff)
    except Exception:
        return True

def iter_structure(
    dir_path: Path,
    blacklist: Set[str],
    indent_level: int = 0
) -> Iterable[str]:
    """
    Рекурсивно обходит каталог dir_path и выдаёт его структуру:
      - Пропускает всё, что в blacklist.
      - Все остальные папки и файлы показывает с отступами.
      - Не делает различий между DEFAULT_EXCLUDES и обычными элементами —
        для всех выводит полную структуру.
    """
    indent = '    ' * indent_level
    name = dir_path.name if indent_level else '.'
    yield f"{indent}{name}/"

    for item in sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
        if item.name in blacklist:
            continue
        if item.is_dir():
            yield from iter_structure(item, blacklist, indent_level + 1)
        else:
            yield f"{indent}    {item.name}"

def dump_project(
    root: Path,
    out_file: Path,
    max_bytes: int,
    skip_binary: bool,
    excludes: Set[str],
    blacklist: Set[str],
):
    """Записывает в out_file структуру и содержимое проекта."""
    with out_file.open('w', encoding='utf-8', errors='replace') as out:
        # --- PROJECT STRUCTURE ---
        out.write(f"{STRUCTURE_HEADER}\n")
        for line in iter_structure(root, blacklist):
            out.write(line + "\n")
        out.write("\n\n")

        # --- FILE CONTENTS ---
        out.write(f"{CONTENT_HEADER}\n")
        for path in root.rglob('*'):
            # 1) Полностью игнорируем blacklist
            if any(part in blacklist for part in path.parts):
                continue
            # 2) Пропускаем сами каталоги
            if path.is_dir():
                continue
            # 3) Пропускаем файлы из excludes (и всё, что в них лежит)
            if any(part in excludes for part in path.parts):
                continue
            # 4) Ограничение размера
            if path.stat().st_size > max_bytes:
                continue
            # 5) Опционально бинарные
            if skip_binary and is_binary(path):
                continue

            rel = path.relative_to(root)
            out.write(f"### {rel.as_posix()}\n")
            try:
                out.write(path.read_text(encoding='utf-8', errors='replace'))
            except Exception as exc:
                out.write(f"<error reading file: {exc}>\n")
            out.write("\n\n")

# --- CLI -------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Export a project's structure and file contents into a single text file."
    )
    parser.add_argument('project_root', type=Path, help='Path to the project directory')
    parser.add_argument('-o', '--output', type=Path, default=Path('project_dump.txt'),
                        help='Output file path')
    parser.add_argument('--max-bytes', type=int, default=DEFAULT_MAX_BYTES,
                        help='Skip files larger than this many bytes')
    parser.add_argument('--skip-binary', action='store_true',
                        help='Skip files detected as binary')
    parser.add_argument('--exclude', nargs='*', default=[], metavar='NAME',
                        help='Дополнительные директории/файлы, которые выводить в структуре, но не включать в контент')
    return parser.parse_args()

def main():
    args = parse_args()
    script_name = Path(__file__).name
    output_name = args.output.name

    # Собираем списки: в excludes попадают DEFAULT_EXCLUDES + пользовательские + сам скрипт и выходной файл
    all_excludes = DEFAULT_EXCLUDES.union(args.exclude, {script_name, output_name})
    all_blacklist = DEFAULT_BLACKLIST

    dump_project(
        args.project_root,
        args.output,
        args.max_bytes,
        args.skip_binary,
        all_excludes,
        all_blacklist,
    )
    print(f"Exported project to {args.output!s}")

if __name__ == '__main__':
    main()