import re
from tg_rich_converter import balance_streaming_markdown, to_rich


def _assert_valid_tags(html_text: str):
    """Вспомогательная проверка сбалансированности базовых HTML-тегов."""
    for tag in ("pre", "code", "details", "summary", "tg-math", "tg-math-block", "b", "i", "s", "u", "mark", "tg-spoiler", "blockquote"):
        open_count = len(re.findall(rf"<{tag}(?:[\s>])", html_text))
        close_count = len(re.findall(rf"</{tag}>", html_text))
        assert open_count == close_count, f"Тег <{tag}> не сбалансирован ({open_count} != {close_count}) в: {html_text}"


def test_stream_unclosed_think():
    partial = "<think>Анализируем условия квантовой задачи"
    balanced = balance_streaming_markdown(partial)
    assert balanced.endswith("</think>")

    html_out = to_rich(partial, streaming=True)
    assert "<details><summary>Размышления</summary>Анализируем условия квантовой задачи</details>" in html_out
    _assert_valid_tags(html_out)


def test_stream_unclosed_code_fence():
    partial = "```python\ndef compute(a, b):\n    return a + b"
    balanced = balance_streaming_markdown(partial)
    assert balanced.endswith("\n```")

    html_out = to_rich(partial, streaming=True)
    assert '<pre><code class="language-python">def compute(a, b):\n    return a + b</code></pre>' in html_out
    _assert_valid_tags(html_out)


def test_stream_unclosed_display_math():
    partial = "Эволюция оператора:\n$$\\hat{H} |\\psi\\rangle = E |\\psi\\rangle"
    balanced = balance_streaming_markdown(partial)
    assert balanced.endswith("$$")

    html_out = to_rich(partial, streaming=True)
    assert "<tg-math-block>\\hat{H} |\\psi\\rangle = E |\\psi\\rangle</tg-math-block>" in html_out
    _assert_valid_tags(html_out)


def test_stream_unclosed_inline_math():
    partial = "Где энергия частицы $E = mc^2"
    balanced = balance_streaming_markdown(partial)
    assert balanced.endswith("$")

    html_out = to_rich(partial, streaming=True)
    assert "<tg-math>E = mc^2</tg-math>" in html_out
    _assert_valid_tags(html_out)


def test_stream_unclosed_inline_styles():
    # Жирный
    assert to_rich("Это **важный текст", streaming=True) == "Это <b>важный текст</b>"
    # Спойлер
    assert to_rich("Ключ доступа: ||0xDEADBEEF", streaming=True) == "Ключ доступа: <tg-spoiler>0xDEADBEEF</tg-spoiler>"
    # Подчёркивание
    assert to_rich("Строго ++унитарный", streaming=True) == "Строго <u>унитарный</u>"
    # Маркер
    assert to_rich("==Внимание", streaming=True) == "<mark>Внимание</mark>"
    # Зачёркнутый
    assert to_rich("~~Устарело", streaming=True) == "<s>Устарело</s>"


def test_stream_nested_inline_styles_lifo():
    partial = "Внимание: **жирный текст и ||скрытый спойлер"
    html_out = to_rich(partial, streaming=True)
    assert html_out == "Внимание: <b>жирный текст и <tg-spoiler>скрытый спойлер</tg-spoiler></b>"
    _assert_valid_tags(html_out)


def test_stream_incremental_token_simulation():
    """Стресс-тест пошагового поступления токенов (эмуляция генерации LLM)."""
    full_markdown = (
        "<think>\n"
        "1. Рассчитаем матрицу Паули: $\\sigma_x = \\begin{pmatrix} 0 & 1 \\\\ 1 & 0 \\end{pmatrix}$.\n"
        "2. Проверим ключ: ||KEY_STREAM_001||.\n"
        "</think>\n\n"
        "# Квантовый анализ\n\n"
        "Формула состояния:\n"
        "$$|\\Psi\\rangle = \\frac{1}{\\sqrt{2}}(|0\\rangle + |1\\rangle)$$\n\n"
        "Используем функцию на `Python`:\n"
        "```python\n"
        "import numpy as np\n"
        "def run():\n"
        "    return True\n"
        "```\n\n"
        "Результат: **успешно** и ++проверено++."
    )

    # Симулируем поступление текста порциями по 3-7 символов
    buffer = ""
    step = 5
    for i in range(0, len(full_markdown), step):
        chunk = full_markdown[i : i + step]
        buffer += chunk

        # Конвертируем промежуточный буфер в потоковом режиме
        rendered_html = to_rich(buffer, streaming=True)

        # Каждый промежуточный кадр обязан быть валидным HTML
        assert rendered_html is not None
        assert "§§TGBLOCK" not in rendered_html
        _assert_valid_tags(rendered_html)

    # Финальная проверка полного текста
    final_html = to_rich(full_markdown, streaming=False)
    _assert_valid_tags(final_html)
    assert "<h1>Квантовый анализ</h1>" in final_html
    assert "<tg-math-block>" in final_html
    assert '<pre><code class="language-python">' in final_html