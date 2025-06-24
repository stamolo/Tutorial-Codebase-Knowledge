# tests/test_combine_tutorial_edge_cases.py
"""
Edge-case-тесты для узла CombineTutorial и функции generate_mermaid_png.

Сценарии:
  1. Несколько ```mermaid```-блоков, PNG успешно сгенерирован –
     заменяем только первый, остальные остаются.
  2. Несколько ```mermaid```-блоков, PNG НЕ сгенерирован –
     блоки остаются без изменений, PNG-файла нет.
  3. Тайм-аут CLI mmdc обрабатывается корректно (generate_mermaid_png → False).
"""

import subprocess
from pathlib import Path
import nodes
import utils
import pytest


# ---------- вспомогалка: минимальный shared -------------------------------
def _minimal_shared(tmp_path):
    """Возвращает минимальный набор данных для CombineTutorial."""
    return {
        "project_name": "demo_project",
        "output_dir": str(tmp_path),
        "repo_url": "https://example.com/repo",
        "relationships": {
            "summary": "Demo summary",
            "details": [{"from": 0, "to": 0, "label": "Self"}],
        },
        "chapter_order": [0],
        "abstractions": [
            {"name": "Core", "description": "Desc", "files": []}
        ],
        "chapters": [
            "# Chapter 1: Core\nContent\n"
        ],
    }


# ---------------------------------------------------------------------------


def test_multiple_mermaid_blocks_png_success(tmp_path, monkeypatch):
    """
    В index.md два блока ```mermaid```.
    При успешной генерации PNG заменяется только первый блок,
    второй остаётся нетронутым.
    """
    # --- фиктивная успешная генерация PNG ---
    def _fake_generate(mmd, png):
        Path(png).write_bytes(b"png-bytes")
        return True

    monkeypatch.setattr(nodes, "generate_mermaid_png", _fake_generate)

    # --- готовим shared + подменяем index_content ---
    shared = _minimal_shared(tmp_path)
    ct = nodes.CombineTutorial()
    prep = ct.prep(shared)

    # добавляем второй дополнительныӗ блок ```mermaid```
    extra = "\n\n```mermaid\ngraph TD; X-->Y;\n```\n"
    prep["index_content"] += extra

    out_dir = Path(ct.exec(prep))
    index_text = (out_dir / "index.md").read_text(encoding="utf-8")

    # PNG-файл должен существовать
    assert (out_dir / "diagram.png").exists()

    # Замена только для первого блока
    assert index_text.count("![Architecture Diagram]") == 1
    # Второй блок вообще должен остаться
    assert index_text.count("```mermaid") == 1


def test_multiple_mermaid_blocks_png_failure(tmp_path, monkeypatch):
    """
    PNG не генерируется → оба блока ```mermaid``` остаются,
    PNG-файл не создаётся.
    """
    monkeypatch.setattr(nodes, "generate_mermaid_png", lambda *_: False)

    shared = _minimal_shared(tmp_path)
    ct = nodes.CombineTutorial()
    prep = ct.prep(shared)
    prep["index_content"] += "\n\n```mermaid\ngraph TD; X-->Y;\n```\n"

    out_dir = Path(ct.exec(prep))
    index_text = (out_dir / "index.md").read_text(encoding="utf-8")

    # PNG-файла быть не должно
    assert not (out_dir / "diagram.png").exists()
    # Оба блока на месте
    assert index_text.count("```mermaid") == 2
    # Никакой замены не произошло
    assert "![Architecture Diagram]" not in index_text


def test_generate_mermaid_png_timeout(tmp_path, monkeypatch):
    """
    generate_mermaid_png(): subprocess.TimeoutExpired → функция тихо
    возвращает False и не создает PNG-файл.
    """
    # shutil.which → «нашёл» CLI
    monkeypatch.setattr(utils.shutil, "which", lambda *_: "mmdc")

    # subprocess.run бросает TimeoutExpired
    def _fake_run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="mmdc", timeout=60)

    monkeypatch.setattr(utils.subprocess, "run", _fake_run)

    mmd_file = tmp_path / "d.mmd"
    mmd_file.write_text("graph TD;A-->B")
    png_file = tmp_path / "d.png"

    assert utils.generate_mermaid_png(mmd_file, png_file) is False
    assert not png_file.exists()
