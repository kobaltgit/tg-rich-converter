from pathlib import Path
from unittest.mock import patch

import pytest
from tg_rich_converter import __version__
from tg_rich_converter.cli import _detect_language, _extract_lang, main, render_banner


def test_detect_language(monkeypatch):
    monkeypatch.setenv("TG_RICH_LANG", "ru")
    assert _detect_language() == "ru"

    monkeypatch.setenv("TG_RICH_LANG", "en")
    assert _detect_language() == "en"

    monkeypatch.delenv("TG_RICH_LANG", raising=False)
    monkeypatch.setenv("LANG", "ru_RU.UTF-8")
    assert _detect_language() == "ru"

    monkeypatch.setenv("LANG", "en_US.UTF-8")
    assert _detect_language() == "en"


def test_extract_lang():
    assert _extract_lang(["--help", "--lang", "en"]) == "en"
    assert _extract_lang(["--lang", "ru", "--preview"]) == "ru"
    assert _extract_lang(["--lang=en", "-q"]) == "en"
    assert _extract_lang(["--lang=ru"]) == "ru"


def test_cli_help_localization(capsys):
    with pytest.raises(SystemExit) as exc_info_en:
        main(["--help", "--lang", "en"])
    assert exc_info_en.value.code == 0
    captured_en = capsys.readouterr()
    assert "Convert LLM Markdown" in captured_en.out
    assert "show this help message and exit" in captured_en.out

    with pytest.raises(SystemExit) as exc_info_ru:
        main(["--help", "--lang", "ru"])
    assert exc_info_ru.value.code == 0
    captured_ru = capsys.readouterr()
    assert "Конвертер Markdown" in captured_ru.out
    assert "показать эту справку и выйти" in captured_ru.out


def test_banner_rendering_with_and_without_color(monkeypatch):
    # Тест 1: С включёнными цветами на русском
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.delenv("NO_COLOR", raising=False)
    ru_banner = render_banner(lang="ru")
    assert "TG-Rich CLI" in ru_banner
    assert "Конвертер сообщений для Telegram" in ru_banner
    assert "\033[" in ru_banner

    # Тест 2: С включёнными цветами на английском
    en_banner = render_banner(lang="en")
    assert "Telegram Rich Messages Converter" in en_banner

    # Тест 3: Без цветов (эмуляция NO_COLOR)
    monkeypatch.setenv("NO_COLOR", "1")
    plain_ru_banner = render_banner(lang="ru")
    assert "Конвертер Telegram Rich HTML" in plain_ru_banner
    assert "\033[" not in plain_ru_banner


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


def test_cli_lang_flag_override(tmp_path: Path):
    md_file = tmp_path / "think_doc.md"
    preview_en = tmp_path / "preview_en.html"
    preview_ru = tmp_path / "preview_ru.html"
    md_file.write_text("<think>Deep Thought</think>\nDone.", encoding="utf-8")

    # Проверка языка EN (дефолтный заголовок 'Reasoning')
    exit_code_en = main([
        str(md_file),
        "-p", str(preview_en),
        "--lang", "en",
        "-q",
    ])
    assert exit_code_en == 0
    assert "<summary>Reasoning</summary>" in preview_en.read_text(encoding="utf-8")

    # Проверка языка RU (дефолтный заголовок 'Размышления')
    exit_code_ru = main([
        str(md_file),
        "-p", str(preview_ru),
        "--lang", "ru",
        "-q",
    ])
    assert exit_code_ru == 0
    assert "<summary>Размышления</summary>" in preview_ru.read_text(encoding="utf-8")


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
    assert ("PART" in captured.out or "ЧАСТЬ" in captured.out)
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
    exit_code = main(["non_existent_file_999.md", "-q", "--lang", "ru"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "не найден" in captured.err


def test_cli_empty_input(tmp_path: Path, capsys):
    empty_file = tmp_path / "empty.md"
    empty_file.write_text("   \n   ", encoding="utf-8")

    exit_code = main([str(empty_file), "-q", "--lang", "ru"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "пустой текст" in captured.err