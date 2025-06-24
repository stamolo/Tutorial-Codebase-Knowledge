# tests/test_combine_tutorial_variants.py
from pathlib import Path
import nodes
import pytest

# ======== вспомогалка для сжатой подготовки shared =========
def _minimal_shared(tmp_path):
    return {
        "project_name": "demo",
        "output_dir": str(tmp_path),
        "repo_url": "https://x/repo",
        "relationships": {
            "summary": "Demo",
            "details": [{"from": 0, "to": 0, "label": "Self"}],
        },
        "chapter_order": [0],
        "abstractions": [
            {"name": "Core", "description": "Desc", "files": []}
        ],
        "chapters": ["# Chapter 1: Core\nText\n"],
    }

# ---------- 1. PNG пропущен --------------
def test_combine_tutorial_without_png(tmp_path, monkeypatch):
    # fake_generate_mermaid_png → возвращает False (CLI нет)
    monkeypatch.setattr(
        nodes, "generate_mermaid_png",
        lambda *_: False
    )

    shared = _minimal_shared(tmp_path)
    ct = nodes.CombineTutorial()
    output = Path(ct.exec(ct.prep(shared)))

    # diagram.mmd должен быть, а diagram.png – нет
    assert (output / "diagram.mmd").exists()
    assert not (output / "diagram.png").exists()

    index_text = (output / "index.md").read_text(encoding="utf-8")
    assert "```mermaid" in index_text, \
        "Mermaid-блок не сохранился при отсутствии PNG"

# ---------- 2. Тайм-аут CLI --------------
def test_generate_mermaid_png_timeout(monkeypatch, tmp_path):
    from utils import generate_mermaid_png

    class _Timeout(Exception): pass

    def _fake_run(*_a, **_kw):
        raise subprocess.TimeoutExpired(cmd="mmdc", timeout=60)

    import utils, subprocess
    monkeypatch.setattr(utils, "shutil", utils.shutil)  # сохраняем which
    monkeypatch.setattr(utils.shutil, "which", lambda _:"mmdc")
    monkeypatch.setattr(utils.subprocess, "run", _fake_run)

    mmd = tmp_path / "d.mmd"; mmd.write_text("graph TD;A-->B")
    png = tmp_path / "d.png"

    assert generate_mermaid_png(mmd, png) is False, \
        "При TimeoutExpired функция должна вернуть False"
    assert not png.exists()
