<p align="center">
  <img src="https://raw.githubusercontent.com/kobaltgit/tg-rich-converter/main/assets/banner.svg" alt="tg-rich-converter banner" width="100%" />
</p>
<div align="center">

<img src="https://raw.githubusercontent.com/kobaltgit/tg-rich-converter/main/assets/icon.svg" alt="tg-rich-converter icon" width="15%" /> 

# tg-rich-converter

[![PyPI version](https://img.shields.io/pypi/v/tg-rich-converter.svg)](https://pypi.org/project/tg-rich-converter/)
[![Python versions](https://img.shields.io/pypi/pyversions/tg-rich-converter.svg)](https://pypi.org/project/tg-rich-converter/)
[![Platform](https://img.shields.io/badge/Platform-Telegram-26A5E4)](https://telegram.org)
[![Bot API](https://img.shields.io/badge/Bot%20API-10.1-green)](https://core.telegram.org/bots/api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![Stars](https://img.shields.io/github/stars/kobaltgit/tg-rich-converter?style=for-the-badge&logo=github)](https://github.com/kobaltgit/tg-rich-converter/stargazers)
[![Forks](https://img.shields.io/github/forks/kobaltgit/tg-rich-converter?style=for-the-badge&logo=github)](https://github.com/kobaltgit/tg-rich-converter/network/members)

A lightweight, zero-dependency Python library that converts standard LLM Markdown, LaTeX formulas, thinking processes, and tables into **native Telegram Bot API 10.1+ Rich HTML** (`sendRichMessage`).
</div>

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

However, LLMs (OpenAI, Anthropic, DeepSeek, Ollama) still output plain Markdown and LaTeX. `tg-rich-converter` bridges this gap seamlessly in **a single function call** or via the **CLI command line tool**.

---

## Features

- 🌊 **LLM Streaming Mode (`streaming=True`):** Auto-balances unclosed code blocks (`` ``` ``), reasoning tags (`<think>`), unclosed LaTeX formulas (`$$` / `$`), and unclosed inline styles (`**`, `||`, `++`, `==`, `~~`) during token-by-token streaming, completely preventing Telegram `400 Bad Request: can't parse entities` errors on live message edits.
- 📊 **Robust Native Tables:** Converts standard Markdown pipe tables into `<table bordered striped>` with column alignment (`left`, `center`, `right`). Safely handles formulas with pipes (`$|\psi\rangle$`, `$|x| \ge 0$`) and escaped pipes (`\|`) inside table cells without breaking columns.
- 🧮 **LaTeX Math:** Converts `$$...$$` into `<tg-math-block>` and `$x$` into `<tg-math>`.
- 🧠 **Customizable AI Thinking Blocks:** Converts `<think>...</think>` tags from reasoning models into expandable `<details><summary>Размышления</summary>...</details>` blocks with configurable summary titles.
- 🛡️ **HTML-Safe:** Automatically escapes raw `<`, `>`, and `&` in regular text (e.g. mathematical conditions like `x < 5` and `y > 10`), completely preventing Telegram API `400 Bad Request: can't parse entities` errors.
- 📋 **Native Lists:** Converts unordered (`- `, `* `, `+ `) and ordered (`1. `) lists into native `<ul>` and `<ol>` tags, avoiding conflicts between asterisk bullet markers and italics.
- 🎨 **Rich Typography:** Supports bold (`**`), italic (`*` / `_`), strikethrough (`~~`), underline (`++text++`), highlight (`==text==`), and spoilers (`||spoiler||`) with snake_case protection.
- 💻 **Syntax-Highlighted Code:** Converts markdown code fences into `<pre><code class="language-...">` preserving language classes, indentation, and copy buttons.
- ✂️ **Smart Message Splitter:** Safely splits long texts up to 32,768 (Telegram Rich limit) or 4,096 (Classic limit) characters. Automatically closes and re-opens nested tags with attributes (`<pre><code class="...">`, `<blockquote>`), and protects LaTeX formulas from fragmentation.
- 👁️ **Local HTML Preview:** Instantly generates a standalone `preview.html` styled with authentic Telegram Web dark theme and KaTeX client-side math rendering to visually inspect output without launching a bot.
- 🚀 **Built-in CLI (`tg-rich`):** Fast command-line utility with TrueColor ANSI logo, preview generator, auto-opening in browser, pipeline support (`stdin`/`stdout`), and batch message splitter.
- ⚡ **Thread-Safe & Zero Dependencies:** Pure standard Python (`re`, `html`, `argparse`). Fully reentrant and async-safe for high-concurrency bot environments.

---

## Installation

```bash
pip install tg-rich-converter
```

---

## Quick Start (Python)

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

## LLM Streaming Mode (Live Edits)

When streaming LLM responses token-by-token (`OpenAI`, `DeepSeek-R1`, `Anthropic Claude`, `Ollama`), intermediate tokens frequently contain unfinished Markdown/LaTeX structures:
- Unclosed code fences: ````python\ndef run():`` (missing closing ````)
- Open reasoning blocks: `<think>Analyzing steps...` (missing `</think>`)
- Half-written formulas: `$E = mc^2` or `$$\int_0^\infty`
- Incomplete typography: `**bold text`, `||secret key`, `++underlined`

Passing `streaming=True` automatically balances and virtually closes all open structures in LIFO order for every frame:

```python
import time
from tg_rich_converter import to_rich

# 1. Send initial placeholder message via sendRichMessage
sent_msg = await bot.send_rich_message(
    chat_id=chat_id,
    rich_message={"html": "<i>⏳ Thinking...</i>"}
)

buffer = ""
last_edit_time = time.time()
THROTTLE_SECONDS = 0.7  # Recommended: 0.6 - 0.8s to avoid Telegram 429 Flood Limits

# 2. Stream tokens from LLM
async for chunk in openai_client.chat.completions.create(..., stream=True):
    buffer += chunk.choices[0].delta.content or ""
    now = time.time()
    
    # Edit message with rate-limiting throttle
    if now - last_edit_time >= THROTTLE_SECONDS:
        safe_frame_html = to_rich(buffer, streaming=True)
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=sent_msg.message_id,
            rich_message={"html": safe_frame_html}  # Must pass rich_message, NOT text/parse_mode!
        )
        last_edit_time = now

# 3. Final complete render (streaming=False)
final_html = to_rich(buffer, streaming=False)
await bot.edit_message_text(
    chat_id=chat_id,
    message_id=sent_msg.message_id,
    rich_message={"html": final_html}
)
```

---

## ⚠️ Troubleshooting & Common Pitfalls

### 1. `Bad Request: can't parse entities: Unsupported start tag "details"`
* **Cause:** Calling `sendMessage` or `editMessageText` with legacy `text="<details>..."` and `parse_mode="HTML"`. The legacy Telegram parser does not support `<details>`, `<tg-math>`, or `<table>`.
* **Fix:** Use the Telegram Bot API 10.1+ Rich Message format with `rich_message={"html": ...}`:
  ```python
  # ❌ WRONG (Triggers 400 Bad Request):
  await bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=rich_html, parse_mode="HTML")

  # ✔ CORRECT (Native Rich Messages):
  await bot.edit_message_text(chat_id=chat_id, message_id=msg_id, rich_message={"html": rich_html})
  ```

### 2. `Too Many Requests: retry after X` (Flood Limits)
* **Cause:** Sending `editMessageText` on every single incoming LLM token.
* **Fix:** Throttle live edits to once every **0.6 – 0.8 seconds** (or every 40–60 characters).

### 3. Missing `<think>` reasoning block header
* **Fix:** Customize the default title via `thinking_summary`:
  ```python
  html_output = to_rich(markdown_text, thinking_summary="Chain of Thought")
  ```

---

## Command-Line Interface (CLI)

After installation, the `tg-rich` command is available in your terminal:

### 1. Instant Preview in Browser
Convert a markdown file and open the interactive Telegram preview directly in your default browser:
```bash
tg-rich prompt_response.md --preview --open
```

### 2. Convert to Rich HTML File
```bash
tg-rich document.md -o output.html
```

### 3. Pipeline / Stdin Mode
```bash
cat llm_output.md | tg-rich > telegram_message.html
```

### 4. Smart Message Splitting
Split a large document into chunks respecting Telegram character limits:
```bash
# Split for Rich Messages (32k limit)
tg-rich big_report.md --split

# Split for Classic Messages (4k limit) into separate files
tg-rich big_report.md --split --limit 4096 -o chunk.html
```

### CLI Options Reference
| Flag | Description | Default |
|:---|:---|:---|
| `input_file` | Path to markdown file (or `-` / pipe for stdin) | `-` |
| `-o, --output FILE` | Write converted HTML to file instead of stdout | `stdout` |
| `-p, --preview [FILE]` | Generate standalone preview.html with KaTeX & Telegram Dark theme | `preview.html` |
| `--open` | Automatically open the preview in default web browser | `False` |
| `-s, --split` | Split long message into safe Telegram chunks | `False` |
| `-l, --limit INT` | Maximum character length for splitting | `32768` |
| `-t, --thinking-summary TEXT` | Custom header for `<think>` reasoning blocks | `Размышления` |
| `--lang {ru,en}` | Interface and error message language | `auto` |
| `-q, --quiet` | Suppress banner and progress messages in stderr | `False` |
| `-v, --version` | Display current library version | |

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

## Testing & Demos

### 1. Run Unit Tests
Run the comprehensive test suite locally (44 tests, 100% pass):
```bash
pytest
```

### 2. Live Telegram Streaming Demo

> 🎬 **Demo:** [The Secret to Perfect Telegram Bot Streaming](https://www.youtube.com/watch?v=bINwbCmhl1g)

Test real-time LLM token-by-token streaming with rate-limiting throttle (0.7s) directly in your Telegram chat:
```bash
# Direct CLI arguments
python demo_streaming.py --token "YOUR_BOT_TOKEN" --chat-id "YOUR_CHAT_ID"

# Or via environment variables
export BOT_TOKEN="YOUR_BOT_TOKEN"
export CHAT_ID="YOUR_CHAT_ID"
python demo_streaming.py

# Windows PowerShell
$env:BOT_TOKEN="YOUR_BOT_TOKEN"; $env:CHAT_ID="YOUR_CHAT_ID"; python demo_streaming.py
```

### 3. Local Console Stream Simulation
Validate intermediate streaming frames in terminal without sending requests to Telegram:
```bash
python demo_streaming.py
```

---

## License

MIT License. Free for commercial and personal use.