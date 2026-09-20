import html
from pathlib import Path
from typing import Union

from .converter import to_rich

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
    <style>
        :root {{
            --bg-color: #0e1621;
            --bubble-bg: #182533;
            --text-color: #f5f5f5;
            --text-secondary: #7f91a4;
            --link-color: #64b5f6;
            --accent-blue: #5288c1;
            --quote-bg: rgba(82, 136, 193, 0.1);
            --code-bg: #101921;
            --code-border: #242f3d;
            --table-border: #242f3d;
            --table-striped: #1e2c3a;
            --table-header-bg: #17212b;
            --spoiler-bg: #2b394a;
            --mark-bg: rgba(230, 194, 41, 0.3);
            --details-bg: #131d27;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            font-size: 15px;
            line-height: 1.45;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
        }}

        .tg-container {{
            width: 100%;
            max-width: 720px;
        }}

        .tg-header-badge {{
            display: inline-block;
            margin-bottom: 12px;
            padding: 4px 10px;
            background: #17212b;
            border-radius: 6px;
            color: var(--text-secondary);
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}

        .tg-message-bubble {{
            background-color: var(--bubble-bg);
            border-radius: 12px;
            padding: 14px 18px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
            word-wrap: break-word;
        }}

        /* Заголовки */
        h1, h2, h3, h4, h5, h6 {{
            margin: 14px 0 8px 0;
            font-weight: 600;
            line-height: 1.3;
        }}
        h1:first-child, h2:first-child, h3:first-child {{
            margin-top: 0;
        }}
        h1 {{ font-size: 1.45em; }}
        h2 {{ font-size: 1.3em; }}
        h3 {{ font-size: 1.15em; }}
        h4, h5, h6 {{ font-size: 1.05em; }}

        /* Ссылки */
        a {{
            color: var(--link-color);
            text-decoration: underline;
        }}
        a:hover {{
            text-decoration: none;
        }}

        /* Выделения текста */
        b, strong {{
            font-weight: 700;
        }}
        i, em {{
            font-style: italic;
        }}
        u {{
            text-decoration: underline;
        }}
        s, strike {{
            text-decoration: line-through;
        }}
        mark {{
            background-color: var(--mark-bg);
            color: #fff;
            padding: 1px 4px;
            border-radius: 3px;
        }}

        /* Спойлеры */
        tg-spoiler {{
            background-color: var(--spoiler-bg);
            color: transparent !important;
            filter: blur(5px);
            border-radius: 4px;
            padding: 1px 4px;
            cursor: pointer;
            user-select: none;
            transition: filter 0.2s ease, color 0.2s ease;
        }}
        tg-spoiler.revealed {{
            background-color: transparent;
            color: inherit !important;
            filter: none;
            user-select: auto;
            cursor: text;
        }}

        /* Формулы */
        tg-math {{
            display: inline-block;
            vertical-align: middle;
            padding: 0 2px;
        }}
        tg-math-block {{
            display: block;
            margin: 10px 0;
            text-align: center;
            overflow-x: auto;
            overflow-y: hidden;
            padding: 8px 0;
        }}

        /* Код */
        code {{
            font-family: "JetBrains Mono", Consolas, Monaco, "Courier New", monospace;
            background-color: var(--code-bg);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.9em;
            color: #e2e8f0;
        }}
        pre {{
            background-color: var(--code-bg);
            border: 1px solid var(--code-border);
            border-radius: 8px;
            padding: 12px 14px;
            margin: 10px 0;
            overflow-x: auto;
        }}
        pre code {{
            background: none;
            padding: 0;
            font-size: 0.88em;
            line-height: 1.4;
        }}

        /* Блок размышлений (<think>) */
        details {{
            background-color: var(--details-bg);
            border: 1px solid var(--code-border);
            border-radius: 8px;
            margin: 10px 0;
            padding: 8px 12px;
        }}
        details summary {{
            font-weight: 600;
            cursor: pointer;
            color: var(--text-secondary);
            outline: none;
            user-select: none;
            padding: 4px 0;
        }}
        details[open] summary {{
            margin-bottom: 8px;
            border-bottom: 1px solid var(--code-border);
        }}

        /* Цитаты */
        blockquote {{
            border-left: 3px solid var(--accent-blue);
            background-color: var(--quote-bg);
            padding: 8px 12px;
            margin: 10px 0;
            border-radius: 0 6px 6px 0;
            color: #dbe4ee;
        }}

        /* Горизонтальный разделитель */
        hr {{
            border: none;
            border-top: 1px solid var(--table-border);
            margin: 14px 0;
        }}

        /* Списки */
        ul, ol {{
            margin: 8px 0;
            padding-left: 24px;
        }}
        li {{
            margin: 3px 0;
        }}

        /* Таблицы */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
            font-size: 0.95em;
        }}
        table[bordered="true"] th,
        table[bordered="true"] td {{
            border: 1px solid var(--table-border);
        }}
        th, td {{
            padding: 8px 12px;
        }}
        th {{
            background-color: var(--table-header-bg);
            font-weight: 600;
            text-align: left;
        }}
        table[striped="true"] tbody tr:nth-child(even) {{
            background-color: var(--table-striped);
        }}
    </style>
</head>
<body>
    <div class="tg-container">
        <div class="tg-header-badge">Telegram Rich HTML Preview</div>
        <div class="tg-message-bubble">
{content}
        </div>
    </div>

    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            // Интерактивные спойлеры
            document.querySelectorAll("tg-spoiler").forEach(function(el) {{
                el.addEventListener("click", function() {{
                    el.classList.toggle("revealed");
                }});
            }});

            // Рендеринг KaTeX формул
            function renderMath() {{
                if (typeof katex === "undefined") return;

                document.querySelectorAll("tg-math").forEach(function(el) {{
                    try {{
                        katex.render(el.textContent, el, {{
                            displayMode: false,
                            throwOnError: false
                        }});
                    }} catch (e) {{
                        console.error(e);
                    }}
                }});

                document.querySelectorAll("tg-math-block").forEach(function(el) {{
                    try {{
                        katex.render(el.textContent, el, {{
                            displayMode: true,
                            throwOnError: false
                        }});
                    }} catch (e) {{
                        console.error(e);
                    }}
                }});
            }}

            // Проверка загрузки KaTeX
            if (typeof katex !== "undefined") {{
                renderMath();
            }} else {{
                window.addEventListener("load", renderMath);
            }}
        }});
    </script>
</body>
</html>
"""


def render_html_preview(
    text: str,
    is_markdown: bool = True,
    thinking_summary: str = "Размышления",
    title: str = "Telegram Rich HTML Preview",
) -> str:
    """Генерирует автономную HTML-страницу с превью в тёмном стиле Telegram."""
    if is_markdown:
        rendered_content = to_rich(text, thinking_summary=thinking_summary)
    else:
        rendered_content = text

    # Добавляем базовый отступ для красивого расположения внутри bubble
    indented_content = "\n".join(f"            {line}" for line in rendered_content.splitlines())
    return _HTML_TEMPLATE.format(
        title=html.escape(title),
        content=indented_content,
    )


def save_preview(
    text: str,
    file_path: Union[str, Path] = "preview.html",
    is_markdown: bool = True,
    thinking_summary: str = "Размышления",
    title: str = "Telegram Rich HTML Preview",
) -> Path:
    """Генерирует страницу предварительного просмотра и сохраняет её в файл."""
    html_output = render_html_preview(
        text=text,
        is_markdown=is_markdown,
        thinking_summary=thinking_summary,
        title=title,
    )
    path = Path(file_path)
    path.write_text(html_output, encoding="utf-8")
    return path