"""CLI-интерфейс библиотеки tg-rich-converter."""

import argparse
import os
import sys
import webbrowser
from pathlib import Path
from typing import List, Optional

from . import __version__
from .converter import to_rich
from .preview import save_preview
from .splitter import split_rich_message

# ANSI TrueColor Escape Sequences (24-bit RGB)
_RESET = "\033[0m"
_BOLD = "\033[1m"
_COLOR_BUBBLE = "\033[38;2;43;82;120m"       # #2B5278 (Telegram Blue)
_COLOR_SIGMA = "\033[38;2;255;255;255m"       # #FFFFFF (White)
_COLOR_CHECKS = "\033[38;2;107;191;255m"      # #6BBFFF (Telegram Light Cyan)
_COLOR_TITLE = "\033[38;2;82;136;193m"        # #5288C1 (Accent Blue)
_COLOR_TEXT = "\033[38;2;220;230;242m"        # #DCE6F2 (Light Blue-Gray)
_COLOR_MUTED = "\033[38;2;127;145;164m"       # #7F91A4 (Secondary Gray)
_COLOR_GREEN = "\033[38;2;78;205;196m"       # #4ECDC4 (Success Cyan-Green)
_COLOR_WARN = "\033[38;2;255;190;11m"        # #FFBE0B (Warning Yellow)
_COLOR_ERR = "\033[38;2;255;0;110m"          # #FF006E (Error Pink-Red)


def _supports_color() -> bool:
    """Проверяет, поддерживает ли терминал цветной вывод ANSI."""
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stderr.isatty():
        return False
    return True


def render_banner() -> str:
    """Генерирует цветной баннер с пиксельным SVG-логотипом и метаданными."""
    if not _supports_color():
        return f"TG-Rich Converter CLI v{__version__} — Telegram Bot API 10.1+ Rich HTML Converter\n"

    b = _COLOR_BUBBLE
    s = _COLOR_SIGMA
    c = _COLOR_CHECKS
    r = _RESET
    t = _COLOR_TITLE
    w = _COLOR_TEXT
    m = _COLOR_MUTED
    bold = _BOLD

    logo_lines = [
        f"  {b}▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄{r}     {bold}{t}TG-Rich CLI{r} {m}v{__version__}{r} 🚀",
        f"  {b}█{r} {s}█▀▀▀▀▀█{r}{b}     █{r}     {w}Telegram Rich Messages Converter{r}",
        f"  {b}█{r}   {s}▀▀█{r}{b}       █{r}     {m}LaTeX Math • Native Tables • Spoilers • Reasoning{r}",
        f"  {b}█{r} {s}█▄▄▄▄▄█{r}{b}   {c}✓✓{b}█{r}     {m}Bot API 10.1+ Native HTML (up to 32,768 chars){r}",
        f"  {b}▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀{r}     {t}─────────────────────────────────────────────────{r}",
    ]
    return "\n" + "\n".join(logo_lines) + "\n"


def _log_info(message: str) -> None:
    """Выводит информационное сообщение в stderr."""
    if _supports_color():
        sys.stderr.write(f"  {_COLOR_GREEN}✔{_RESET} {message}\n")
    else:
        sys.stderr.write(f"  [OK] {message}\n")


def _log_warn(message: str) -> None:
    """Выводит предупреждение в stderr."""
    if _supports_color():
        sys.stderr.write(f"  {_COLOR_WARN}▲{_RESET} {message}\n")
    else:
        sys.stderr.write(f"  [WARN] {message}\n")


def _log_err(message: str) -> None:
    """Выводит ошибку в stderr."""
    if _supports_color():
        sys.stderr.write(f"  {_COLOR_ERR}✖ Ошибка:{_RESET} {message}\n")
    else:
        sys.stderr.write(f"  [ERROR] {message}\n")


