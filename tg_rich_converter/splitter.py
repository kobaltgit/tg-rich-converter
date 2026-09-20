import re
from typing import List, Optional, Tuple

from .converter import to_rich

_SELF_CLOSING_TAGS = {"hr", "br", "img"}

# Регулярное выражение для безопасной токенизации HTML Telegram
_TOKEN_PATTERN = re.compile(
    r"(?P<math_block><tg-math-block>.*?</tg-math-block>)|"
    r"(?P<math_inline><tg-math>.*?</tg-math>)|"
    r"(?P<comment><!--.*?-->)|"
    r"(?P<tag><[^>]+>)|"
    r"(?P<entity>&[a-zA-Z0-9#]+;)|"
    r"(?P<newlines>\n{2,}|\n)|"
    r"(?P<spaces>[ \t]+)|"
    r"(?P<word>[^\s<>&]+)|"
    r"(?P<char>.)",
    re.DOTALL,
)

_OPEN_TAG_PATTERN = re.compile(r"^<([a-zA-Z0-9_\-]+)(\s+[^>]*)?/?>$", re.DOTALL)
_CLOSE_TAG_PATTERN = re.compile(r"^</([a-zA-Z0-9_\-]+)>$", re.DOTALL)


class _TagTracker:
    """Отслеживает стек открытых HTML-тегов и формирует строки закрытия/открытия."""

    def __init__(self, initial_stack: Optional[List[Tuple[str, str]]] = None):
        # Список кортежей: (tag_name, raw_open_tag)
        self.stack: List[Tuple[str, str]] = list(initial_stack) if initial_stack else []

    def copy(self) -> "_TagTracker":
        return _TagTracker(self.stack)

    def process_token(self, token: str) -> None:
        if not (token.startswith("<") and token.endswith(">")):
            return

        close_match = _CLOSE_TAG_PATTERN.match(token)
        if close_match:
            tag_name = close_match.group(1).lower()
            for idx in range(len(self.stack) - 1, -1, -1):
                if self.stack[idx][0] == tag_name:
                    self.stack.pop(idx)
                    break
            return

        open_match = _OPEN_TAG_PATTERN.match(token)
        if open_match:
            tag_name = open_match.group(1).lower()
            if tag_name in _SELF_CLOSING_TAGS or token.endswith("/>"):
                return
            self.stack.append((tag_name, token))

    def get_closing_string(self) -> str:
        return "".join(f"</{tag_name}>" for tag_name, _ in reversed(self.stack))

    def get_reopen_string(self) -> str:
        return "".join(raw_tag for _, raw_tag in self.stack)

    def is_inside(self, tag_name: str) -> bool:
        return any(t[0] == tag_name for t in self.stack)


def _get_token_priority(token: str) -> int:
    """Определяет приоритет точки разреза после данного токена."""
    if token.startswith("</") and any(
        token.startswith(f"</{tag}>")
        for tag in ("pre", "blockquote", "table", "details", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol")
    ):
        return 10
    if token.startswith("<hr"):
        return 10
    if "\n\n" in token:
        return 9
    if "\n" in token:
        return 7
    if token.isspace():
        return 5
    if token.startswith("</"):
        return 4
    return 1


def split_rich_message(
    text: str,
    max_length: int = 32768,
    is_markdown: bool = False,
    thinking_summary: str = "Размышления",
) -> List[str]:
    """Разбивает сообщение на части, не превышающие max_length, сохраняя валидность HTML.

    Args:
        text: Исходный текст (Markdown или Rich HTML).
        max_length: Максимальная длина одного сообщения (по умолчанию 32768 для Rich сообщений Telegram).
        is_markdown: Если True, предварительно конвертирует текст через to_rich().
        thinking_summary: Заголовок блока рассуждений при конвертации Markdown.

    Returns:
        Список валидных HTML-сообщений.
    """
    if is_markdown:
        text = to_rich(text, thinking_summary=thinking_summary)

    text = text.strip()
    if not text:
        return []

    if len(text) <= max_length:
        return [text]

    tokens: List[str] = [m.group(0) for m in _TOKEN_PATTERN.finditer(text)]
    if not tokens:
        return []

    chunks: List[str] = []
    token_idx = 0
    active_tracker = _TagTracker()

    while token_idx < len(tokens):
        current_tokens: List[str] = []
        current_len = len(active_tracker.get_reopen_string())
        temp_tracker = active_tracker.copy()

        # Кандидаты для разреза: кортеж (индекс_токена_в_current_tokens, снимок_стека, приоритет)
        breakpoints: List[Tuple[int, _TagTracker, int]] = []

        while token_idx < len(tokens):
            tok = tokens[token_idx]
            tok_len = len(tok)

            # Проверяем, как изменится стек тегов
            next_tracker = temp_tracker.copy()
            next_tracker.process_token(tok)
            closing_str = next_tracker.get_closing_string()
            closing_len = len(closing_str)

            # Если добавление токена превышает допустимый лимит
            if current_len + tok_len + closing_len > max_length:
                if not current_tokens:
                    # Случай, когда одиночный токен длиннее max_length (например, длинная ссылка или текст)
                    # Принудительно отрезаем разрешённую длину
                    allowed_len = max(1, max_length - current_len - closing_len)
                    part1 = tok[:allowed_len]
                    part2 = tok[allowed_len:]
                    current_tokens.append(part1)
                    temp_tracker = next_tracker
                    tokens[token_idx] = part2
                break

            current_tokens.append(tok)
            current_len += tok_len
            temp_tracker = next_tracker
            token_idx += 1

            priority = _get_token_priority(tok)
            if priority > 1:
                breakpoints.append((len(current_tokens), temp_tracker.copy(), priority))

        # Выбираем наилучшую точку разреза
        split_at_idx = len(current_tokens)
        split_tracker = temp_tracker

        if token_idx < len(tokens) and breakpoints:
            # Ищем границу с максимальным приоритетом среди последних кандидатов
            best_prio = -1
            best_idx = -1
            best_snap = None

            # Проверяем последние 40% накопленного чанка для красивого разбиения
            cutoff = int(len(current_tokens) * 0.6)
            candidates = [b for b in breakpoints if b[0] >= cutoff] or breakpoints

            for idx_in_curr, snap, prio in candidates:
                if prio >= best_prio:
                    best_prio = prio
                    best_idx = idx_in_curr
                    best_snap = snap

            if best_idx > 0 and best_idx < len(current_tokens):
                # Возвращаем неиспользованные токены обратно в общий поток
                returned_tokens = current_tokens[best_idx:]
                current_tokens = current_tokens[:best_idx]
                token_idx -= len(returned_tokens)
                split_at_idx = best_idx
                split_tracker = best_snap

        # Формируем готовый чанк: восстанавливающий префикс + токены + закрывающий суффикс
        prefix = active_tracker.get_reopen_string()
        body = "".join(current_tokens)

        # Если не внутри блока <pre>, удаляем лишние пробельные символы по краям
        if not active_tracker.is_inside("pre"):
            body = body.lstrip("\r\n")

        suffix = split_tracker.get_closing_string()
        chunk_result = f"{prefix}{body}{suffix}"

        if chunk_result.strip():
            chunks.append(chunk_result)

        # Для следующего чанка активным становится стек на момент разреза
        active_tracker = split_tracker

    return chunks