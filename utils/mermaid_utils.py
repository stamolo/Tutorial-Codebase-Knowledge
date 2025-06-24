"""
Обработка блоков ```mermaid``` в Markdown-тексте.

Функция `render_mermaid_blocks` выполняет:

* Поиск всех внешних ```mermaid```-блоков.
* Если содержимое похоже на настоящую диаграмму — сохраняет код в
  `<sha>.mmd`, рендерит PNG через `png_func` (совместимо с
  `utils.generate_mermaid_png`). При успешном рендере заменяет блок
  на `![Diagram](<sha>.png)`.
* Если блок «демонстрационный» (например, внутри — пример YAML/JSON) или
  рендер завершился неуспешно (`png_func` → False), исходный Markdown
  остаётся без изменений.
* Вложенные блоки ```lang … ``` внутри ```mermaid``` поддерживаются
  счётчиком `nested`: внешний блок закрывается только после парного
  ``` того же уровня вложенности.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable, List

__all__ = ["render_mermaid_blocks", "_sha10"]


# ---------- служебные ------------------------------------------------------
def _sha10(text: str) -> str:
    """Короткий идентификатор диаграммы — первые 10 символов SHA-1."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


MERMAID_PREFIXES: tuple[str, ...] = (
    "graph ",
    "flowchart",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram",
    "erDiagram",
    "journey",
    "gantt",
)


# ---------- главная функция -----------------------------------------------
def render_mermaid_blocks(
    md_text: str,
    out_dir: Path,
    png_func: Callable[[Path, Path], bool],
) -> str:
    """
    Преобразует Markdown, рендеря реальные диаграммы Mermaid в PNG.

    Parameters
    ----------
    md_text:
        Исходный Markdown.
    out_dir:
        Каталог, куда сохранять *.mmd / *.png.
    png_func:
        Функция рендера — должна вернуть True при успешном создании PNG.

    Returns
    -------
    str
        Модифицированный Markdown.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    result: List[str] = []
    in_mermaid = False
    nested = 0
    block: List[str] = []

    for raw in md_text.splitlines():
        stripped = raw.strip()

        # ---------- открытие внешнего блока ----------
        if not in_mermaid and stripped.startswith("```mermaid"):
            in_mermaid = True
            block.clear()
            continue

        # ---------- внутри mermaid-блока --------------
        if in_mermaid:
            # встречен ```
            if stripped.startswith("```"):
                # вложенный ```lang (например ```yaml)
                if stripped != "```":
                    nested += 1
                    block.append(raw)
                    continue

                # закрытие вложенного блока
                if nested:
                    nested -= 1
                    block.append(raw)
                    continue

                # закрываем ВНЕШНИЙ mermaid-блок
                code = "\n".join(block).strip()
                first = next((ln for ln in code.splitlines() if ln.strip()), "")

                is_real = first.lstrip().startswith(MERMAID_PREFIXES)
                replaced = False

                if is_real:
                    sha = _sha10(code)
                    png_name = f"{sha}.png"
                    png_path = out_dir / png_name

                    # .mmd сохраняем независимо от результата рендера —
                    # полезно для отладки
                    mmd_path = out_dir / f"{sha}.mmd"
                    if not mmd_path.exists():
                        mmd_path.write_text(code, encoding="utf-8")

                    # рендер PNG (только если ещё нет)
                    ok = png_path.exists() or png_func(mmd_path, png_path)

                    if ok:
                        result.append(f"![Diagram]({png_name})")
                        replaced = True

                if not replaced:
                    # либо демонстрационный блок, либо рендер упал —
                    # возвращаем исходный блок
                    result.append("```mermaid")
                    result.extend(block)
                    result.append("```")

                in_mermaid = False
                continue

            # обычная строка внутри mermaid
            block.append(raw)
            continue

        # ---------- вне mermaid-блока ------------------
        result.append(raw)

    # незакрытый mermaid в конце файла — возвращаем как есть
    if in_mermaid:
        result.append("```mermaid")
        result.extend(block)

    return "\n".join(result)
