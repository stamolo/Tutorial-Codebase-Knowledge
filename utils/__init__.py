# utils/__init__.py
import shutil
import subprocess
from pathlib import Path
from typing import Union


def is_tool_available(tool: str) -> bool:
    """Проверяет, доступен ли исполняемый файл `tool` в PATH."""
    return shutil.which(tool) is not None


def generate_mermaid_png(
    mmd_path: Union[str, Path],
    png_path: Union[str, Path],
) -> bool:
    """
    Конвертирует Mermaid-файл (.mmd) в PNG с помощью CLI `mmdc`.

    Возвращает
    ----------
    bool
        • True  — PNG успешно сгенерирован и сохранён.
        • False — CLI недоступна *или* при запуске произошла любая
          из перехватываемых ошибок.

    Функция устойчива к сбоям: при любой проблеме она молча возвращает False,
    чтобы не ронять основной workflow.
    """
    # 1) Проверяем, что CLI найдена в PATH
    mmdc_path = shutil.which("mmdc")
    if not mmdc_path:
        return False

    # 2) Пытаемся вызвать CLI
    try:
        subprocess.run(
            [mmdc_path, "-i", str(mmd_path), "-o", str(png_path)],
            check=True,
            timeout=60,  # защита от зависания
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        PermissionError,
        subprocess.TimeoutExpired,   # обработка тайм-аута
    ):
        return False
