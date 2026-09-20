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


def test_latex_formulas():
    md = "Энергия: $$E = mc^2$$, скорость $c$ константа."
    result = to_rich(md)
    assert "<tg-math-block>E = mc^2</tg-math-block>" in result
    assert "<tg-math>c</tg-math>" in result


def test_thinking_block():
    md = "<think>Подумаем над планом решения...</think>\nРезультат готов."
    result = to_rich(md)
    assert "<details><summary>Размышления</summary>" in result
    assert "Результат готов." in result


def test_code_blocks():
    md = "```python\nprint('tg-rich-converter')\n```"
    result = to_rich(md)
    assert '<pre><code class="language-python">print(\'tg-rich-converter\')</code></pre>' in result


def test_spoiler_with_snake_case():
    md = "Секретный ключ: ||SUPER_SECRET_KEY_42||"
    result = to_rich(md)
    assert "<tg-spoiler>SUPER_SECRET_KEY_42</tg-spoiler>" in result
    assert "<i>" not in result


def test_alias_works():
    assert to_rich("**test**") == markdown_to_rich("**test**")