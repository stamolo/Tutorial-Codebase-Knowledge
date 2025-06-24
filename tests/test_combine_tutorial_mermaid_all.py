# tests/test_combine_tutorial_mermaid_all.py
"""
Расширенные тесты обработки Mermaid-диаграмм.

Проверяем:
  1. diagram.png + PNG главы, а второй mermaid-блок в index.md остаётся.
  2. Повторяющийся код диаграммы рендерится один раз и переиспользуется.
"""
from pathlib import Path
import hashlib
import nodes
import pytest


# --------------------------- общие утилиты ---------------------------------
def _sha10(code: str) -> str:
    return hashlib.sha1(code.encode("utf-8")).hexdigest()[:10]


def _fake_png(mmd: Path, png: Path):
    png.write_bytes(b"fake-bytes")
    return True


# ------------------------ ТЕСТ 1 -------------------------------------------
def test_chapter_png_and_second_block_kept(tmp_path, monkeypatch):
    """
    • diagram.png создаётся;
    • глава получила свой <hash>.png;
    • второй mermaid-блок в index.md сохранён.
    """
    monkeypatch.setattr(nodes, "generate_mermaid_png", _fake_png)

    mer_code = "graph TD; A-->B;"
    h = _sha10(mer_code)

    shared = {
        "project_name": "merdemo",
        "output_dir": str(tmp_path),
        "repo_url": "https://ex/repo",
        "relationships": {"summary": "Sum", "details": [{"from": 0, "to": 0, "label": "Self"}]},
        "chapter_order": [0],
        "abstractions": [{"name": "Core", "description": "D", "files": []}],
        "chapters": [f"# Chapter 1\n\n```mermaid\n{mer_code}\n```"],
    }

    ct = nodes.CombineTutorial()
    prep = ct.prep(shared)

    # --- добавляем второй mermaid-блок, который должен сохраниться ----------
    prep["index_content"] += "\n\n```mermaid\ngraph TD; X-->Y;\n```\n"

    out = Path(ct.exec(prep))

    # 1. PNG-файлы
    assert (out / "diagram.png").exists(), "diagram.png не создан"
    assert (out / f"{h}.png").exists(), "PNG для главы не создан"

    # 2. index.md: один Architecture Diagram + один mermaid-блок
    idx = (out / "index.md").read_text(encoding="utf-8")
    assert idx.count("![Architecture Diagram]") == 1
    assert idx.split("![Architecture Diagram]")[1].count("```mermaid") == 1, \
        "Второй mermaid-блок пропал"


# ------------------------ ТЕСТ 2 -------------------------------------------
def test_identical_mermaid_code_reuses_png(tmp_path, monkeypatch):
    """Одинаковый mermaid-код в двух главах → один PNG, обе главы ссылаются на него."""
    monkeypatch.setattr(nodes, "generate_mermaid_png", _fake_png)

    code = "flowchart TD; X-->Y;"
    sha = _sha10(code)

    shared = {
        "project_name": "reuse_demo",
        "output_dir": str(tmp_path),
        "repo_url": "https://ex/repo",
        "relationships": {"summary": "S", "details": [{"from": 0, "to": 1, "label": "L"}]},
        "chapter_order": [0, 1],
        "abstractions": [
            {"name": "A", "description": "d", "files": []},
            {"name": "B", "description": "d", "files": []},
        ],
        "chapters": [
            f"# Ch1\n\n```mermaid\n{code}\n```",
            f"# Ch2\n\n```mermaid\n{code}\n```",
        ],
    }

    ct = nodes.CombineTutorial()
    out = Path(ct.exec(ct.prep(shared)))

    # существует ровно один PNG с данным хэшем
    pngs = list(out.glob(f"{sha}.png"))
    assert len(pngs) == 1, "Создано несколько одинаковых PNG"

    # обе главы ссылаются на этот PNG
    marker = f"![Diagram]({sha}.png)"
    assert marker in (out / "01_a.md").read_text(encoding="utf-8")
    assert marker in (out / "02_b.md").read_text(encoding="utf-8")
