"""CLI-интерфейс библиотеки tg-rich-converter с поддержкой локализации (RU / EN)."""

import argparse
import locale
import os
import sys
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional

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

_I18N: Dict[str, Dict[str, str]] = {
    "ru": {
        "desc": "Конвертер Markdown / LaTeX от LLM в валидный Telegram Rich HTML (Bot API 10.1+).",
        "help_option": "показать эту справку и выйти.",
        "input_help": "Путь к Markdown-файлу (если '-' или не указан, читается из stdin).",
        "output_help": "Путь к выходному файлу (по умолчанию вывод в stdout).",
        "preview_help": "Сгенерировать HTML-превью с темой Telegram и KaTeX (по умолчанию: preview.html).",
        "open_help": "Автоматически открыть созданный HTML-файл превью в браузере по умолчанию.",
        "split_help": "Разбить документ на безопасные сообщения Telegram с сохранением тегов.",
        "limit_help": "Максимальный размер сообщения при нарезке (по умолчанию: 32768, для обычных: 4096).",
        "thinking_help": "Заголовок для блоков рассуждений <think> (по умолчанию: 'Размышления').",
        "lang_help": "Язык интерфейса и сообщений (ru или en).",
        "quiet_help": "Тихий режим (отключает логотип и информационные логи в stderr).",
        "version_help": "Показать версию программы и выйти.",
        "banner_subtitle": "Конвертер сообщений для Telegram Rich HTML",
        "banner_features": "LaTeX Формулы • Таблицы • Спойлеры • Рассуждения",
        "banner_limits": "Поддержка Bot API 10.1+ (до 32 768 символов)",
        "banner_plain": f"TG-Rich Converter CLI v{__version__} — Конвертер Telegram Rich HTML (Bot API 10.1+)\n",
        "preview_created": "HTML-превью успешно создано:",
        "preview_opening": "Открытие страницы превью в браузере...",
        "preview_title_doc": "Документ",
        "split_info": "Документ ({total_len} симв.) успешно разделён на {count} сообщ. (лимит: {limit} симв.):",
        "split_part": "Часть",
        "split_saved": "Сохранено файлов:",
        "output_saved": "Результат сохранён в файл:",
        "empty_input": "Получен пустой текст для обработки.",
        "err_file_not_found": "Файл '{source}' не найден.",
        "err_preview": "Не удалось создать превью:",
        "err_split": "Ошибка при нарезке сообщения:",
        "err_convert": "Ошибка при конвертации:",
        "default_thinking": "Размышления",
    },
    "en": {
        "desc": "Convert LLM Markdown & LaTeX into native Telegram Bot API 10.1+ Rich HTML.",
        "help_option": "show this help message and exit.",
        "input_help": "Path to input Markdown file (if '-' or omitted, reads from stdin).",
        "output_help": "Path to output file (default writes to stdout).",
        "preview_help": "Generate standalone preview HTML with KaTeX & Telegram Dark theme (default: preview.html).",
        "open_help": "Automatically open generated preview in default web browser.",
        "split_help": "Split oversized document into Telegram-safe messages preserving tags.",
        "limit_help": "Maximum message length when splitting (default: 32768, for standard: 4096).",
        "thinking_help": "Summary title for <think> reasoning blocks (default: 'Reasoning').",
        "lang_help": "Interface language (ru or en).",
        "quiet_help": "Quiet mode (suppresses banner and info messages in stderr).",
        "version_help": "Show program version and exit.",
        "banner_subtitle": "Telegram Rich Messages Converter",
        "banner_features": "LaTeX Math • Native Tables • Spoilers • Reasoning",
        "banner_limits": "Bot API 10.1+ Native HTML (up to 32,768 chars)",
        "banner_plain": f"TG-Rich Converter CLI v{__version__} — Telegram Bot API 10.1+ Rich HTML Converter\n",
        "preview_created": "HTML preview successfully generated:",
        "preview_opening": "Opening preview in browser...",
        "preview_title_doc": "Document",
        "split_info": "Document ({total_len} chars) successfully split into {count} chunks (limit: {limit} chars):",
        "split_part": "Part",
        "split_saved": "Files saved:",
        "output_saved": "Result saved to file:",
        "empty_input": "Received empty text for processing.",
        "err_file_not_found": "File '{source}' not found.",
        "err_preview": "Failed to create preview:",
        "err_split": "Error splitting message:",
        "err_convert": "Error during conversion:",
        "default_thinking": "Reasoning",
    },
}


