import html
import re
from typing import Dict, List


class TelegramRichConverter:
    """Конвертер Markdown / LaTeX от LLM в валидный Telegram Rich HTML (Bot API 10.1+)."""

    def __init__(self):
        self._placeholders: Dict[str, str] = {}
        self._placeholder_idx = 0

    def _save_block(self, content: str) -> str:
        key = f"§§TGBLOCK{self._placeholder_idx}§§"
        self._placeholder_idx += 1
        self._placeholders[key] = content
        return key

    def _format_inline(self, text: str) -> str:
        """Обработка инлайнового форматирования (формулы, код, спойлеры, стили)."""
        # 1. Инлайновые формулы: $x$ или \(x\)
        def replace_inline_math(match: re.Match) -> str:
            formula = html.escape(match.group(1).strip(), quote=False)
            return self._save_block(f"<tg-math>{formula}</tg-math>")

        text = re.sub(
            r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", replace_inline_math, text
        )
        text = re.sub(r"\\\((.*?)\\\)", replace_inline_math, text)

        # 2. Инлайн код: `code`
        def replace_inline_code(match: re.Match) -> str:
            escaped = html.escape(match.group(1), quote=False)
            return self._save_block(f"<code>{escaped}</code>")

        text = re.sub(r"`([^`\n]+)`", replace_inline_code, text)

        # 3. Спойлеры: ||text||
        text = re.sub(r"\|\|(.+?)\|\|", r"<tg-spoiler>\1</tg-spoiler>", text)

        # 4. Ссылки: [текст](url)
        text = re.sub(
            r"\[(.*?)\]\((https?://[^\s\)]+)\)",
            r'<a href="\2">\1</a>',
            text,
        )

        # 5. Жирный: **text** или __text__
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)

        # 6. Курсив: *text* или _text_ (не затрагивая snake_case внутри слов)
        text = re.sub(r"(?<!\*)\*(?!\*)([^\*\n]+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
        text = re.sub(r"(?<!\w)_(?!_)([^_\n]+?)(?<!_)_(?!\w)", r"<i>\1</i>", text)

        # 7. Зачеркнутый: ~~text~~
        text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)

        return text

    def convert(self, text: str) -> str:
        self._placeholders.clear()
        self._placeholder_idx = 0

        # Нормализация переносов строк
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 1. Защищаем блоки кода от случайного парсинга
        def replace_code_block(match: re.Match) -> str:
            lang = match.group(1) or ""
            code_content = html.escape(match.group(2).strip("\n"), quote=False)
            if lang:
                rendered = f'<pre><code class="language-{html.escape(lang)}">{code_content}</code></pre>'
            else:
                rendered = f"<pre><code>{code_content}</code></pre>"
            return self._save_block(rendered)

        text = re.sub(
            r"```([a-zA-Z0-9_\-\+]*)\n(.*?)```",
            replace_code_block,
            text,
            flags=re.DOTALL,
        )

        # 2. Обрабатываем reasoning-теги моделей (<think>...</think>)
        def replace_think(match: re.Match) -> str:
            thought = match.group(1).strip()
            sub_converted = TelegramRichConverter().convert(thought)
            rendered = f"<details><summary>Размышления</summary>{sub_converted}</details>"
            return self._save_block(rendered)

        text = re.sub(
            r"<think>(.*?)</think>", replace_think, text, flags=re.DOTALL | re.IGNORECASE
        )

        # 3. Блочные формулы LaTeX: $$...$$ или \[...\]
        def replace_math_block(match: re.Match) -> str:
            formula = html.escape(match.group(1).strip(), quote=False)
            return self._save_block(f"<tg-math-block>{formula}</tg-math-block>")

        text = re.sub(r"\$\$(.*?)\$\$", replace_math_block, text, flags=re.DOTALL)
        text = re.sub(r"\\\[(.*?)\\\]", replace_math_block, text, flags=re.DOTALL)

        # 4. Markdown Таблицы (| ... |)
        text = self._parse_tables(text)

        # 5. Заголовки (H1-H6)
        def replace_headings(match: re.Match) -> str:
            level = min(len(match.group(1)), 6)
            heading_text = match.group(2).strip()
            return f"<h{level}>{heading_text}</h{level}>"

        text = re.sub(r"^(#{1,6})\s+(.+)$", replace_headings, text, flags=re.MULTILINE)

        # 6. Цитаты (> text)
        def replace_quotes(match: re.Match) -> str:
            quote_lines = [
                line.lstrip(">").strip() for line in match.group(0).split("\n")
            ]
            content = "<br/>".join(quote_lines)
            return f"<blockquote>{content}</blockquote>"

        text = re.sub(r"^(?:>.*(?:\n|$))+", replace_quotes, text, flags=re.MULTILINE)

        # 7. Инлайновые стили, формулы, спойлеры
        text = self._format_inline(text)

        # 8. Восстанавливаем сохраненные блоки (с поддержкой вложенности)
        while "§§TGBLOCK" in text:
            prev_text = text
            for key, value in self._placeholders.items():
                text = text.replace(key, value)
            if text == prev_text:
                break

        return text.strip()

    def _parse_tables(self, text: str) -> str:
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

                rendered_table = self._render_table(table_lines)
                new_lines.append(self._save_block(rendered_table))
            else:
                new_lines.append(line)
                i += 1

        return "\n".join(new_lines)

    def _render_table(self, lines: List[str]) -> str:
        header_raw = [
            col.strip() for col in lines[0].strip().strip("|").split("|")
        ]
        aligns_raw = [
            col.strip() for col in lines[1].strip().strip("|").split("|")
        ]
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

        # Заголовок таблицы с поддержкой инлайн-форматирования
        html_out.append("  <thead><tr>")
        for idx, col in enumerate(header_raw):
            align = alignments[idx] if idx < len(alignments) else ""
            cell_content = self._format_inline(col)
            html_out.append(f"    <th{align}>{cell_content}</th>")
        html_out.append("  </tr></thead>")

        # Тело таблицы с поддержкой инлайн-форматирования
        html_out.append("  <tbody>")
        for row_str in lines[2:]:
            cells = [c.strip() for c in row_str.strip().strip("|").split("|")]
            html_out.append("    <tr>")
            for idx, c in enumerate(cells):
                align = alignments[idx] if idx < len(alignments) else ""
                cell_content = self._format_inline(c)
                html_out.append(f"      <td{align}>{cell_content}</td>")
            html_out.append("    </tr>")
        html_out.append("  </tbody>")
        html_out.append("</table>")

        return "\n".join(html_out)


def to_rich(text: str) -> str:
    """Конвертирует сырой Markdown/LaTeX/таблицы в Telegram Rich HTML."""
    return TelegramRichConverter().convert(text)


markdown_to_rich = to_rich