# tests/test_mermaid_filtering.py
"""
Проверяем корректность фильтрации и рендера mermaid-блоков.
"""

from pathlib import Path
from utils.mermaid_utils import render_mermaid_blocks, _sha10


def _fake_png_success(src: Path, dst: Path) -> bool:
    dst.write_bytes(b"png")
    return True


def _fake_png_fail(src: Path, dst: Path) -> bool:
    return False


# ---------- 1. демонстрационный блок остаётся -----------------------------
def test_demo_block_kept(tmp_path):
    md_in = "Text\n```mermaid\n```yaml\n- name: demo\n```\n```\nEnd"
    md_out = render_mermaid_blocks(md_in, tmp_path, _fake_png_success)
    assert md_out == md_in
    assert not list(tmp_path.glob("*.png"))


# ---------- 2. валидная диаграмма → PNG + замена --------------------------
def test_real_mermaid_block_rendered(tmp_path):
    code = "graph TD; A-->B;"
    sha = _sha10(code)
    md_in = f"```mermaid\n{code}\n```"

    md_out = render_mermaid_blocks(md_in, tmp_path, _fake_png_success)

    assert f"![Diagram]({sha}.png)" in md_out
    assert (tmp_path / f"{sha}.png").exists()


# ---------- 3. ошибка рендера → блок не трогаем ---------------------------
def test_render_failure_keeps_block(tmp_path):
    code = "flowchart LR; A-->B;"
    md_in = f"```mermaid\n{code}\n```"

    md_out = render_mermaid_blocks(md_in, tmp_path, _fake_png_fail)

    # блок остался прежним, PNG нет
    assert md_out == md_in
    assert not list(tmp_path.glob("*.png"))