def _detect_language() -> str:
    """Определяет язык системы (по умолчанию 'ru' для русскоязычных локалей, иначе 'en')."""
    for env_var in ("TG_RICH_LANG", "LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        val = os.environ.get(env_var, "").lower()
        if val.startswith("ru"):
            return "ru"
        if val.startswith("en"):
            return "en"

    try:
        loc = locale.getdefaultlocale()[0]
        if loc and loc.lower().startswith("ru"):
            return "ru"
    except Exception:
        pass

    return "en"


def _extract_lang(argv: Optional[List[str]] = None) -> str:
    """Извлекает язык из аргументов командной строки до основного парсинга argparse."""
    args_list = sys.argv[1:] if argv is None else list(argv)
    for idx, arg in enumerate(args_list):
        if arg == "--lang" and idx + 1 < len(args_list):
            val = args_list[idx + 1].lower()
            if val in ("ru", "en"):
                return val
        elif arg.startswith("--lang="):
            val = arg.split("=", 1)[1].lower()
            if val in ("ru", "en"):
                return val
    return _detect_language()


def _supports_color() -> bool:
    """Проверяет, поддерживает ли терминал цветной вывод ANSI."""
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stderr.isatty():
        return False
    return True


def render_banner(lang: str = "en") -> str:
    """Генерирует цветной баннер с пиксельным SVG-логотипом и метаданными."""
    i18n = _I18N.get(lang, _I18N["en"])
    if not _supports_color():
        return i18n["banner_plain"]

    b = _COLOR_BUBBLE
    s = _COLOR_SIGMA
    c = _COLOR_CHECKS
    r = _RESET
    t = _COLOR_TITLE
    w = _COLOR_TEXT
    m = _COLOR_MUTED
    bold = _BOLD

    subtitle = i18n["banner_subtitle"]
    features = i18n["banner_features"]
    limits = i18n["banner_limits"]

    logo_lines = [
        f"  {b}▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄{r}     {bold}{t}TG-Rich CLI{r} {m}v{__version__}{r} 🚀",
        f"  {b}█{r} {s}█▀▀▀▀▀█{r}{b}     █{r}     {w}{subtitle}{r}",
        f"  {b}█{r}   {s}▀▀█{r}{b}       █{r}     {m}{features}{r}",
        f"  {b}█{r} {s}█▄▄▄▄▄█{r}{b}   {c}✓✓{b}█{r}     {m}{limits}{r}",
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


def _log_err(message: str, lang: str = "en") -> None:
    """Выводит ошибку в stderr."""
    prefix = "✖ Ошибка:" if lang == "ru" else "✖ Error:"
    if _supports_color():
        sys.stderr.write(f"  {_COLOR_ERR}{prefix}{_RESET} {message}\n")
    else:
        sys.stderr.write(f"  [ERROR] {message}\n")


def build_parser(lang: str = "en") -> argparse.ArgumentParser:
    """Создаёт парсер аргументов командной строки для указанного языка."""
    i18n = _I18N.get(lang, _I18N["en"])

    parser = argparse.ArgumentParser(
        prog="tg-rich",
        description=i18n["desc"],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )

    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help=i18n["help_option"],
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        default="-",
        help=i18n["input_help"],
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        metavar="FILE",
        help=i18n["output_help"],
    )

    parser.add_argument(
        "-p",
        "--preview",
        nargs="?",
        const="preview.html",
        default=None,
        metavar="FILE",
        help=i18n["preview_help"],
    )

    parser.add_argument(
        "--open",
        action="store_true",
        help=i18n["open_help"],
    )

    parser.add_argument(
        "-s",
        "--split",
        action="store_true",
        help=i18n["split_help"],
    )

    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=32768,
        metavar="INT",
        help=i18n["limit_help"],
    )

    parser.add_argument(
        "-t",
        "--thinking-summary",
        type=str,
        default=None,
        metavar="TEXT",
        help=i18n["thinking_help"],
    )

    parser.add_argument(
        "--lang",
        type=str,
        choices=["ru", "en"],
        default=None,
        help=i18n["lang_help"],
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help=i18n["quiet_help"],
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"tg-rich-converter v{__version__}",
        help=i18n["version_help"],
    )

    return parser


