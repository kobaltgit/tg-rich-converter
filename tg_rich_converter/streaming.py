"""Модуль потоковой обработки и автобалансировки Markdown/LaTeX от LLM (Streaming Mode)."""

import re
from typing import List


class StreamBalancer:
    """Балансировщик потокового вывода LLM для предотвращения ошибок парсинга Telegram."""

    # Маркеры инлайн-форматирования в порядке приоритета проверки
    _INLINE_PAIRS = [
        ("||", "||"),
        ("**", "**"),
        ("__", "__"),
        ("~~", "~~"),
        ("++", "++"),
        ("==", "=="),
        ("*", "*"),
        ("_", "_"),
    ]

    def balance(self, text: str) -> str:
        """Анализирует незавершённый текст и виртуально закрывает все открытые структуры.

        Args:
            text: Сырой промежуточный фрагмент текста от LLM.

        Returns:
            Сбалансированный текст, готовый к валидной конвертации в Telegram Rich HTML.
        """
        if not text:
            return ""

        result = text

        # 1. Проверяем незакрытый тег <think>
        open_thinks = len(re.findall(r"<think\b[^>]*>", result, re.IGNORECASE))
        close_thinks = len(re.findall(r"</think>", result, re.IGNORECASE))
        unclosed_think = open_thinks > close_thinks

        # 2. Проверяем блоки кода (```)
        code_fence_count = len(re.findall(r"```", result))
        if code_fence_count % 2 == 1:
            # Если блок кода открыт, закрываем его
            result += "\n```"
            if unclosed_think:
                result += "</think>"
            return result

        # 3. Проверяем блочные формулы LaTeX ($$)
        # Считаем только те $$, которые не экранированы
        display_math_count = len(re.findall(r"(?<!\\)\$\$", result))
        if display_math_count % 2 == 1:
            result += "\n$$"
            if unclosed_think:
                result += "</think>"
            return result

        # 4. Проверяем инлайн код (одиночные обратные кавычки `)
        # Исключаем тройные бэктики, так как они уже обработаны выше
        clean_text_no_fences = re.sub(r"```.*?```", "", result, flags=re.DOTALL)
        inline_code_count = len(re.findall(r"(?<!`)(`)(?!`)", clean_text_no_fences))
        if inline_code_count % 2 == 1:
            result += "`"
            if unclosed_think:
                result += "</think>"
            return result

        # 5. Проверяем инлайновые формулы LaTeX ($)
        # Убираем уже закрытые $$...$$ формулы для точного подсчета одиночных $
        text_without_display_math = re.sub(r"\$\$.*?\$\$", "", result, flags=re.DOTALL)
        # Находим неэкранированные одиночные знаки доллара
        inline_dollar_matches = re.findall(r"(?<!\\)(?<!\$)\$(?!\$)", text_without_display_math)
        if len(inline_dollar_matches) % 2 == 1:
            result += "$"

        # 6. Проверяем инлайн-стили оформления (жирный, курсив, спойлер, маркер и т.д.)
        result = self._balance_inline_styles(result)

        # 7. Проверяем незавершённые строки таблиц
        lines = result.split("\n")
        if lines and lines[-1].strip().startswith("|") and not lines[-1].strip().endswith("|"):
            lines[-1] = lines[-1].rstrip() + " |"
            result = "\n".join(lines)

        # 8. Закрываем тег <think>, если он оставался открытым
        if unclosed_think:
            result += "</think>"

        return result

    def _balance_inline_styles(self, text: str) -> str:
        """Отслеживает стек открытых инлайн-маркеров и закрывает их в порядке LIFO."""
        # Удаляем из анализа блоки кода и формулы, чтобы их содержимое не влияло на стили
        masked = text
        masked = re.sub(r"```.*?```", "", masked, flags=re.DOTALL)
        masked = re.sub(r"\$\$.*?\$\$", "", masked, flags=re.DOTALL)
        masked = re.sub(r"`[^`\n]+`", "", masked)
        masked = re.sub(r"(?<!\$)\$(?!\$)[^\n\$]+(?<!\$)\$(?!\$)", "", masked)

        stack: List[str] = []
        i = 0
        n = len(masked)

        while i < n:
            matched_pair = False
            # Проверяем двухсимвольные маркеры
            if i + 1 < n:
                two_char = masked[i : i + 2]
                for op, cl in self._INLINE_PAIRS:
                    if len(op) == 2 and two_char == op:
                        if stack and stack[-1] == cl:
                            stack.pop()
                        else:
                            stack.append(cl)
                        i += 2
                        matched_pair = True
                        break

            if matched_pair:
                continue

            # Проверяем односимвольные маркеры (* и _)
            one_char = masked[i]
            for op, cl in self._INLINE_PAIRS:
                if len(op) == 1 and one_char == op:
                    # Защита от snake_case внутри слов для символа '_'
                    if op == "_" and i > 0 and i + 1 < n and masked[i - 1].isalnum() and masked[i + 1].isalnum():
                        pass
                    else:
                        if stack and stack[-1] == cl:
                            stack.pop()
                        else:
                            stack.append(cl)
                    break

            i += 1

        # Закрываем оставшиеся в стеке маркеры в обратном порядке
        if stack:
            closing_suffix = "".join(reversed(stack))
            text += closing_suffix

        return text


def balance_streaming_markdown(text: str) -> str:
    """Вспомогательная функция для быстрой автобалансировки потокового текста."""
    return StreamBalancer().balance(text)