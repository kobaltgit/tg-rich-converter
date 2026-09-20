from tg_rich_converter import split_rich_message


def test_short_message_not_split():
    text = "<b>Короткое сообщение</b>"
    result = split_rich_message(text, max_length=100)
    assert len(result) == 1
    assert result[0] == text


def test_empty_message():
    assert split_rich_message("") == []
    assert split_rich_message("   \n  ") == []


def test_split_preserves_inline_tags():
    # Длина текста около 90 символов, лимит 50
    text = "<b>Первая часть длинного жирного текста и вторая часть жирного текста</b>"
    chunks = split_rich_message(text, max_length=50)

    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 50

    # Первая часть должна корректно закрыть </b>
    assert chunks[0].startswith("<b>")
    assert chunks[0].endswith("</b>")

    # Вторая часть должна заново открыть <b>
    assert chunks[1].startswith("<b>")
    assert chunks[1].endswith("</b>")


def test_split_nested_code_and_quotes():
    text = (
        '<blockquote><pre><code class="language-python">'
        'x = 1\n'
        'y = 2\n'
        'z = x + y\n'
        'print(f"Сумма: {z}")\n'
        'return z'
        '</code></pre></blockquote>'
    )
    # Задаем небольшой лимит, чтобы гарантировать разделение внутри кода
    chunks = split_rich_message(text, max_length=95)

    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 95

    # Первая часть обязана закрыть все вложенные теги в правильном порядке
    assert chunks[0].endswith("</code></pre></blockquote>")

    # Вторая часть обязана заново открыть теги с сохранением атрибута language-python
    assert chunks[1].startswith('<blockquote><pre><code class="language-python">')
    assert chunks[-1].endswith("</code></pre></blockquote>")


def test_split_formula_atomic():
    formula = "<tg-math>\\int_0^1 x^2 dx = \\frac{1}{3}</tg-math>"
    text = f"Начало текста. {formula} Конец формульного блока текста."

    chunks = split_rich_message(text, max_length=70)
    assert len(chunks) >= 2

    # Формула не должна быть разрезана пополам
    found_formula = False
    for chunk in chunks:
        assert len(chunk) <= 70
        if formula in chunk:
            found_formula = True

    assert found_formula, "Формула LaTeX должна целиком оказаться в одном из чанков"


def test_split_with_markdown_flag():
    md = """# Заголовок 1

Первый длинный абзац текста с **жирным выделением** и формулой $E=mc^2$.

## Заголовок 2

Второй длинный абзац текста с `кодом` и дополнительными пояснениями.
"""
    chunks = split_rich_message(md, max_length=120, is_markdown=True)

    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 120
        # Проверяем, что markdown был сконвертирован в rich HTML
        assert "# Заголовок" not in chunk
        assert ("<h1>" in chunk or "<h2>" in chunk or "<b>" in chunk or "<tg-math>" in chunk)


def test_split_respects_32k_limit():
    # Генерируем большой документ свыше 70 000 символов
    paragraph = (
        "<b>Квантовый блок:</b> суперпозиция состояний $|\\psi\\rangle$ "
        "и оператор эволюции $\\hat{U}(t) = e^{-i\\hat{H}t/\\hbar}$.\n\n"
    )
    long_html = paragraph * 700  # ~77 000 символов

    chunks = split_rich_message(long_html, max_length=32768)

    assert len(chunks) >= 3
    for chunk in chunks:
        assert len(chunk) <= 32768
        # Проверяем баланс тегов в каждом чанке
        assert chunk.count("<b>") == chunk.count("</b>")


def test_split_huge_unbroken_token():
    # Строка без пробелов длиннее лимита
    unbroken = "A" * 250
    text = f"<b>{unbroken}</b>"

    chunks = split_rich_message(text, max_length=100)
    assert len(chunks) >= 3

    for chunk in chunks:
        assert len(chunk) <= 100
        assert chunk.startswith("<b>")
        assert chunk.endswith("</b>")