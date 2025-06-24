from pathlib import Path
import utils


def _make_dummy_files(tmp_path):
    mmd_file = tmp_path / "diagram.mmd"
    mmd_file.write_text("flowchart TD; A --> B;")
    png_file = tmp_path / "diagram.png"
    return mmd_file, png_file


# --- 1. mmdc отсутствует ---------------------------------------------------
def test_generate_mermaid_png_not_available(monkeypatch, tmp_path):
    # Подменяем shutil.which → None
    monkeypatch.setattr(utils, "shutil", utils.shutil)
    monkeypatch.setattr(utils.shutil, "which", lambda _cmd: None)

    mmd_file, png_file = _make_dummy_files(tmp_path)

    result = utils.generate_mermaid_png(mmd_file, png_file)

    assert result is False
    assert not png_file.exists()


# --- 2. mmdc найден, но запуск -> FileNotFoundError ------------------------
def test_generate_mermaid_png_run_not_found(monkeypatch, tmp_path):
    monkeypatch.setattr(utils.shutil, "which", lambda _cmd: "mmdc")  # путь «найден»

    def _fake_run(*_args, **_kwargs):
        raise FileNotFoundError("mmdc missing at runtime")

    monkeypatch.setattr(utils.subprocess, "run", _fake_run)

    mmd_file, png_file = _make_dummy_files(tmp_path)

    result = utils.generate_mermaid_png(mmd_file, png_file)

    assert result is False
    assert not png_file.exists()


# --- 3. Успех --------------------------------------------------------------
def test_generate_mermaid_png_success(monkeypatch, tmp_path):
    monkeypatch.setattr(utils.shutil, "which", lambda _cmd: "mmdc")

    class _DummyCompletedProcess:
        def __init__(self): self.returncode = 0

    def _fake_run(args, **kwargs):
        # симулируем создание файла по аргументу после "-o"
        out_idx = args.index("-o") + 1
        Path(args[out_idx]).write_bytes(b"fake-png")
        return _DummyCompletedProcess()

    monkeypatch.setattr(utils.subprocess, "run", _fake_run)

    mmd_file, png_file = _make_dummy_files(tmp_path)

    result = utils.generate_mermaid_png(mmd_file, png_file)

    assert result is True
    assert png_file.exists()
