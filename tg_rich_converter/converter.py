import html
import re
from typing import Dict, List

from .streaming import balance_streaming_markdown


class _ConversionContext:
    """Изолированный контекст одной операции конвертации для потокобезопасности."""

    def __init__(self, thinking_summary: str = "Размышления"):
        self.placeholders: Dict[str, str] = {}
        self.placeholder_idx: int = 0
        self.thinking_summary: str = thinking_summary

    def save(self, content: str) -> str:
        key = f"§§TGBLOCK{self.placeholder_idx}§§"
        self.placeholder_idx += 1
        self.placeholders[key] = content
        return key


class TelegramRichConverter:
    """Конвертер Markdown / LaTeX от LLM в валидный Telegram Rich HTML (Bot API 10.1+)."""

    def _format_inline(self, text: str, ctx: _ConversionContext) -> str:
        """Безопасная обработка инлайнового форматирования текста."""
        # 1. Сначала безопасно экранируем все сырые HTML-символы в тексте
        text = html.escape(text, quote=False)

        # 2. Спойлеры: ||text||
        text = re.sub(r"\|\|(.+?)\|\|", r"<tg-spoiler>\1</tg-spoiler>", text)

        # 3. Ссылки: [текст](url)
        text = re.sub(
            r"\[(.*?)\]\((https?://[^\s\)]+)\)",
            r'<a href="\2">\1</a>',
            text,
        )

        # 4. Подчёркивание: ++text++
        text = re.sub(r"\+\+(.+?)\+\+", r"<u>\1</u>", text)

        # 5. Выделение (маркер): ==text==
        text = re.sub(r"==(.+?)==", r"<mark>\1</mark>", text)

        # 6. Жирный шрифт: **text** или __text__
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)

        # 7. Зачёркнутый шрифт: ~~text~~
        text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)

        # 8. Курсив: *text* или _text_ (с защитой от snake_case внутри слов)
        text = re.sub(r"(?<!\*)\*(?!\*)([^\*\n]+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
        text = re.sub(r"(?<!\w)_(?!_)([^_\n]+?)(?<!_)_(?!\w)", r"<i>\1</i>", text)

        return text

    def convert(
        self,
        text: str,
        thinking_summary: str = "Размышления",
        streaming: bool = False,
    ) -> str:
        """Конвертирует исходный текст в Telegram Rich HTML.

        Args:
            text: Исходный Markdown/LaTeX текст.
            thinking_summary: Заголовок блока рассуждений <think>.
            streaming: Включить автобалансировку незавершённых конструкций (потоковый режим).
        """
        if streaming:
            text = balance_streaming_markdown(text)

        ctx = _ConversionContext(thinking_summary=thinking_summary)

        # Нормализация переносов строк
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 1. Защищаем блоки кода (```lang\n...```)
        def replace_code_block(match: re.Match) -> str:
            lang = match.group(1) or ""
            code_content = html.escape(match.group(2).strip("\n"), quote=False)
            if lang:
                rendered = f'<pre><code class="language-{html.escape(lang)}">{code_content}</code></pre>'
            else:
                rendered = f"<pre><code>{code_content}</code></pre>"
            return ctx.save(rendered)

        text = re.sub(
            r"```([a-zA-Z0-9_\-\+]*)\n(.*?)```",
            replace_code_block,
            text,
            flags=re.DOTALL,
        )

        # 2. Обрабатываем reasoning-теги моделей (<think>...</think>)
        def replace_think(match: re.Match) -> str:
            thought = match.group(1).strip()
            sub_converted = self.convert(
                thought,
                thinking_summary=ctx.thinking_summary,
                streaming=False,
            )
            rendered = f"<details><summary>{html.escape(ctx.thinking_summary)}</summary>{sub_converted}</details>"
            return ctx.save(rendered)

        text = re.sub(
            r"<think>(.*?)</think>", replace_think, text, flags=re.DOTALL | re.IGNORECASE
        )

        # 3. Блочные формулы LaTeX: $$...$$ или \[...\]
        def replace_math_block(match: re.Match) -> str:
            formula = html.escape(match.group(1).strip(), quote=False)
            return ctx.save(f"<tg-math-block>{formula}</tg-math-block>")

        text = re.sub(r"\$\$(.*?)\$\$", replace_math_block, text, flags=re.DOTALL)
        text = re.sub(r"\\\[(.*?)\\\]", replace_math_block, text, flags=re.DOTALL)

        # 4. Инлайновые формулы LaTeX: $...$ или \(...\)
        # Скрываем их до таблиц, чтобы бра-кет и модули ($|\psi\rangle$) не ломали пайпы таблицы
        def replace_inline_math(match: re.Match) -> str:
            formula = html.escape(match.group(1).strip(), quote=False)
            return ctx.save(f"<tg-math>{formula}</tg-math>")

        text = re.sub(
            r"(?<!\$)\$(?!\$)([^\n\$]+?)(?<!\$)\$(?!\$)", replace_inline_math, text
        )
        text = re.sub(r"\\\((.*?)\\\)", replace_inline_math, text)

        # 5. Инлайн код: `code` (также скрываем до таблиц)
        def replace_inline_code(match: re.Match) -> str:
            escaped = html.escape(match.group(1), quote=False)
            return ctx.save(f"<code>{escaped}</code>")

        text = re.sub(r"`([^`\n]+)`", replace_inline_code, text)

        # 6. Markdown Таблицы (| ... |)
        text = self._parse_tables(text, ctx)

        # 7. Списки (маркированные и нумерованные)
        text = self._parse_lists(text, ctx)

        # 8. Заголовки (H1-H6)
        def replace_headings(match: re.Match) -> str:
            level = min(len(match.group(1)), 6)
            heading_text = self._format_inline(match.group(2).strip(), ctx)
            return ctx.save(f"<h{level}>{heading_text}</h{level}>")

        text = re.sub(r"^(#{1,6})\s+(.+)$", replace_headings, text, flags=re.MULTILINE)

        # 9. Горизонтальные разделители (---, ***, ___)
        text = re.sub(r"^(?:[-*_]\s*){3,}$", lambda _: ctx.save("<hr/>"), text, flags=re.MULTILINE)

        # 10. Цитаты (> text)
        def replace_quotes(match: re.Match) -> str:
            quote_lines = [
                self._format_inline(line.lstrip(">").strip(), ctx)
                for line in match.group(0).split("\n")
                if line.strip()
            ]
            content = "\n".join(quote_lines)
            return ctx.save(f"<blockquote>{content}</blockquote>")

        text = re.sub(r"^(?:>.*(?:\n|$))+", replace_quotes, text, flags=re.MULTILINE)

        # 11. Форматируем оставшийся обычный текст
        text = self._format_inline(text, ctx)

        # 12. Восстанавливаем сохраненные блоки из плейсхолдеров
        while "§§TGBLOCK" in text:
            prev_text = text
            for key, value in ctx.placeholders.items():
                text = text.replace(key, value)
            if text == prev_text:
                break

        return text.strip()

    def _parse_lists(self, text: str, ctx: _ConversionContext) -> str:
        """Преобразование маркированных и нумерованных списков в нативные <ul> и <ol>."""
        lines = text.split("\n")
        new_lines: List[str] = []
        i = 0

        while i < len(lines):
            line = lines[i]
            ul_match = re.match(r"^\s*[\*\-\+]\s+(.+)$", line)
            ol_match = re.match(r"^\s*\d+\.\s+(.+)$", line)

            if ul_match:
                list_items = [ul_match.group(1)]
                i += 1
                while i < len(lines):
                    next_item = re.match(r"^\s*[\*\-\+]\s+(.+)$", lines[i])
                    if next_item:
                        list_items.append(next_item.group(1))
                        i += 1
                    else:
                        break
                rendered_items = [
                    f"  <li>{self._format_inline(item, ctx)}</li>"
                    for item in list_items
                ]
                html_list = "<ul>\n" + "\n".join(rendered_items) + "\n</ul>"
                new_lines.append(ctx.save(html_list))

            elif ol_match:
                list_items = [ol_match.group(1)]
                i += 1
                while i < len(lines):
                    next_item = re.match(r"^\s*\d+\.\s+(.+)$", lines[i])
                    if next_item:
                        list_items.append(next_item.group(1))
                        i += 1
                    else:
                        break
                rendered_items = [
                    f"  <li>{self._format_inline(item, ctx)}</li>"
                    for item in list_items
                ]
                html_list = "<ol>\n" + "\n".join(rendered_items) + "\n</ol>"
                new_lines.append(ctx.save(html_list))

            else:
                new_lines.append(line)
                i += 1

        return "\n".join(new_lines)

    def _split_table_row(self, row: str) -> List[str]:
        """Разбивает строку таблицы по '|', поддерживая экранированные пайпы '\\|'."""
        escaped_pipe_placeholder = "§§ESCAPED_PIPE§§"
        safe_row = row.replace(r"\|", escaped_pipe_placeholder).strip().strip("|")
        cells = [c.replace(escaped_pipe_placeholder, "|").strip() for c in safe_row.split("|")]
        return cells

    def _parse_tables(self, text: str, ctx: _ConversionContext) -> str:
        """Поиск и преобразование Markdown pipe-таблиц в Telegram <table bordered striped>."""
        lines = text.split("\n")
        new_lines: List[str] = []
        i = 0

        while i < len(lines):
            line = lines[i]
            if (
                "|" in line
                and i + 1 < len(lines)
                and re.match(r"^[\s\|:\-]+$", lines[i + 1])
                and "-" in lines[i + 1]
            ):
                table_lines = [line, lines[i + 1]]
                i += 2
                while i < len(lines) and "|" in lines[i] and lines[i].strip():
                    table_lines.append(lines[i])
                    i += 1

                rendered_table = self._render_table(table_lines, ctx)
                new_lines.append(ctx.save(rendered_table))
            else:
                new_lines.append(line)
                i += 1

        return "\n".join(new_lines)

    def _render_table(self, lines: List[str], ctx: _ConversionContext) -> str:
        header_raw = self._split_table_row(lines[0])
        aligns_raw = self._split_table_row(lines[1])

        alignments = []
        for a in aligns_raw:
            if a.startswith(":") and a.endswith(":"):
                alignments.append(' align="center"')
            elif a.endswith(":"):
                alignments.append(' align="right"')
            elif a.startswith(":"):
                alignments.append(' align="left"')
            else:
                alignments.append("")

        html_out = ['<table bordered="true" striped="true">']

        # Заголовок таблицы
        html_out.append("  <thead><tr>")
        for idx, col in enumerate(header_raw):
            align = alignments[idx] if idx < len(alignments) else ""
            cell_content = self._format_inline(col, ctx)
            html_out.append(f"    <th{align}>{cell_content}</th>")
        html_out.append("  </tr></thead>")

        # Тело таблицы
        html_out.append("  <tbody>")
        for row_str in lines[2:]:
            cells = self._split_table_row(row_str)
            html_out.append("    <tr>")
            for idx, c in enumerate(cells):
                align = alignments[idx] if idx < len(alignments) else ""
                cell_content = self._format_inline(c, ctx)
                html_out.append(f"      <td{align}>{cell_content}</td>")
            html_out.append("    </tr>")
        html_out.append("  </tbody>")
        html_out.append("</table>")

        return "\n".join(html_out)


def to_rich(
    text: str,
    thinking_summary: str = "Размышления",
    streaming: bool = False,
) -> str:
    """Конвертирует сырой Markdown/LaTeX/таблицы в Telegram Rich HTML.

    Args:
        text: Исходный Markdown-текст от нейросети.
        thinking_summary: Заголовок для блоков рассуждений <think>.
        streaming: Флаг потокового режима (автозакрытие незавершённых конструкций).
    """
    return TelegramRichConverter().convert(
        text,
        thinking_summary=thinking_summary,
        streaming=streaming,
    )


markdown_to_rich = to_rich