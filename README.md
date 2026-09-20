# tg-rich-converter

Convert LLM-generated Markdown, LaTeX equations, thinking blocks and tables into **Telegram Bot API 10.1+ native Rich HTML** (`sendRichMessage`).

Zero dependencies. Lightweight and fast.

## Installation

```bash
pip install tg-rich-converter
```
# Quick Start

from tg_rich_converter import to_rich

llm_response = """
### Results
| Model | Score |
|:------|------:|
| GPT-4 | 95%   |

Formula: $$E = mc^2$$

<think>
Internal thought process
</think>
"""

rich_html = to_rich(llm_response)

## Usage with aiogram 3.31+

```python
from aiogram import Bot
from tg_rich_converter import to_rich

bot = Bot(token="BOT_TOKEN")

rich_html = to_rich(llm_response)
await bot.send_rich_message(chat_id=123456, rich_message={"html": rich_html})
```

## Usage with pyTelegramBotAPI (telebot 4.36+)

```python
import telebot
from tg_rich_converter import to_rich

bot = telebot.TeleBot("BOT_TOKEN")
rich_html = to_rich(llm_response)

bot.send_rich_message(chat_id=123456, rich_message={"html": rich_html})
```

# License

MIT