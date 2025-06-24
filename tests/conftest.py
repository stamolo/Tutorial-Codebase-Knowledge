# tests/conftest.py
"""
Автоматически подключается pytest-ом.
Делает так, чтобы корень репозитория был в PYTHONPATH,
и любой импорт вида `import utils` находил наш пакет utils.
"""
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]   # на уровень выше каталога tests
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