def _read_input(input_source: str, lang: str = "en") -> str:
    """Читает текст из файла или потока stdin."""
    i18n = _I18N.get(lang, _I18N["en"])
    if input_source == "-" or not input_source:
        if sys.stdin.isatty():
            return ""
        return sys.stdin.read()

    file_path = Path(input_source)
    if not file_path.exists():
        raise FileNotFoundError(i18n["err_file_not_found"].format(source=input_source))
    return file_path.read_text(encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    """Точка входа CLI."""
    chosen_lang = _extract_lang(argv)
    i18n = _I18N.get(chosen_lang, _I18N["en"])

    parser = build_parser(lang=chosen_lang)
    args = parser.parse_args(argv)

    # Если язык был явно указан через аргументы
    if args.lang and args.lang in ("ru", "en"):
        chosen_lang = args.lang
        i18n = _I18N[chosen_lang]

    # Заголовок рассуждений по умолчанию
    thinking_summary = args.thinking_summary if args.thinking_summary is not None else i18n["default_thinking"]

    # Если запущен без аргументов в интерактивном терминале
    if args.input_file == "-" and sys.stdin.isatty() and not args.quiet:
        sys.stderr.write(render_banner(lang=chosen_lang))
        parser.print_help(sys.stderr)
        return 0

    # Отображаем логотип в интерактивном режиме
    if not args.quiet and sys.stderr.isatty():
        sys.stderr.write(render_banner(lang=chosen_lang))

    try:
        raw_text = _read_input(args.input_file, lang=chosen_lang)
    except Exception as e:
        _log_err(str(e), lang=chosen_lang)
        return 1

    if not raw_text.strip():
        _log_warn(i18n["empty_input"])
        return 0

    # Режим 1: Генерация Preview HTML
    if args.preview or args.open:
        preview_target = args.preview if args.preview else "preview.html"
        try:
            doc_name = Path(args.input_file).name if args.input_file != "-" else i18n["preview_title_doc"]
            out_path = save_preview(
                text=raw_text,
                file_path=preview_target,
                is_markdown=True,
                thinking_summary=thinking_summary,
                title=f"Telegram Rich Preview — {doc_name}",
            )
            if not args.quiet:
                _log_info(f"{i18n['preview_created']} {out_path.resolve()}")

            if args.open:
                if not args.quiet:
                    _log_info(i18n["preview_opening"])
                webbrowser.open(out_path.resolve().as_uri())
            return 0
        except Exception as e:
            _log_err(f"{i18n['err_preview']} {e}", lang=chosen_lang)
            return 1

    # Режим 2: Нарезка на части (Split)
    if args.split:
        try:
            chunks = split_rich_message(
                text=raw_text,
                max_length=args.limit,
                is_markdown=True,
                thinking_summary=thinking_summary,
            )

            if not args.quiet:
                info_msg = i18n["split_info"].format(
                    total_len=len(raw_text),
                    count=len(chunks),
                    limit=args.limit,
                )
                _log_info(info_msg)
                for idx, chunk in enumerate(chunks, 1):
                    sys.stderr.write(f"    • {i18n['split_part']} {idx}: {len(chunk)} chars.\n")

            if args.output:
                out_path = Path(args.output)
                stem = out_path.stem
                suffix = out_path.suffix or ".html"
                parent = out_path.parent

                for idx, chunk in enumerate(chunks, 1):
                    chunk_file = parent / f"{stem}_part{idx}{suffix}" if len(chunks) > 1 else out_path
                    chunk_file.write_text(chunk, encoding="utf-8")
                if not args.quiet:
                    _log_info(f"{i18n['split_saved']} {len(chunks)}")
            else:
                for idx, chunk in enumerate(chunks, 1):
                    if len(chunks) > 1:
                        sys.stdout.write(
                            f"\n<!-- ====== {i18n['split_part'].upper()} {idx} / {len(chunks)} ({len(chunk)} chars) ====== -->\n"
                        )
                    sys.stdout.write(chunk + "\n")
            return 0
        except Exception as e:
            _log_err(f"{i18n['err_split']} {e}", lang=chosen_lang)
            return 1

    # Режим 3: Прямая конвертация в Telegram Rich HTML
    try:
        converted_html = to_rich(raw_text, thinking_summary=thinking_summary)

        if args.output:
            out_file = Path(args.output)
            out_file.write_text(converted_html, encoding="utf-8")
            if not args.quiet:
                _log_info(f"{i18n['output_saved']} {out_file.resolve()}")
        else:
            sys.stdout.write(converted_html + "\n")
        return 0
    except Exception as e:
        _log_err(f"{i18n['err_convert']} {e}", lang=chosen_lang)
        return 1


if __name__ == "__main__":
    sys.exit(main())