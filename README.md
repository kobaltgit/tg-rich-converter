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
- **Expandable spoiler/details blocks** for reasoning models (`DeepSeek-R1`, `OpenAI o1/o3`).

However, LLMs (OpenAI, Anthropic, DeepSeek, Ollama) still output plain Markdown and LaTeX. `tg-rich-converter` bridges this gap seamlessly in **a single function call**.

---

## Features

- 📊 **Native Tables:** Converts standard Markdown pipe tables (`| col | col |`) into `<table bordered striped>` with column alignment (`left`, `center`, `right`).
- 🧮 **LaTeX Math:** Converts `$$...$$` into `<tg-math-block>` and `$x$` into `<tg-math>`. Even works **inside table cells**!
- 🧠 **AI Thinking Blocks:** Converts `<think>...</think>` tags from reasoning models into expandable native `<details><summary>Размышления</summary>...</details>` blocks.
- 💻 **Syntax-Highlighted Code:** Converts ` ```python ` into `<pre><code class="language-python">` preserving quotes and copy-paste buttons.
- 💬 **Quotes & Spoilers:** Native blockquotes and spoilers (`||spoiler||`) with snake_case protection.
- ⚡ **Zero Dependencies:** Pure standard Python (`re`, `html`). Extremely fast (~0.001s per message).

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

| Algorithm | Database | Complexity | Speedup |
|:----------|:--------:|:----------:|--------:|
| Linear Search | $N$ items | $O(N)$ | $1\\times$ |
| Grover Search | $N$ items | $O(\\sqrt{N})$ | Quadratic |

### Key Formula
$$|\\psi\\rangle = \\alpha |0\\rangle + \\beta |1\\rangle$$

<think>
Evaluating time complexity and qubit entanglement...
</think>
"""

rich_html = to_rich(llm_output)
```

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

### 3. Direct HTTP (requests / httpx)

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