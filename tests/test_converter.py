from tg_rich_converter import to_rich, markdown_to_rich


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