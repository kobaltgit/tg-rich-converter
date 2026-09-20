__version__ = "0.4.0"

from .cli import main as cli_main
from .converter import TelegramRichConverter, markdown_to_rich, to_rich
from .preview import render_html_preview, save_preview
from .splitter import split_rich_message

__all__ = [
    "__version__",
    "TelegramRichConverter",
    "to_rich",
    "markdown_to_rich",
    "render_html_preview",
    "save_preview",
    "split_rich_message",
    "cli_main",
]