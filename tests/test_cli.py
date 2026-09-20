from pathlib import Path
from unittest.mock import patch

import pytest
from tg_rich_converter import __version__
from tg_rich_converter.cli import main, render_banner


def test_banner_rendering_with_and_without_color(monkeypatch):
    # Тест 1: С включёнными цветами (эмуляция TTY)
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.delenv("NO_COLOR", raising=False)
    colored_banner = render_banner()
    assert "TG-Rich CLI" in colored_banner
    assert "\033[" in colored_banner  # Наличие ANSI-последовательностей

    # Тест 2: Без цветов (эмуляция NO_COLOR)
    monkeypatch.setenv("NO_COLOR", "1")
    plain_banner = render_banner()
    assert "TG-Rich Converter CLI" in plain_banner
    assert "\033[" not in plain_banner


def test_cli_convert_to_stdout(tmp_path: Path, capsys):
    md_file = tmp_path / "test.md"
    md_file.write_text("# Заголовок\n\nТекст с формулой $x^2$.", encoding="utf-8")

    exit_code = main([str(md_file), "-q"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "<h1>Заголовок</h1>" in captured.out
    assert "<tg-math>x^2</tg-math>" in captured.out


def test_cli_convert_to_output_file(tmp_path: Path):
    md_file = tmp_path / "input.md"
    out_file = tmp_path / "output.html"
    md_file.write_text("**Жирный текст**", encoding="utf-8")

    exit_code = main([str(md_file), "-o", str(out_file), "-q"])

    assert exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "<b>Жирный текст</b>" in content


def test_cli_preview_flag(tmp_path: Path):
    md_file = tmp_path / "doc.md"
    preview_file = tmp_path / "custom_preview.html"
    md_file.write_text("<think>Рассуждение</think>\nОтвет.", encoding="utf-8")

    exit_code = main([
        str(md_file),
        "-p", str(preview_file),
        "-t", "Анализ модели",
        "-q",
    ])

    assert exit_code == 0
    assert preview_file.exists()
    content = preview_file.read_text(encoding="utf-8")
    assert "<title>Telegram Rich Preview — doc.md</title>" in content
    assert "<summary>Анализ модели</summary>" in content
    assert "katex.min.js" in content


def test_cli_open_browser_mocked(tmp_path: Path):
    md_file = tmp_path / "doc.md"
    preview_file = tmp_path / "preview.html"
    md_file.write_text("Hello World", encoding="utf-8")

    with patch("webbrowser.open") as mock_open:
        exit_code = main([str(md_file), "-p", str(preview_file), "--open", "-q"])
        assert exit_code == 0
        assert mock_open.called
        called_url = mock_open.call_args[0][0]
        assert "preview.html" in called_url


def test_cli_split_stdout(tmp_path: Path, capsys):
    md_file = tmp_path / "long.md"
    text = "**Блок данных для нарезки сообщения.**\n\n" * 10
    md_file.write_text(text, encoding="utf-8")

    exit_code = main([str(md_file), "--split", "--limit", "120", "-q"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "<!-- ====== ЧАСТЬ 1 /" in captured.out
    assert "<b>Блок данных" in captured.out


def test_cli_split_to_files(tmp_path: Path):
    md_file = tmp_path / "huge.md"
    text = "*Квантовое состояние и вычисления.*\n\n" * 15
    md_file.write_text(text, encoding="utf-8")

    out_pattern = tmp_path / "chunk.html"
    exit_code = main([
        str(md_file),
        "--split",
        "--limit", "100",
        "-o", str(out_pattern),
        "-q",
    ])

    assert exit_code == 0
    created_parts = list(tmp_path.glob("chunk_part*.html"))
    assert len(created_parts) >= 2
    for part in created_parts:
        content = part.read_text(encoding="utf-8")
        assert len(content) <= 100
        assert content.count("<i>") == content.count("</i>")


def test_cli_stdin_pipeline(monkeypatch, capsys):
    from io import StringIO

    monkeypatch.setattr("sys.stdin", StringIO("Тест из stdin: **успех**"))
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)

    exit_code = main(["-", "-q"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Тест из stdin: <b>успех</b>" in captured.out


def test_cli_file_not_found(capsys):
    exit_code = main(["non_existent_file_999.md", "-q"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "не найден" in captured.err


def test_cli_empty_input(tmp_path: Path, capsys):
    empty_file = tmp_path / "empty.md"
    empty_file.write_text("   \n   ", encoding="utf-8")

    exit_code = main([str(empty_file), "-q"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "пустой текст" in captured.err