from pathlib import Path

from tg_rich_converter import (
    markdown_to_rich,
    render_html_preview,
    save_preview,
    to_rich,
)


def test_table_with_inline_math():
    md = """
| Алгоритм | Временная сложность |
|:---------|--------------------:|
| Поиск    | $O(N)$              |
| Гровер   | $O(\\sqrt{N})$      |
"""
    result = to_rich(md)
    assert '<table bordered="true" striped="true">' in result
    assert '<th align="left">Алгоритм</th>' in result
    assert '<td align="right"><tg-math>O(N)</tg-math></td>' in result
    assert '<td align="right"><tg-math>O(\\sqrt{N})</tg-math></td>' in result


def test_table_with_bra_ket_and_escaped_pipe():
    md = """
| Состояние | Формула | Описание |
|:---|:---:|---:|
| Вектор | $|\\psi\\rangle$ | Квантовое состояние |
| Модуль | $|x| \\ge 0$ | Значение A \\| B |
"""
    result = to_rich(md)
    assert '<table bordered="true" striped="true">' in result
    assert '<td align="center"><tg-math>|\\psi\\rangle</tg-math></td>' in result
    assert '<td align="center"><tg-math>|x| \\ge 0</tg-math></td>' in result
    assert '<td align="right">Значение A | B</td>' in result


def test_latex_formulas():
    md = "Энергия: $$E = mc^2$$, скорость $c$ константа."
    result = to_rich(md)
    assert "<tg-math-block>E = mc^2</tg-math-block>" in result
    assert "<tg-math>c</tg-math>" in result


def test_html_escaping_raw_text():
    md = "Условие: если x < 5 и y > 10, то выполнить a & b."
    result = to_rich(md)
    assert "x &lt; 5" in result
    assert "y &gt; 10" in result
    assert "a &amp; b" in result


def test_thinking_block():
    md = "<think>Подумаем над планом решения...</think>\nРезультат готов."
    result = to_rich(md)
    assert "<details><summary>Размышления</summary>" in result
    assert "Результат готов." in result


def test_custom_thinking_summary():
    md = "<think>Deep reasoning process...</think>\nFinished."
    result = to_rich(md, thinking_summary="Reasoning")
    assert "<details><summary>Reasoning</summary>" in result


def test_code_blocks():
    md = "```python\nprint('tg-rich-converter')\n```"
    result = to_rich(md)
    assert '<pre><code class="language-python">print(\'tg-rich-converter\')</code></pre>' in result


def test_lists_not_breaking_italics():
    md = """
* Первый пункт
* Второй пункт
* Третий пункт
"""
    result = to_rich(md)
    assert "<ul>" in result
    assert "<li>Первый пункт</li>" in result
    assert "<li>Второй пункт</li>" in result
    assert "<i>" not in result


def test_underline_and_mark():
    md = "Текст ++подчеркнут++ и ==выделен маркером==."
    result = to_rich(md)
    assert "<u>подчеркнут</u>" in result
    assert "<mark>выделен маркером</mark>" in result


def test_spoiler_with_snake_case():
    md = "Секретный ключ: ||SUPER_SECRET_KEY_42||"
    result = to_rich(md)
    assert "<tg-spoiler>SUPER_SECRET_KEY_42</tg-spoiler>" in result
    assert "<i>" not in result


def test_alias_works():
    assert to_rich("**test**") == markdown_to_rich("**test**")


def test_render_html_preview_markdown():
    md = "# Заголовок\n\nТекст с формулой $E=mc^2$ и спойлером ||секрет||."
    html_page = render_html_preview(md, title="Тест Превью")

    assert "<!DOCTYPE html>" in html_page
    assert "<title>Тест Превью</title>" in html_page
    assert "katex.min.js" in html_page
    assert "tg-message-bubble" in html_page
    assert "<h1>Заголовок</h1>" in html_page
    assert "<tg-math>E=mc^2</tg-math>" in html_page
    assert "<tg-spoiler>секрет</tg-spoiler>" in html_page


def test_render_html_preview_raw_html():
    raw_html = "<b>Жирный текст</b>"
    html_page = render_html_preview(raw_html, is_markdown=False)

    assert "<b>Жирный текст</b>" in html_page
    assert "<!DOCTYPE html>" in html_page


def test_save_preview_creates_file(tmp_path: Path):
    target_file = tmp_path / "subfolder" / "preview.html"
    target_file.parent.mkdir(parents=True, exist_ok=True)

    result_path = save_preview(
        "Тестовое сообщение с формулой: $x^2$",
        file_path=target_file,
    )

    assert result_path.exists()
    content = result_path.read_text(encoding="utf-8")
    assert "<tg-math>x^2</tg-math>" in content
    assert "Telegram Rich HTML Preview" in content


def test_complex_document_stress_test():
    complex_md = r"""
<think>
План: проверить $U^\dagger U = I$ и параметр ||DIAG_KEY_0x99||.
</think>

# Квантовый осциллятор

Формула состояния: $|\psi(t)\rangle = e^{-i\hat{H}t/\hbar}|\psi(0)\rangle$.
Гамильтониан:
$$\hat{H} = -\frac{\hbar^2}{2m} \nabla^2 + V(x)$$

| Оператор | Матрица | Режим \| Тип |
|:---|:---:|---:|
| Паули $\sigma_x$ | $\begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}$ | Базовый \| $X$ |

> Важно: эволюция ++строго унитарна++, а ~~старый метод~~ запрещён.
Маркер: ==квантовое превосходство==.
Секрет: ||KEY_TOKEN_SECRET||.

```python
import numpy as np
print("OK")
```
"""
    result = to_rich(complex_md, thinking_summary="Цепочка рассуждений")

    # Проверка отсутствия нераскрытых плейсхолдеров
    assert "§§TGBLOCK" not in result

    # Проверка блоков рассуждений
    assert "<details><summary>Цепочка рассуждений</summary>" in result
    assert "<tg-spoiler>DIAG_KEY_0x99</tg-spoiler>" in result

    # Проверка заголовков и формул
    assert "<h1>Квантовый осциллятор</h1>" in result
    assert "<tg-math>|\\psi(t)\\rangle = e^{-i\\hat{H}t/\\hbar}|\\psi(0)\\rangle</tg-math>" in result
    assert "<tg-math-block>\\hat{H} = -\\frac{\\hbar^2}{2m} \\nabla^2 + V(x)</tg-math-block>" in result

    # Проверка таблицы
    assert '<table bordered="true" striped="true">' in result
    assert '<th align="left">Оператор</th>' in result
    assert '<th align="center">Матрица</th>' in result
    assert '<th align="right">Режим | Тип</th>' in result
    assert '<td align="center"><tg-math>\\begin{pmatrix} 0 &amp; 1 \\\\ 1 &amp; 0 \\end{pmatrix}</tg-math></td>' in result
    assert '<td align="right">Базовый | <tg-math>X</tg-math></td>' in result

    # Проверка инлайн стилей
    assert "<blockquote>" in result
    assert "<u>строго унитарна</u>" in result
    assert "<s>старый метод</s>" in result
    assert "<mark>квантовое превосходство</mark>" in result
    assert "<tg-spoiler>KEY_TOKEN_SECRET</tg-spoiler>" in result

    # Проверка кода
    assert '<pre><code class="language-python">' in result
    assert 'print("OK")' in result