def build_parser() -> argparse.ArgumentParser:
    """Создаёт парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="tg-rich",
        description="Конвертер Markdown / LaTeX от LLM в валидный Telegram Rich HTML (Bot API 10.1+).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        default="-",
        help="Путь к исходному Markdown-файлу (если '-' или не указан, читается из stdin).",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        metavar="FILE",
        help="Путь к выходному файлу (по умолчанию результат выводится в stdout).",
    )

    parser.add_argument(
        "-p",
        "--preview",
        nargs="?",
        const="preview.html",
        default=None,
        metavar="FILE",
        help="Сгенерировать автономный HTML-файл предварительного просмотра с темой Telegram и KaTeX (по умолчанию: preview.html).",
    )

    parser.add_argument(
        "--open",
        action="store_true",
        help="Автоматически открыть созданный HTML-файл превью в браузере по умолчанию.",
    )

    parser.add_argument(
        "-s",
        "--split",
        action="store_true",
        help="Разбить длинный документ на безопасные Telegram-сообщения с сохранением тегов.",
    )

    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=32768,
        metavar="INT",
        help="Максимальная длина сообщения при нарезке (по умолчанию: 32768, для классических сообщений: 4096).",
    )

    parser.add_argument(
        "-t",
        "--thinking-summary",
        type=str,
        default="Размышления",
        metavar="TEXT",
        help="Заголовок для блоков рассуждений <think> (по умолчанию: 'Размышления').",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Тихий режим (отключает вывод логотипа и информационных сообщений в stderr).",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"tg-rich-converter v{__version__}",
        help="Показать версию программы и выйти.",
    )

    return parser


def _read_input(input_source: str) -> str:
    """Читает текст из файла или потока stdin."""
    if input_source == "-" or not input_source:
        if sys.stdin.isatty():
            return ""
        return sys.stdin.read()

    file_path = Path(input_source)
    if not file_path.exists():
        raise FileNotFoundError(f"Файл '{input_source}' не найден.")
    return file_path.read_text(encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    """Точка входа CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Если запущен без аргументов в интерактивном терминале
    if args.input_file == "-" and sys.stdin.isatty() and not args.quiet:
        sys.stderr.write(render_banner())
        parser.print_help(sys.stderr)
        return 0

    # Отображаем логотип в интерактивном режиме
    if not args.quiet and sys.stderr.isatty():
        sys.stderr.write(render_banner())

    try:
        raw_text = _read_input(args.input_file)
    except Exception as e:
        _log_err(str(e))
        return 1

    if not raw_text.strip():
        _log_warn("Получен пустой текст для обработки.")
        return 0

    # Режим 1: Генерация Preview HTML
    if args.preview or args.open:
        preview_target = args.preview if args.preview else "preview.html"
        try:
            out_path = save_preview(
                text=raw_text,
                file_path=preview_target,
                is_markdown=True,
                thinking_summary=args.thinking_summary,
                title=f"Telegram Rich Preview — {Path(args.input_file).name if args.input_file != '-' else 'Document'}",
            )
            if not args.quiet:
                _log_info(f"HTML-превью успешно создано: {out_path.resolve()}")

            if args.open:
                if not args.quiet:
                    _log_info("Открытие страницы превью в браузере...")
                webbrowser.open(out_path.resolve().as_uri())
            return 0
        except Exception as e:
            _log_err(f"Не удалось создать превью: {e}")
            return 1

    # Режим 2: Нарезка на части (Split)
    if args.split:
        try:
            chunks = split_rich_message(
                text=raw_text,
                max_length=args.limit,
                is_markdown=True,
                thinking_summary=args.thinking_summary,
            )

            if not args.quiet:
                _log_info(
                    f"Документ ({len(raw_text)} симв.) успешно разделён на {len(chunks)} сообщ. (лимит: {args.limit} симв.):"
                )
                for idx, chunk in enumerate(chunks, 1):
                    sys.stderr.write(f"    • Часть {idx}: {len(chunk)} симв.\n")

            if args.output:
                out_path = Path(args.output)
                stem = out_path.stem
                suffix = out_path.suffix or ".html"
                parent = out_path.parent

                for idx, chunk in enumerate(chunks, 1):
                    chunk_file = parent / f"{stem}_part{idx}{suffix}" if len(chunks) > 1 else out_path
                    chunk_file.write_text(chunk, encoding="utf-8")
                if not args.quiet:
                    _log_info(f"Сохранено файлов: {len(chunks)}")
            else:
                for idx, chunk in enumerate(chunks, 1):
                    if len(chunks) > 1:
                        sys.stdout.write(f"\n<!-- ====== ЧАСТЬ {idx} / {len(chunks)} ({len(chunk)} симв.) ====== -->\n")
                    sys.stdout.write(chunk + "\n")
            return 0
        except Exception as e:
            _log_err(f"Ошибка при нарезке сообщения: {e}")
            return 1

    # Режим 3: Прямая конвертация в Telegram Rich HTML
    try:
        converted_html = to_rich(raw_text, thinking_summary=args.thinking_summary)

        if args.output:
            out_file = Path(args.output)
            out_file.write_text(converted_html, encoding="utf-8")
            if not args.quiet:
                _log_info(f"Результат сохранён в файл: {out_file.resolve()}")
        else:
            sys.stdout.write(converted_html + "\n")
        return 0
    except Exception as e:
        _log_err(f"Ошибка при конвертации: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())