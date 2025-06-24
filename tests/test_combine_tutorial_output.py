# tests/test_combine_tutorial_output.py
from pathlib import Path
import nodes                     # узлы Flow лежат здесь
import pytest

def test_combine_tutorial_creates_markdown_and_png(tmp_path, monkeypatch):
    """
    Интеграционный тест узла CombineTutorial.
    Проверяет, что после его выполнения на диске оказываются:
      • index.md с заменённым Mermaid-блоком
      • diagram.mmd (исходник)
      • diagram.png (сгенерированный; создаём через мок)
      • файлы глав 01_*.md, 02_*.md …
    """

    # --- 1. Мокаем генератор PNG ------------------------------------------
    generated_pngs = []

    def _fake_generate_mermaid_png(mmd_path, png_path):
        # Реалистично: CLI отрендерил PNG-файл
        Path(png_path).write_bytes(b"fake-png-bytes")
        generated_pngs.append(Path(png_path))
        return True

    # в nodes.py функция уже импортирована: monkeypatch именно там
    monkeypatch.setattr(nodes, "generate_mermaid_png", _fake_generate_mermaid_png)

    # --- 2. Готовим минимально-достаточный shared -------------------------
    shared = {
        "project_name": "demo_project",
        "output_dir": str(tmp_path),                     # пишем в temp-каталог
        "repo_url": "https://example.com/repo",

        "relationships": {
            "summary": "Demo summary for the tutorial.",
            "details": [
                {"from": 0, "to": 1, "label": "Uses"},
            ],
        },

        "chapter_order": [0, 1],
        "abstractions": [
            {"name": "Core",   "description": "Main logic",   "files": []},
            {"name": "Helper", "description": "Aux routines", "files": []},
        ],
        "chapters": [
            "# Chapter 1: Core\n\nContent of Core chapter.\n",
            "# Chapter 2: Helper\n\nContent of Helper chapter.\n",
        ],
    }

    # --- 3. Запускаем узел -------------------------------------------------
    ct = nodes.CombineTutorial()
    prep_res = ct.prep(shared)
    output_dir = Path(ct.exec(prep_res))         # метод возвращает путь
    ct.post(shared, prep_res, str(output_dir))   # чтобы shared заполнить

    # --- 4. Проверяем результат -------------------------------------------
    # 4.1 Набор обязательных файлов
    expected_files = {
        output_dir / "index.md",
        output_dir / "diagram.mmd",
        output_dir / "diagram.png",
        output_dir / "01_core.md",
        output_dir / "02_helper.md",
    }
    for path in expected_files:
        assert path.exists(), f"Файл {path.name} не создан"

    # 4.2 Проверяем содержимое index.md
    index_text = (output_dir / "index.md").read_text(encoding="utf-8")
    assert "![Architecture Diagram](diagram.png)" in index_text, \
        "Mermaid-блок не заменён на ссылку на PNG"
    assert "1. [Core](01_core.md)"   in index_text, "Оглавление не содержит Core"
    assert "2. [Helper](02_helper.md)" in index_text, "Оглавление не содержит Helper"

    # 4.3 PNG действительно создан через мок
    assert generated_pngs and generated_pngs[0].exists(), "PNG-файл не был создан моком"
