<p align="center">
  <img src="https://raw.githubusercontent.com/kobaltgit/tg-rich-converter/main/assets/banner.svg" alt="tg-rich-converter banner" width="100%" />
</p>

# tg-rich-converter 🚀

[![PyPI version](https://img.shields.io/pypi/v/tg-rich-converter.svg)](https://pypi.org/project/tg-rich-converter/)
[![Python versions](https://img.shields.io/pypi/pyversions/tg-rich-converter.svg)](https://pypi.org/project/tg-rich-converter/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, zero-dependency Python library that converts standard LLM Markdown, LaTeX formulas, thinking processes, and tables into **native Telegram Bot API 10.1+ Rich HTML** (`sendRichMessage`).

---

<p align="center">
  <img src="https://raw.githubusercontent.com/kobaltgit/tg-rich-converter/main/assets/demo_01.png" width="48%" alt="Tables and Math Demo" />
</p>

---

## Why tg-rich-converter?

Starting with **Telegram Bot API 10.1**, Telegram introduced **Rich Messages** (`sendRichMessage`) supporting:
- Messages up to **32,768 characters** (no more 4,096-character limit!).
- **Native interactive tables** with borders and striping.
- **Native LaTeX math rendering** (both inline and display equations).
- **Expandable spoiler/details blocks** for reasoning models (`DeepSeek-R1`, `OpenAI o1/o3`, `Qwen`, `Gemini`).
- **Native lists and advanced typography** (`<ul>`, `<ol>`, `<u>`, `<mark>`).

However, LLMs (OpenAI, Anthropic, DeepSeek, Ollama) still output plain Markdown and LaTeX. `tg-rich-converter` bridges this gap seamlessly in **a single function call**.

---

## Features

- 📊 **Robust Native Tables:** Converts standard Markdown pipe tables into `<table bordered striped>` with column alignment (`left`, `center`, `right`). Safely handles formulas with pipes (`$|\psi\rangle$`, `$|x| \ge 0$`) and escaped pipes (`\|`) inside table cells without breaking columns.
- 🧮 **LaTeX Math:** Converts `$$...$$` into `<tg-math-block>` and `$x$` into `<tg-math>`.
- 🧠 **Customizable AI Thinking Blocks:** Converts `<think>...</think>` tags from reasoning models into expandable `<details><summary>Размышления</summary>...</details>` blocks with configurable summary titles.
- 🛡️ **HTML-Safe:** Automatically escapes raw `<`, `>`, and `&` in regular text (e.g. mathematical conditions like `x < 5` and `y > 10`), completely preventing Telegram API `400 Bad Request: can't parse entities` errors.
- 📋 **Native Lists:** Converts unordered (`- `, `* `, `+ `) and ordered (`1. `) lists into native `<ul>` and `<ol>` tags, avoiding conflicts between asterisk bullet markers and italics.
- 🎨 **Rich Typography:** Supports bold (`**`), italic (`*` / `_`), strikethrough (`~~`), underline (`++text++`), highlight (`==text==`), and spoilers (`||spoiler||`) with snake_case protection.
- 💻 **Syntax-Highlighted Code:** Converts markdown code fences into `<pre><code class="language-...">` preserving language classes, indentation, and copy buttons.
- ✂️ **Smart Message Splitter:** Safely splits long texts up to 32,768 (Telegram Rich limit) or 4,096 (Classic limit) characters. Automatically closes and re-opens nested tags with attributes (`<pre><code class="...">`, `<blockquote>`), and protects LaTeX formulas from fragmentation.
- 👁️ **Local HTML Preview:** Instantly generates a standalone `preview.html` styled with authentic Telegram Web dark theme and KaTeX client-side math rendering to visually inspect output without launching a bot.
- ⚡ **Thread-Safe & Zero Dependencies:** Pure standard Python (`re`, `html`). Fully reentrant and async-safe for high-concurrency bot environments.

---

## Installation

```bash
pip install tg-rich-converter
```

---

## Quick Start

```python
from tg_rich_converter import to_rich

llm_output = """
# Quantum Computing Report

| Algorithm | State | Complexity | Option |
|:----------|:-----:|:----------:|-------:|
| Linear Search | $N$ items | $O(N)$ | Mode A \\| B |
| State Vector  | $|\\psi\\rangle$ | $O(1)$ | Basic |

### Key Formula
$$|\\psi\\rangle = \\alpha |0\\rangle + \\beta |1\\rangle$$

Stability requires delta < 0.05 and alpha > 0.

<think>
Evaluating time complexity and qubit entanglement...
</think>
"""

# Default thinking summary is "Размышления"
rich_html = to_rich(llm_output)

# Or specify a custom summary:
rich_html_en = to_rich(llm_output, thinking_summary="Reasoning Process")
```

---

## Smart Message Splitting (Long Outputs)

When LLM output exceeds Telegram limits (32,768 chars for Rich Messages or 4,096 chars for standard messages), naive slicing breaks open HTML tags and crashes the bot. Use `split_rich_message`:

```python
from tg_rich_converter import split_rich_message

# Automatically converts Markdown to Rich HTML and splits into safe chunks
chunks = split_rich_message(
    long_llm_response,
    max_length=32768,      # 32,768 for Rich Messages (default) or 4,096 for Classic
    is_markdown=True,      # Automatically runs to_rich()
    thinking_summary="Reasoning"
)

# Each chunk is guaranteed to be valid HTML with all open tags closed and reopened
for chunk in chunks:
    await bot.send_rich_message(chat_id=chat_id, rich_message={"html": chunk})
```

---

## Local HTML Preview

Visualize how your message will look in Telegram Desktop/Mobile without running a bot or sending messages:

```python
from tg_rich_converter import save_preview

# Generates preview.html with Telegram dark theme, KaTeX formulas, and interactive spoilers
save_preview(
    llm_output,
    file_path="preview.html",
    title="LLM Telegram Preview"
)
```

Double click `preview.html` to open it in your browser!

---

## Framework Integrations

### 1. aiogram (3.31+)

```python
from aiogram import Bot
from tg_rich_converter import to_rich

bot = Bot(token="YOUR_BOT_TOKEN")

rich_html = to_rich(llm_response)
await bot.send_rich_message(
    chat_id=chat_id,
    rich_message={"html": rich_html}
)
```

### 2. pyTelegramBotAPI (telebot 4.36+)

```python
import telebot
from tg_rich_converter import to_rich

bot = telebot.TeleBot("YOUR_BOT_TOKEN")

rich_html = to_rich(llm_response)
bot.send_rich_message(
    chat_id=chat_id,
    rich_message={"html": rich_html}
)
```

### 3. Direct HTTP (requests / httpx / urllib)

```python
import requests
from tg_rich_converter import to_rich

rich_html = to_rich(llm_response)

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendRichMessage",
    json={
        "chat_id": chat_id,
        "rich_message": {
            "html": rich_html
        }
    }
)
```

---

## Testing

Run unit tests locally:

```bash
pytest
```

---

## License

MIT License. Free for commercial and personal use.